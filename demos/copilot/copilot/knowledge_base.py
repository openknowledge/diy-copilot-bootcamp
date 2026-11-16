"""Semantic search over the company knowledge base (RAG retrieval).

The documents are chunked like in the workshop (Markdown splitter, 1000 characters,
100 overlap, ``# File: <path>`` header), embedded with Gemini and kept in memory as a
numpy matrix - the knowledge base is small, a vector database is not needed.

Embeddings are cached in SQLite. The cache of the workshop (data/cache/embeddings.sqlite)
can be used as a read-only seed: it contains the same chunks, so building the index
usually costs no embedding requests at all.
"""

import hashlib
import logging
import sqlite3
import threading
from array import array
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from copilot import llm, settings

logger = logging.getLogger("copilot.knowledge_base")


@dataclass
class Chunk:
    source: str  # path relative to the knowledge base, e.g. "security/secrets-and-logging.md"
    start_line: int
    end_line: int
    text: str  # with "# File: ..." header, as embedded

    @property
    def location(self) -> str:
        return f"{self.source}:{self.start_line}-{self.end_line}"


@dataclass
class SearchResult:
    chunk: Chunk
    score: float


# --- Documents and chunks ---------------------------------------------------------


def list_documents(root: Path = settings.KNOWLEDGE_BASE_PATH) -> list[str]:
    """All Markdown documents, without outdated versions in archive/ folders."""
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.md")
        if not any(part.startswith(".") or part == "archive" for part in path.relative_to(root).parts)
    )


def _line_ranges(text: str, chunks: list[str]) -> list[tuple[int, int]]:
    ranges, search_from = [], 0
    for chunk in chunks:
        start = text.find(chunk, search_from)
        if start == -1:
            start = text.find(chunk)
        end = start + len(chunk)
        ranges.append((text.count("\n", 0, start) + 1, text.count("\n", 0, end) + 1))
        search_from = start + 1
    return ranges


def load_chunks(root: Path = settings.KNOWLEDGE_BASE_PATH) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
    )
    chunks = []
    for source in list_documents(root):
        content = (root / source).read_text(encoding="utf-8")
        parts = splitter.split_text(content)
        for part, (start, end) in zip(parts, _line_ranges(content, parts)):
            chunks.append(Chunk(source=source, start_line=start, end_line=end, text=f"# File: {source}\n{part}"))
    return chunks


# --- Embedding cache ------------------------------------------------------------------
# Same key as in the workshop: sha256("model|task_type|text"), vectors as float32.


def _cache_key(text: str, task_type: str | None) -> str:
    return hashlib.sha256(f"{settings.EMBEDDING_MODEL}|{task_type}|{text}".encode("utf-8")).hexdigest()


def _read_cache(connection: sqlite3.Connection, keys: list[str]) -> dict[str, list[float]]:
    found = {}
    for i in range(0, len(keys), 500):
        part = keys[i : i + 500]
        rows = connection.execute(
            f"SELECT key, vector FROM embeddings WHERE key IN ({','.join('?' * len(part))})", part
        ).fetchall()
        found.update({key: array("f", blob).tolist() for key, blob in rows})
    return found


def _own_cache() -> sqlite3.Connection:
    settings.CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.CACHE_PATH, timeout=30)
    connection.execute("CREATE TABLE IF NOT EXISTS embeddings (key TEXT PRIMARY KEY, model TEXT, vector BLOB)")
    return connection


def _seed_cache() -> sqlite3.Connection | None:
    if not settings.SEED_CACHE_PATH.is_file():
        return None
    # Read-only, never modifies the workshop's file
    return sqlite3.connect(f"file:{settings.SEED_CACHE_PATH}?mode=ro&immutable=1", uri=True)


def embed_cached(texts: list[str], task_type: str | None = None) -> list[list[float]]:
    """Embeds texts; texts that were embedded before are taken from the caches."""
    keys = [_cache_key(text, task_type) for text in texts]
    with _own_cache() as own:
        found = _read_cache(own, list(set(keys)))
        seed = _seed_cache()
        if seed is not None:
            missing_keys = [key for key in set(keys) if key not in found]
            from_seed = _read_cache(seed, missing_keys) if missing_keys else {}
            seed.close()
            found.update(from_seed)
        missing = list(dict.fromkeys(text for text, key in zip(texts, keys) if key not in found))
        for i in range(0, len(missing), 100):
            batch = missing[i : i + 100]
            logger.info("embedding %d new text(s)", len(batch))
            vectors = llm.embed(batch, task_type=task_type)
            new = {_cache_key(text, task_type): array("f", vector).tolist() for text, vector in zip(batch, vectors)}
            own.executemany(
                "INSERT OR REPLACE INTO embeddings (key, model, vector) VALUES (?, ?, ?)",
                [(key, settings.EMBEDDING_MODEL, array("f", vector).tobytes()) for key, vector in new.items()],
            )
            own.commit()
            found.update(new)
    return [found[key] for key in keys]


# --- Index --------------------------------------------------------------------------


def _normalize(matrix: np.ndarray) -> np.ndarray:
    return matrix / np.linalg.norm(matrix, axis=-1, keepdims=True)


class KnowledgeBaseIndex:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.chunks: list[Chunk] = []
        self._matrix: np.ndarray | None = None

    def build(self) -> None:
        """Loads, chunks and embeds the knowledge base (only once)."""
        with self._lock:
            if self._matrix is not None:
                return
            chunks = load_chunks()
            vectors = embed_cached([chunk.text for chunk in chunks])
            self.chunks, self._matrix = chunks, _normalize(np.array(vectors, dtype=np.float32))
            documents = len({chunk.source for chunk in chunks})
            logger.info("knowledge base index ready: %d chunks from %d documents", len(chunks), documents)

    def search(self, query: str, top_k: int = settings.TOP_K) -> list[SearchResult]:
        """Returns the top_k chunks most similar to the query, best first."""
        self.build()
        query_vector = _normalize(np.array(embed_cached([query])[0], dtype=np.float32))
        scores = self._matrix @ query_vector
        best = np.argsort(-scores)[:top_k]
        return [SearchResult(chunk=self.chunks[i], score=float(scores[i])) for i in best]


index = KnowledgeBaseIndex()


def format_results(results: list[SearchResult]) -> str:
    """Formats search results as context for the model (or as an MCP tool result)."""
    return "\n\n---\n\n".join(f"Source: {r.chunk.location}\n{r.chunk.text}" for r in results)
