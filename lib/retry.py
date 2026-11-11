"""Retries for transient API errors.

The Gemini free tier has low rate limits (e.g. 15 requests per minute per
model) and the models are sometimes overloaded. Instead of failing, we wait
and try again:

* 429 rate limit: wait as long as the API asks for ("Please retry in 13.9s")
* 503 overloaded / 500 / timeouts: wait with exponential backoff; if a generation
  model stays overloaded, switch to a fallback model (see lib.constants)
"""

import re
import time
from typing import Callable, TypeVar

import litellm

from lib.constants import FALLBACK_GENERATION_MODELS

T = TypeVar("T")

MAX_ATTEMPTS = 8
MAX_WAIT_SECONDS = 65
# After this many failed attempts with an overloaded model (503), switch to a fallback model.
FALLBACK_AFTER_ATTEMPTS = 3

RETRYABLE_ERRORS = (
    litellm.RateLimitError,
    litellm.ServiceUnavailableError,
    litellm.InternalServerError,
    litellm.Timeout,
    litellm.APIConnectionError,
)

# Avoid printing long tracebacks and help links for errors we handle ourselves.
litellm.suppress_debug_info = True


def _requested_wait_seconds(error: Exception) -> float | None:
    """Extracts the wait time from messages like 'Please retry in 13.95s'."""
    match = re.search(r"retry in ([\d.]+)\s*s", str(error), flags=re.IGNORECASE)
    return float(match.group(1)) + 1 if match else None


def _is_generation(function: Callable) -> bool:
    """Fallback models are only used for text generation, never for embeddings
    (embeddings of different models are not comparable)."""
    return getattr(function, "__name__", "") == "completion"


def _is_rate_limit(error: Exception) -> bool:
    # LiteLLM sometimes maps a 429 of the Gemini embedding API to a BadRequestError,
    # so we also look at the message.
    return isinstance(error, litellm.RateLimitError) or "RESOURCE_EXHAUSTED" in str(error)


def _is_retryable(error: Exception) -> bool:
    return isinstance(error, RETRYABLE_ERRORS) or _is_rate_limit(error)


def call_with_retry(function: Callable[..., T], *args, verbose: bool = True, **kwargs) -> T:
    """Calls *function* and retries it on transient API errors.

    Parameters
    ----------
    function : Callable
        The function to call, e.g. ``litellm.completion``.
    *args, **kwargs
        Arguments passed to the function.
    verbose : bool
        Print a short note when waiting.

    Returns
    -------
    The return value of the function.
    """
    fallbacks = [m for m in FALLBACK_GENERATION_MODELS if m != kwargs.get("model")]
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return function(*args, **kwargs)
        except Exception as error:
            if not _is_retryable(error) or attempt == MAX_ATTEMPTS:
                raise
            overloaded = isinstance(error, litellm.ServiceUnavailableError)
            if overloaded and attempt >= FALLBACK_AFTER_ATTEMPTS and fallbacks and _is_generation(function):
                # The model is still overloaded: switch to another model instead of waiting longer.
                kwargs["model"] = fallbacks.pop(0)
                if verbose:
                    print(f"[retry] model still overloaded, switching to {kwargs['model']} ...")
                continue
            if _is_rate_limit(error):
                wait = _requested_wait_seconds(error) or 20
                reason = "rate limit reached"
            else:
                # Overloaded models often need a minute or more to recover.
                wait = 5 * 2 ** (attempt - 1)
                reason = f"temporary error ({type(error).__name__})"
            wait = min(wait, MAX_WAIT_SECONDS)
            if verbose:
                print(f"[retry] {reason}, waiting {wait:.0f}s (attempt {attempt}/{MAX_ATTEMPTS - 1}) ...")
            time.sleep(wait)
    raise RuntimeError("unreachable")
