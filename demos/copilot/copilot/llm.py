"""Calls to the Gemini API via LiteLLM, with retries for the free tier.

* 429 rate limit: wait as long as the API asks for
* daily limit of a generation model: switch to a fallback model
* 503 overloaded / timeouts: exponential backoff, then fallback model
"""

import logging
import re
import time
from typing import Iterator

import litellm

from copilot import settings

logger = logging.getLogger("copilot.llm")

litellm.suppress_debug_info = True
litellm.drop_params = True

MAX_ATTEMPTS = 6
MAX_WAIT_SECONDS = 65
FALLBACK_AFTER_ATTEMPTS = 3

RETRYABLE_ERRORS = (
    litellm.RateLimitError,
    litellm.ServiceUnavailableError,
    litellm.InternalServerError,
    litellm.Timeout,
    litellm.APIConnectionError,
)


class QuotaExceededError(RuntimeError):
    """The daily free tier limit is used up."""


def _is_rate_limit(error: Exception) -> bool:
    return isinstance(error, litellm.RateLimitError) or "RESOURCE_EXHAUSTED" in str(error)


def _is_daily_limit(error: Exception) -> bool:
    return _is_rate_limit(error) and ("PerDay" in str(error) or "per day" in str(error))


def _wait_seconds(error: Exception, attempt: int) -> float:
    if _is_rate_limit(error):
        match = re.search(r"retry in ([\d.]+)\s*s", str(error), flags=re.IGNORECASE)
        return min(float(match.group(1)) + 1 if match else 20, MAX_WAIT_SECONDS)
    return min(5 * 2 ** (attempt - 1), MAX_WAIT_SECONDS)


def _call(function, generation: bool, **kwargs):
    fallbacks = [m for m in settings.FALLBACK_MODELS if m != kwargs.get("model")] if generation else []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return function(**kwargs)
        except Exception as error:
            retryable = isinstance(error, RETRYABLE_ERRORS) or _is_rate_limit(error)
            if not retryable or attempt == MAX_ATTEMPTS:
                raise
            overloaded = isinstance(error, litellm.ServiceUnavailableError) and attempt >= FALLBACK_AFTER_ATTEMPTS
            if (_is_daily_limit(error) or overloaded) and fallbacks:
                kwargs["model"] = fallbacks.pop(0)
                logger.warning("switching to fallback model %s", kwargs["model"])
                continue
            if _is_daily_limit(error):
                raise QuotaExceededError(f"The daily free tier limit for {kwargs.get('model')} is used up.") from None
            wait = _wait_seconds(error, attempt)
            logger.warning("%s, waiting %.0fs (attempt %d)", type(error).__name__, wait, attempt)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def complete(messages: list[dict], **kwargs) -> str:
    """Returns the answer of the generation model."""
    response = _call(litellm.completion, generation=True, model=settings.GENERATION_MODEL, messages=messages, **kwargs)
    return response.choices[0].message.content or ""


def stream(messages: list[dict], **kwargs) -> Iterator[str]:
    """Yields the answer of the generation model in pieces."""
    response = _call(litellm.completion, generation=True, model=settings.GENERATION_MODEL, messages=messages,
                     stream=True, **kwargs)
    for chunk in response:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


def embed(texts: list[str], task_type: str | None = None) -> list[list[float]]:
    """Embeds the texts (without cache, see knowledge_base.embed_cached)."""
    kwargs = {"task_type": task_type} if task_type else {}
    response = _call(litellm.embedding, generation=False, model=settings.EMBEDDING_MODEL, input=texts, **kwargs)
    return [item["embedding"] for item in response["data"]]


def count_tokens(text: str) -> int:
    """Estimates the number of tokens locally (no API request)."""
    return litellm.token_counter(model=settings.GENERATION_MODEL, text=text)
