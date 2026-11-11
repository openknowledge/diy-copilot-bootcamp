from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data"
# The fictional internal code base our coding assistant works on.
CODEBASE_PATH = DATA_PATH / "codebase" / "roomie"
# The knowledge base for RAG: domain policies, engineering guidelines and
# security/privacy requirements of the (fictional) company.
KNOWLEDGE_BASE_PATH = DATA_PATH / "knowledge_base"
EVALUATION_DATA_PATH = DATA_PATH / "evaluation"
# Export of the issue tracker of the team that owns the code base.
TICKETS_PATH = DATA_PATH / "issue_tracker" / "tickets.json"
# Cache of embedding vectors (checked into the repository, see lib/rag.py)
EMBEDDING_CACHE_PATH = DATA_PATH / "cache" / "embeddings.sqlite"

# Default models (Gemini API, free tier). Can be overridden via the environment
# variables DEFAULT_GENERATION_MODEL / DEFAULT_EMBEDDING_MODEL.
DEFAULT_GENERATION_MODEL = "gemini/gemini-3.1-flash-lite"
DEFAULT_EMBEDDING_MODEL = "gemini/gemini-embedding-001"
# Used automatically if a generation model stays overloaded (HTTP 503) for a while.
# Only non-"thinking" models are suitable: thinking models (e.g. gemini-3.6-flash) spend
# small token budgets on reasoning and return empty or truncated answers.
# (gemini-2.5-flash-lite is no longer available.)
FALLBACK_GENERATION_MODELS = ["gemini/gemini-3.5-flash-lite"]

# File types of the code base.
CODEBASE_FILE_EXTENSIONS = (".py", ".md", ".toml")
# File types of the knowledge base.
KNOWLEDGE_BASE_FILE_EXTENSIONS = (".md",)
