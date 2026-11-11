"""Building blocks for a RAG system over a knowledge base of Markdown documents
(and, if needed, code files)."""

import uuid
from functools import lru_cache
from pathlib import Path

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from litellm import embedding as litellm_embedding

from lib.constants import CODEBASE_FILE_EXTENSIONS, KNOWLEDGE_BASE_FILE_EXTENSIONS
from lib.evaluation import FetchedChunk, Metadata, do_top_k_fetching  # noqa: F401 (re-exported)
from lib.retry import call_with_retry

# Language-aware splitting: Python code is preferably split at class and
# function boundaries, Markdown at headings.
LANGUAGE_BY_EXTENSION = {
    ".py": Language.PYTHON,
    ".md": Language.MARKDOWN,
}


def list_codebase_files(root: str | Path, extensions: tuple[str, ...] = CODEBASE_FILE_EXTENSIONS) -> list[str]:
    """Returns all files of a code base with the given extensions.

    Parameters
    ----------
    root : str | Path
        Root directory of the code base.
    extensions : tuple[str, ...]
        File extensions to include.

    Returns
    -------
    list[str]
        Sorted file paths relative to *root*, using forward slashes.
    """
    root = Path(root)
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in extensions
        and not any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(root).parts)
    )


def list_knowledge_base_files(root: str | Path) -> list[str]:
    """Returns all documents of the knowledge base, relative to *root*."""
    return list_codebase_files(root, extensions=KNOWLEDGE_BASE_FILE_EXTENSIONS)


def load_file_content(path: str | Path) -> str:
    """Loads and returns the text content of a file."""
    return Path(path).read_text(encoding="utf-8")


def do_chunk(text: str, chunk_size: int, chunk_overlap: int, file_name: str | None = None) -> list[str]:
    """Splits text into overlapping chunks.

    If a *file_name* is given, a splitter that knows the syntax of the file
    type is used (e.g. it prefers splitting Python code between functions).

    Parameters
    ----------
    text : str
        The text to split.
    chunk_size : int
        Maximum size of each chunk in characters.
    chunk_overlap : int
        Number of characters to overlap between consecutive chunks.
    file_name : str | None
        Optional file name used to choose a language-aware splitter.

    Returns
    -------
    list[str]
        List of text chunks.
    """
    language = LANGUAGE_BY_EXTENSION.get(Path(file_name).suffix) if file_name else None
    if language is not None:
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=language, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
    else:
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)


def get_line_ranges(text: str, chunks: list[str]) -> list[tuple[int, int]]:
    """Returns the 1-based (start_line, end_line) of every chunk in *text*.

    Chunks are searched in order, so identical chunks at different positions
    get their correct, distinct line ranges.
    """
    ranges = []
    search_from = 0
    for chunk in chunks:
        start_index = text.find(chunk, search_from)
        if start_index == -1:  # the splitter stripped whitespace; fall back to a global search
            start_index = text.find(chunk)
        end_index = start_index + len(chunk)
        start_line = text.count("\n", 0, start_index) + 1
        end_line = text.count("\n", 0, end_index) + 1
        ranges.append((start_line, end_line))
        search_from = start_index + 1
    return ranges


@lru_cache(maxsize=4096)
def _embed_cached(text: str, model: str, task_type: str | None) -> tuple[float, ...]:
    kwargs = {"task_type": task_type} if task_type else {}
    response = call_with_retry(litellm_embedding, model=model, input=text, **kwargs)
    return tuple(response["data"][0]["embedding"])


def do_embed(chunk: str, model: str, task_type: str | None = None) -> list[float]:
    """Embeds a single text and returns its embedding vector.

    Results are cached in memory, so embedding the same question twice (e.g.
    in repeated evaluation runs) does not cost an additional API request.

    Parameters
    ----------
    chunk : str
        The text to embed.
    model : str
        LiteLLM model identifier (e.g. "gemini/gemini-embedding-001").
    task_type : str | None
        Optional Gemini task type, e.g. "RETRIEVAL_QUERY" or "CODE_RETRIEVAL_QUERY".

    Returns
    -------
    list[float]
        The embedding vector.
    """
    return list(_embed_cached(chunk, model, task_type))


def do_batch_embed(
    chunks: list[str], model: str, batch_size: int = 100, task_type: str | None = None
) -> list[list[float]]:
    """Embeds a list of chunks in batches and returns their embedding vectors.

    Parameters
    ----------
    chunks : list[str]
        The text chunks to embed.
    model : str
        LiteLLM model identifier (e.g. "gemini/gemini-embedding-001").
    batch_size : int, optional
        Number of chunks per API call, by default 100 (the Gemini maximum).
    task_type : str | None
        Optional Gemini task type, e.g. "RETRIEVAL_DOCUMENT".

    Returns
    -------
    list[list[float]]
        List of embedding vectors, one per input chunk.
    """
    kwargs = {"task_type": task_type} if task_type else {}
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        response = call_with_retry(litellm_embedding, model=model, input=batch, **kwargs)
        all_embeddings.extend(data["embedding"] for data in response["data"])
    return all_embeddings


def augment(user_input: str, context: list[str]) -> str:
    """Builds an augmented prompt from the user question and retrieved context."""
    prepared_context = "\n\n---\n\n".join(context)
    return f"""Answer the question as precisely as possible, using only the provided
context from our internal knowledge base. Mention the documents you used. If the answer
is not in the context, say "The answer is not available in the context." and do
not make anything up.

Context:
{prepared_context}

Question:
{user_input}

Answer:
"""


def persist_embeddings(
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    chromadb_client,
    collection_name: str = "default",
) -> None:
    """Persists chunks, embeddings and metadata in a ChromaDB collection."""
    collection = chromadb_client.get_or_create_collection(
        name=collection_name, metadata={"hnsw:search_ef": 50}
    )
    ids = [str(uuid.uuid4()) for _ in chunks]
    collection.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)


def do_ingestion(
    file_names: list[str],
    data_path: str | Path,
    embedding_model: str,
    chromadb_client,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    batch_size: int = 100,
    collection_name: str = "default",
    add_file_header: bool = False,
    task_type: str | None = None,
    verbose: bool = False,
) -> None:
    """Ingests files by loading, chunking, embedding and persisting them.

    The collection is recreated, so calling this function twice does not
    duplicate chunks.

    Parameters
    ----------
    file_names : list[str]
        File paths relative to *data_path*.
    data_path : str | Path
        Root directory of the code base.
    embedding_model : str
        LiteLLM model identifier for embeddings.
    chromadb_client
        A ChromaDB client instance.
    chunk_size : int, optional
        Maximum chunk size in characters, by default 1000.
    chunk_overlap : int, optional
        Overlap between consecutive chunks, by default 100.
    batch_size : int, optional
        Batch size for embedding API calls, by default 100.
    collection_name : str, optional
        Name of the collection, by default ``"default"``.
    add_file_header : bool, optional
        Prefix every chunk with a ``# File: <path>`` line before embedding.
        This gives the embedding model context about where a chunk comes from.
    task_type : str | None, optional
        Optional Gemini embedding task type for the documents.
    verbose : bool, optional
        Print progress information.
    """
    from chromadb.errors import NotFoundError

    if chunk_size < 200:
        raise ValueError("chunk_size must be at least 200")

    try:
        chromadb_client.delete_collection(name=collection_name)
    except NotFoundError:
        pass

    data_path = Path(data_path)
    all_chunks: list[str] = []
    all_metadatas: list[dict] = []
    for file_name in file_names:
        content = load_file_content(data_path / file_name)
        chunks = do_chunk(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap, file_name=file_name)
        for chunk, (start_line, end_line) in zip(chunks, get_line_ranges(content, chunks)):
            all_chunks.append(f"# File: {file_name}\n{chunk}" if add_file_header else chunk)
            all_metadatas.append({"source": file_name, "start_line": start_line, "end_line": end_line})
        if verbose:
            print(f"Loaded {len(chunks):>3} chunks from {file_name}")

    # Embed all chunks of all files together to minimise the number of API requests.
    embeddings = do_batch_embed(all_chunks, embedding_model, batch_size=batch_size, task_type=task_type)
    persist_embeddings(all_chunks, embeddings, all_metadatas, chromadb_client, collection_name)

    if verbose:
        print(f"Added {len(all_chunks)} chunks to the knowledge base")
