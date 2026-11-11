"""Loads the environment for local runs and for Google Colab.

Locally the values come from a ``.env`` file in the repository root. In
Colab they come from the notebook secrets (key icon in the left sidebar).
Only ``GEMINI_API_KEY`` is required; the model defaults fall back to the
values in ``lib.constants``.
"""

import os

from dotenv import find_dotenv, load_dotenv

from lib.constants import DEFAULT_EMBEDDING_MODEL, DEFAULT_GENERATION_MODEL

SECRET_NAMES = (
    "GEMINI_API_KEY",
    "DEFAULT_GENERATION_PROVIDER",
    "DEFAULT_GENERATION_MODEL",
    "DEFAULT_EMBEDDING_PROVIDER",
    "DEFAULT_EMBEDDING_MODEL",
)


def running_in_colab() -> bool:
    try:
        import google.colab  # noqa: F401
    except ImportError:
        return False
    return True


def _load_colab_secrets() -> None:
    from google.colab import userdata

    for name in SECRET_NAMES:
        if os.getenv(name):
            continue
        try:
            value = userdata.get(name)
        except Exception:  # secret not defined or notebook access not granted
            value = None
        if value:
            os.environ[name] = value


def load_environment() -> dict[str, str]:
    """Loads secrets and model defaults into ``os.environ``.

    Returns
    -------
    dict[str, str]
        The generation and embedding model ids in LiteLLM format, e.g.
        ``{"generation_model": "gemini/gemini-3.1-flash-lite", ...}``.
    """
    if running_in_colab():
        _load_colab_secrets()
    else:
        load_dotenv(find_dotenv(usecwd=True))

    if not os.getenv("GEMINI_API_KEY"):
        where = "Colab secrets (key icon on the left)" if running_in_colab() else "the .env file"
        raise ValueError(f"GEMINI_API_KEY is not set. Please add it to {where}.")

    return {
        "generation_model": _model_id("GENERATION", DEFAULT_GENERATION_MODEL),
        "embedding_model": _model_id("EMBEDDING", DEFAULT_EMBEDDING_MODEL),
    }


def _model_id(kind: str, default: str) -> str:
    """Returns the LiteLLM model id ``<provider>/<model>`` for GENERATION or EMBEDDING.

    Accepts both ``DEFAULT_<KIND>_MODEL=gemini/gemini-3.1-flash-lite`` and the
    split form ``DEFAULT_<KIND>_PROVIDER=gemini`` + ``DEFAULT_<KIND>_MODEL=gemini-3.1-flash-lite``.
    Without a provider prefix LiteLLM would route Gemini models to Vertex AI,
    which needs Google Cloud credentials instead of an API key.
    """
    model = os.getenv(f"DEFAULT_{kind}_MODEL", "").strip() or default
    if "/" not in model:
        provider = os.getenv(f"DEFAULT_{kind}_PROVIDER", "").strip() or "gemini"
        model = f"{provider}/{model}"
    os.environ[f"DEFAULT_{kind}_MODEL"] = model
    return model
