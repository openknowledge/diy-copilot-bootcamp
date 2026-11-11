"""Retrieval evaluation for the code base knowledge base.

The origin of a piece of knowledge is a file and a range of lines, written as
``"<file>:<start_line>-<end_line>"``, e.g. ``"roomie/config.py:29-31"``.
A retrieved chunk counts as relevant if it comes from the same file as the
ground truth and its line range overlaps the ground truth line range. In the
evaluation dataset, several origins can be given separated by ``;``.
"""

import csv
import time
from pathlib import Path
from typing import Callable

from pydantic import BaseModel


class Metadata(BaseModel):
    """Metadata of a chunk stored in the knowledge base."""

    source: str  # path relative to the code base root, e.g. "roomie/config.py"
    start_line: int  # 1-based, inclusive
    end_line: int  # 1-based, inclusive

    @property
    def origin(self) -> str:
        return f"{self.source}:{self.start_line}-{self.end_line}"


class FetchedChunk(BaseModel):
    """A chunk fetched from the knowledge base."""

    chunk: str
    metadata: Metadata


class TestdataItem(BaseModel):
    """A test data item with its question, expected answer and origin."""

    input: str
    output: str
    source: str
    difficulty: str = "easy"  # "easy" or "hard" (phrased like a real developer question)


class EvaluationResult(BaseModel):
    """The aggregated evaluation metrics."""

    mean_hit_rate: float
    mean_reciprocal_rank: float
    mean_precision: float


def parse_origin(origin: str) -> Metadata:
    """Parses ``"file:start-end"`` (or ``"file:line"``) into a Metadata object."""
    source, _, lines = origin.rpartition(":")
    start, _, end = lines.partition("-")
    return Metadata(source=source, start_line=int(start), end_line=int(end or start))


def is_relevant(ground_truth: str, retrieved: Metadata) -> bool:
    """Returns True if the retrieved chunk overlaps the ground truth origin."""
    expected = parse_origin(ground_truth)
    return (
        expected.source == retrieved.source
        and retrieved.start_line <= expected.end_line
        and expected.start_line <= retrieved.end_line
    )


def calculate_hit_rate(ground_truth: list[str], retrieved: list[Metadata]) -> int:
    """1 if any retrieved chunk is relevant for any ground truth origin, else 0."""
    for metadata in retrieved:
        if any(is_relevant(gt, metadata) for gt in ground_truth):
            return 1
    return 0


def calculate_reciprocal_rank(ground_truth: list[str], retrieved: list[Metadata]) -> float:
    """1/rank of the first relevant retrieved chunk, or 0.0 if there is none."""
    for rank, metadata in enumerate(retrieved, start=1):
        if any(is_relevant(gt, metadata) for gt in ground_truth):
            return 1 / rank
    return 0.0


def calculate_precision(ground_truth: list[str], retrieved: list[Metadata]) -> float:
    """The fraction of retrieved chunks that are relevant (precision at k)."""
    if not retrieved:
        return 0.0
    relevant = sum(1 for metadata in retrieved if any(is_relevant(gt, metadata) for gt in ground_truth))
    return relevant / len(retrieved)


def do_top_k_fetching(
    user_input_embedding: list[float],
    top_k: int,
    chromadb_client,
    collection_name: str = "default",
) -> list[FetchedChunk]:
    """Fetches the *top_k* semantically closest chunks from a ChromaDB collection.

    Parameters
    ----------
    user_input_embedding : list[float]
        The embedding of the user input.
    top_k : int
        Number of closest chunks to retrieve.
    chromadb_client
        A ChromaDB client instance.
    collection_name : str, optional
        Name of the collection, by default ``"default"``.

    Returns
    -------
    list[FetchedChunk]
        The fetched chunks with metadata, closest first.
    """
    collection = chromadb_client.get_collection(name=collection_name)
    query_result = collection.query(query_embeddings=[user_input_embedding], n_results=top_k)
    chunks = query_result["documents"][0]
    metadatas = query_result["metadatas"][0]
    return [
        FetchedChunk(chunk=chunk, metadata=Metadata(**metadata))
        for chunk, metadata in zip(chunks, metadatas)
    ]


def load_testdata_from_csv(path: Path) -> list[TestdataItem]:
    """Loads test data from a CSV with the columns
    question, ground_truth_origin, ground_truth_answer and (optionally) difficulty."""
    with open(path, newline="", encoding="utf-8") as f:
        return [
            TestdataItem(
                input=row["question"],
                output=row["ground_truth_answer"],
                source=row["ground_truth_origin"],
                difficulty=row.get("difficulty") or "easy",
            )
            for row in csv.DictReader(f)
        ]


def run_evaluation(
    top_k: int,
    testdata_items: list[TestdataItem],
    rag_function: Callable,
    sleep_seconds: float = 0,
    verbose: bool = False,
) -> EvaluationResult:
    """Runs a retrieval evaluation over test data using the given RAG function.

    Parameters
    ----------
    top_k : int
        Number of results to retrieve per query.
    testdata_items : list[TestdataItem]
        The test data to evaluate against.
    rag_function : Callable
        A function with signature ``(user_input: str, top_k: int) -> list[FetchedChunk]``.
    sleep_seconds : float, optional
        Seconds to sleep between test items to stay within API rate limits
        (relevant for the Gemini free tier when the RAG function calls an LLM).
    verbose : bool, optional
        Print the result for every test item.

    Returns
    -------
    EvaluationResult
        The mean hit rate, reciprocal rank and precision.
    """
    hit_rates, reciprocal_ranks, precisions = [], [], []

    for i, item in enumerate(testdata_items):
        if i > 0 and sleep_seconds > 0:
            time.sleep(sleep_seconds)

        # The same knowledge can live in several places (e.g. code and docs),
        # so an item may list multiple origins separated by ";".
        ground_truth = item.source.split(";")
        fetched_chunks = rag_function(user_input=item.input, top_k=top_k)
        retrieved = [chunk.metadata for chunk in fetched_chunks]

        hit_rates.append(calculate_hit_rate(ground_truth, retrieved))
        reciprocal_ranks.append(calculate_reciprocal_rank(ground_truth, retrieved))
        precisions.append(calculate_precision(ground_truth, retrieved))

        if verbose:
            mark = "HIT " if hit_rates[-1] else "MISS"
            print(f"{mark} {item.input}\n     expected {item.source}, got {[m.origin for m in retrieved]}")

    return EvaluationResult(
        mean_hit_rate=sum(hit_rates) / len(hit_rates),
        mean_reciprocal_rank=sum(reciprocal_ranks) / len(reciprocal_ranks),
        mean_precision=sum(precisions) / len(precisions),
    )
