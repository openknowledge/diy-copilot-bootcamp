"""Search over the company knowledge base with an index on disk - used by the MCP server of the MCP lesson.

The index is stored in a temporary folder, so that it is only built once and not every time the server
process starts. Everything here writes to stderr only: in an MCP server, stdout belongs to the protocol.
"""

import hashlib
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

from lib.constants import DEFAULT_EMBEDDING_MODEL, KNOWLEDGE_BASE_PATH
from lib.evaluation import do_top_k_fetching
from lib.rag import do_embed, do_ingestion, list_knowledge_base_files

INDEX_PATH = Path(tempfile.gettempdir()) / "diy_copilot_knowledge_base_index"

# Outdated documents (archive/) are not indexed - they sound right, but they are wrong.
DOCUMENTS = [f for f in list_knowledge_base_files(KNOWLEDGE_BASE_PATH) if "archive/" not in f]

_index = {"client": None, "embedding_model": None, "collection": None}


def _collection_name(embedding_model: str) -> str:
    """A fingerprint of the documents and the embedding model.

    The index is rebuilt when the documents change - or when another embedding model is used
    (vectors of different models are not comparable).
    """
    content = embedding_model + "".join(f"{f}:{(KNOWLEDGE_BASE_PATH / f).stat().st_size}" for f in DOCUMENTS)
    return f"knowledge_base_{hashlib.sha1(content.encode()).hexdigest()[:10]}"


def _get_index():
    """Loads the index from disk, or builds it on first use."""
    if _index["client"] is None:
        from chromadb import PersistentClient

        # The MCP client passes its environment (API key, model defaults) to the server process.
        # Colab secrets are only available in the notebook kernel, not in a subprocess.
        embedding_model = os.environ.get("DEFAULT_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        collection = _collection_name(embedding_model)
        client = PersistentClient(path=str(INDEX_PATH))
        existing = [c.name for c in client.list_collections()]
        if collection not in existing or client.get_collection(collection).count() == 0:
            print("[knowledge-base] building the index (only on first use) ...", file=sys.stderr, flush=True)
            with redirect_stdout(sys.stderr):  # lib prints progress and retry notes
                do_ingestion(file_names=DOCUMENTS, data_path=KNOWLEDGE_BASE_PATH, embedding_model=embedding_model,
                             chromadb_client=client, collection_name=collection, add_file_header=True)
        _index.update(client=client, embedding_model=embedding_model, collection=collection)
    return _index


def search(query: str, top_k: int = 3) -> str:
    """Returns the top_k most relevant sections of the knowledge base, each with its source."""
    index = _get_index()
    with redirect_stdout(sys.stderr):
        chunks = do_top_k_fetching(do_embed(query, index["embedding_model"]), top_k, index["client"], index["collection"])
    return "\n\n---\n\n".join(f"Source: {chunk.metadata.origin}\n{chunk.chunk}" for chunk in chunks)
