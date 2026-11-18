"""Retrieval evaluation with Langfuse.

The evaluation dataset of the workshop (data/evaluation/evaluation_dataset.csv, 62 questions
with the expected location in the knowledge base) becomes a Langfuse *dataset*. Every
retrieval variant is run as an *experiment* over this dataset; every question gets the scores
of the workshop: hit rate, reciprocal rank and precision@k. Langfuse shows the runs side by
side, and every question as a trace with the retrieved chunks.

    python -m copilot.evaluation                  # all variants
    python -m copilot.evaluation baseline top-k-8  # selected variants
    python -m copilot.evaluation --list

Only embeddings are needed (no LLM requests). Embeddings are cached; the workshop cache is
used read-only, so most variants cost only a few requests.
"""

import argparse
import csv
import hashlib
import logging
import os
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime

from copilot import settings
from copilot.knowledge_base import KnowledgeBaseIndex, SearchResult, embed_cached

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("copilot.evaluation")

DATASET_NAME = "roomie-retrieval"


# --- Variants ---------------------------------------------------------------------------


@dataclass
class Variant:
    description: str
    top_k: int = settings.TOP_K
    index_params: dict = field(default_factory=dict)


VARIANTS = {
    "baseline": Variant("Like the roomie-rag model: chunks 1000/100, file header, top 4"),
    "no-file-header": Variant("Without the '# File: <path>' header in the chunks", index_params={"file_header": False}),
    "task-types": Variant(
        "Gemini task types RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY",
        index_params={"document_task_type": "RETRIEVAL_DOCUMENT", "query_task_type": "RETRIEVAL_QUERY"},
    ),
    "chunk-500": Variant("Smaller chunks: 500 characters, 50 overlap", index_params={"chunk_size": 500, "chunk_overlap": 50}),
    "top-k-8": Variant("Twice as many chunks: top 8", top_k=8),
}


# --- Metrics (the same as lib/evaluation.py of the workshop) ---------------------------


def parse_origin(origin: str) -> tuple[str, int, int]:
    """'file:start-end' (or 'file:line') -> (file, start, end)"""
    source, _, lines = origin.rpartition(":")
    start, _, end = lines.partition("-")
    return source, int(start), int(end or start)


def is_relevant(origin: str, retrieved: dict) -> bool:
    """A retrieved chunk is relevant if it overlaps the expected lines of the expected file."""
    source, start, end = parse_origin(origin)
    return retrieved["source"] == source and retrieved["start_line"] <= end and start <= retrieved["end_line"]


def relevant_flags(origins: list[str], retrieved: list[dict]) -> list[bool]:
    return [any(is_relevant(origin, chunk) for origin in origins) for chunk in retrieved]


# --- Dataset --------------------------------------------------------------------------------


def load_dataset_rows() -> list[dict]:
    with open(settings.EVALUATION_DATASET_PATH, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def sync_dataset(langfuse) -> None:
    """Creates the dataset (if missing) and upserts all items (stable ids, so re-running is safe)."""
    try:
        langfuse.get_dataset(DATASET_NAME)
    except Exception:  # noqa: BLE001 - not found
        langfuse.create_dataset(
            name=DATASET_NAME,
            description="Questions about the company knowledge base with the expected location "
                        "(file:start-end) – evaluation dataset of the DIY Copilot workshop",
        )
    rows = load_dataset_rows()
    for row in rows:
        langfuse.create_dataset_item(
            dataset_name=DATASET_NAME,
            id="q-" + hashlib.sha1(row["question"].encode()).hexdigest()[:12],
            input={"question": row["question"]},
            expected_output={"origins": row["ground_truth_origin"].split(";"), "answer": row["ground_truth_answer"]},
            metadata={"difficulty": row["difficulty"]},
        )
    logger.info("dataset %s: %d items", DATASET_NAME, len(rows))


# --- Experiment ----------------------------------------------------------------------------


def _chunk_output(result: SearchResult) -> dict:
    chunk = result.chunk
    return {
        "location": chunk.location,
        "source": chunk.source,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "similarity": round(result.score, 3),
        "preview": chunk.text[:300],
    }


def retrieval_scores(*, input, output, expected_output, metadata=None, **kwargs):
    """Item evaluator: hit rate, reciprocal rank and precision@k of one question."""
    from langfuse import Evaluation

    origins = expected_output["origins"]
    flags = relevant_flags(origins, output)
    first = flags.index(True) + 1 if any(flags) else None
    comment = (f"first relevant chunk at rank {first}" if first else "no relevant chunk") + f"; expected: {', '.join(origins)}"
    return [
        Evaluation(name="hit_rate", value=1.0 if first else 0.0, comment=comment),
        Evaluation(name="reciprocal_rank", value=1 / first if first else 0.0, comment=comment),
        Evaluation(name="precision", value=sum(flags) / len(flags) if flags else 0.0,
                   comment=f"{sum(flags)} of {len(flags)} chunks relevant"),
    ]


def averages_by_difficulty(*, item_results, **kwargs):
    """Run evaluator: average scores per difficulty (easy / hard), in addition to the overall averages."""
    from langfuse import Evaluation

    evaluations = []
    for difficulty in ("easy", "hard"):
        results = [r for r in item_results if (_metadata(r.item) or {}).get("difficulty") == difficulty]
        for metric in ("hit_rate", "reciprocal_rank", "precision"):
            values = [e.value for r in results for e in r.evaluations if e.name == metric]
            if values:
                evaluations.append(Evaluation(name=f"{metric}_{difficulty}", value=sum(values) / len(values),
                                              comment=f"average over {len(values)} {difficulty} questions"))
    return evaluations


def _metadata(item) -> dict | None:
    return item.get("metadata") if isinstance(item, dict) else getattr(item, "metadata", None)


def _input(item) -> dict:
    return item["input"] if isinstance(item, dict) else item.input


def run_variant(langfuse, dataset, name: str, variant: Variant) -> None:
    index = KnowledgeBaseIndex(**variant.index_params)
    index.build()
    # Embed all questions in one batch first: the free tier allows 100 texts per minute,
    # many parallel single requests would only run into the rate limit.
    embed_cached([_input(item)["question"] for item in dataset.items], task_type=index.query_task_type)

    def task(*, item, **kwargs):
        return [_chunk_output(r) for r in index.search(_input(item)["question"], top_k=variant.top_k)]

    run_name = f"{name} {datetime.now():%Y-%m-%d %H:%M}"
    result = dataset.run_experiment(
        name=name,
        run_name=run_name,
        description=variant.description,
        task=task,
        evaluators=[retrieval_scores],
        run_evaluators=[averages_by_difficulty],
        max_concurrency=8,
        metadata={"top_k": str(variant.top_k), **{k: str(v) for k, v in variant.index_params.items()},
                  "chunks": str(len(index.chunks))},
    )
    summary = {
        metric: sum(e.value for r in result.item_results for e in r.evaluations if e.name == metric) / len(result.item_results)
        for metric in ("hit_rate", "reciprocal_rank", "precision")
    }
    logger.info("%-15s hit rate %.2f | MRR %.2f | precision %.2f  (%s)", name, summary["hit_rate"],
                summary["reciprocal_rank"], summary["precision"], run_name)


def wait_for_langfuse(timeout_seconds: int = 300) -> None:
    host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "http://localhost:3100"
    deadline = time.time() + timeout_seconds
    while True:
        try:
            with urllib.request.urlopen(f"{host}/api/public/health", timeout=5) as response:
                if response.status == 200:
                    return
        except Exception:  # noqa: BLE001
            pass
        if time.time() > deadline:
            sys.exit(f"Langfuse is not reachable at {host}")
        logger.info("waiting for Langfuse at %s ...", host)
        time.sleep(5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("variants", nargs="*", help=f"variants to run (default: all): {', '.join(VARIANTS)}")
    parser.add_argument("--list", action="store_true", help="list the variants")
    args = parser.parse_args()

    if args.list:
        for name, variant in VARIANTS.items():
            print(f"{name:15} {variant.description}")
        return
    unknown = [v for v in args.variants if v not in VARIANTS]
    if unknown:
        sys.exit(f"Unknown variant(s): {unknown}. Available: {', '.join(VARIANTS)}")

    from langfuse import get_client

    wait_for_langfuse()
    langfuse = get_client()
    sync_dataset(langfuse)
    dataset = langfuse.get_dataset(DATASET_NAME)
    for name in args.variants or VARIANTS:
        run_variant(langfuse, dataset, name, VARIANTS[name])
    langfuse.flush()
    logger.info("done - open Langfuse (http://localhost:3100) → Datasets → %s", DATASET_NAME)


if __name__ == "__main__":
    main()
