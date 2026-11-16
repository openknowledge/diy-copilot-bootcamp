"""Settings of the copilot service, read from environment variables.

The defaults work for a local run from this folder (``uv run ...``); the Docker
image sets the paths to the mounted volumes.
"""

import os
from pathlib import Path

# Local run: demos/copilot/copilot/settings.py -> the repository root is 3 folders up.
# In the Docker image the file is /app/copilot/settings.py and the paths come from the environment.
_PARENTS = Path(__file__).resolve().parents
_REPO_ROOT = _PARENTS[3] if len(_PARENTS) > 3 else Path("/")


def _env(name: str, default: str) -> str:
    return os.getenv(name, "").strip() or default


# Models (Gemini free tier, same defaults as the workshop)
GENERATION_MODEL = _env("GENERATION_MODEL", "gemini/gemini-3.1-flash-lite")
FALLBACK_MODELS = [m.strip() for m in _env("FALLBACK_MODELS", "gemini/gemini-3.5-flash-lite").split(",") if m.strip()]
EMBEDDING_MODEL = _env("EMBEDDING_MODEL", "gemini/gemini-embedding-001")

# The company knowledge base (Markdown). Only read, never written.
KNOWLEDGE_BASE_PATH = Path(_env("KNOWLEDGE_BASE_PATH", str(_REPO_ROOT / "data" / "knowledge_base")))
# Own embedding cache of the demo (written).
CACHE_PATH = Path(_env("CACHE_PATH", str(Path(__file__).resolve().parents[1] / ".cache" / "embeddings.sqlite")))
# Optional read-only cache of the workshop (data/cache/embeddings.sqlite): the knowledge base
# chunks are the same as in the workshop, so building the index costs no embedding requests.
SEED_CACHE_PATH = Path(_env("SEED_CACHE_PATH", str(_REPO_ROOT / "data" / "cache" / "embeddings.sqlite")))

# Ticket export of the issue tracker (MCP server "issue-tracker"). Only read.
TICKETS_PATH = Path(_env("TICKETS_PATH", str(_REPO_ROOT / "data" / "issue_tracker" / "tickets.json")))

# Retrieval
CHUNK_SIZE = int(_env("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(_env("CHUNK_OVERLAP", "100"))
TOP_K = int(_env("TOP_K", "4"))

# Guardrails
MAX_INPUT_TOKENS = int(_env("MAX_INPUT_TOKENS", "2000"))
TOPIC_THRESHOLD = float(_env("TOPIC_THRESHOLD", "0.675"))

# Optional API key for the OpenAI compatible API (Bearer token). Empty = no check.
COPILOT_API_KEY = os.getenv("COPILOT_API_KEY", "").strip()
