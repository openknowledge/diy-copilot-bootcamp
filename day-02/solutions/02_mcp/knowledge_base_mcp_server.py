"""MCP server that exposes the company knowledge base search as a tool.

It provides exactly the same function as the function calling lesson:
``search_knowledge_base(query)``. The difference: the function now runs in its
own process and any MCP client (our notebook, Claude Code, VS Code, ...) can
discover and call it.

Run it manually with:

    python knowledge_base_mcp_server.py

Usually it is started by an MCP client, which talks to it over stdin/stdout.
Important: stdout is the protocol channel. Never print to stdout in an MCP
server - use stderr for logs.
"""

import hashlib
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

# Make the workshop's `lib` package importable (repo root = 4 levels up)
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from chromadb import PersistentClient  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

from lib.constants import DEFAULT_EMBEDDING_MODEL, KNOWLEDGE_BASE_PATH  # noqa: E402
from lib.evaluation import do_top_k_fetching  # noqa: E402
from lib.rag import do_embed, do_ingestion, list_knowledge_base_files  # noqa: E402

TOP_K = 3
# The index is stored on disk, so it is only built once and not every time the server starts.
INDEX_PATH = Path(tempfile.gettempdir()) / "diy_copilot_knowledge_base_index"

# Outdated documents (archive/) are not indexed - they sound right, but they are wrong.
DOCUMENTS = [f for f in list_knowledge_base_files(KNOWLEDGE_BASE_PATH) if "archive/" not in f]


def collection_name(embedding_model: str) -> str:
    """Name of the index collection: a fingerprint of the documents and the embedding model.

    The index is rebuilt when the documents change - or when another embedding model is used
    (vectors of different models are not comparable).
    """
    content = embedding_model + "".join(f"{f}:{(KNOWLEDGE_BASE_PATH / f).stat().st_size}" for f in DOCUMENTS)
    return f"knowledge_base_{hashlib.sha1(content.encode()).hexdigest()[:10]}"


# log_level WARNING keeps the server's own log (stderr) quiet
mcp = FastMCP("company-knowledge-base", log_level="WARNING")

_client = None
_embedding_model = None
_collection_name = None


def log(message: str) -> None:
    """Logs to stderr - stdout is reserved for the MCP protocol."""
    print(f"[knowledge-base-server] {message}", file=sys.stderr, flush=True)


def get_index():
    """Loads the vector index from disk, or builds it on first use."""
    global _client, _embedding_model, _collection_name
    if _client is None:
        # The client passes its environment (API key, model defaults) to the server process.
        # We don't load .env files or Colab secrets here: Colab secrets are only available
        # inside the notebook kernel, not in a subprocess.
        _embedding_model = os.environ.get("DEFAULT_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        _collection_name = collection_name(_embedding_model)
        _client = PersistentClient(path=str(INDEX_PATH))
        existing = [c.name for c in _client.list_collections()]
        if _collection_name not in existing or _client.get_collection(_collection_name).count() == 0:
            log("building the knowledge base index (only on first use) ...")
            # lib prints progress and retry notes to stdout - redirect them to stderr
            with redirect_stdout(sys.stderr):
                do_ingestion(
                    file_names=DOCUMENTS,
                    data_path=KNOWLEDGE_BASE_PATH,
                    embedding_model=_embedding_model,
                    chromadb_client=_client,
                    collection_name=_collection_name,
                    add_file_header=True,
                )
    return _client


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Searches the company's internal knowledge base and returns the most relevant sections.

    The knowledge base contains business policies (e.g. meeting room booking in Berlin and
    Munich, desk sharing, parking), engineering guidelines (Python coding, API design,
    testing, git and code review) and security requirements (secrets, logging, data
    protection, use of AI assistants). Only current documents are searched. Use it whenever
    a question depends on internal rules or conventions of the company.

    Args:
        query: What to search for, phrased like the wording of a policy or guideline.

    Returns:
        The most relevant sections, each with the document and line range it comes from.
    """
    log(f"search_knowledge_base(query={query!r})")
    client = get_index()
    with redirect_stdout(sys.stderr):
        chunks = do_top_k_fetching(do_embed(query, _embedding_model), TOP_K, client, _collection_name)
    return "\n\n---\n\n".join(f"Source: {chunk.metadata.origin}\n{chunk.chunk}" for chunk in chunks)


if __name__ == "__main__":
    mcp.run()
