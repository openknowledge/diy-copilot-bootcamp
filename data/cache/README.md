# Embedding cache

`embeddings.sqlite` stores the embedding vectors of all texts that were embedded
while running the workshop notebooks (see `lib/rag.py`). It is part of the
repository, so the embeddings of the solutions don't cost participants any quota.

## Why

The Gemini API free tier allows only **1000 embedded texts per day** per model
(every text in a batch counts). Without the cache, re-ingesting the knowledge
base (other chunk sizes, task types, chunk headers) and repeated evaluations
would use up this limit in a single workshop day.

## How it works

- Key: SHA-256 of `model | task type | text` – only identical texts with the same
  model and task type are reused.
- Value: the vector as binary float32 (column `vector`), plus the model name.
- New embeddings are added automatically; nothing has to be configured.
- Disable the cache with the environment variable `DIY_COPILOT_EMBEDDING_CACHE=0`.

## Rebuilding the cache

Rebuild the cache whenever the knowledge base, the chunking or the embedding model
changes. Embedding everything takes a few hundred requests, so do it on a day with
unused free tier quota.

```bash
# 1. Start with an empty cache
rm data/cache/embeddings.sqlite

# 2. Run all solution notebooks (from the repository root)
for nb in day-01/solutions/*/*.ipynb day-02/solutions/*/*.ipynb; do
  (cd "$(dirname "$nb")" && uv run jupyter nbconvert --to notebook --execute "$(basename "$nb")" \
      --output /tmp/executed.ipynb --ExecutePreprocessor.timeout=1800)
done

# 3. Check the content and commit the file
sqlite3 data/cache/embeddings.sqlite "SELECT model, count(*) FROM embeddings GROUP BY model;"
```

The cache contains **no texts** – only the SHA-256 hash of each text, the model name
and the vector. No API keys and no personal data are stored.

Note: `day-01/solutions/03_rag_basic/03_rag_basic.ipynb` builds its RAG building blocks
itself and calls the embedding API directly, so its embeddings (~60 per run) are not cached.
