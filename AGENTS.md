# AGENTS.md – DIY Copilot workshop

Instructions for coding agents working on this repository. For the content of the
workshop, see `README.md`.

## What this repository is

A two-day hands-on workshop: participants learn how modern coding assistants
(GitHub Copilot, Cursor, Claude Code) work by building the building blocks in
Jupyter notebooks. Participants run everything in **Google Colab** with a
**Gemini API key on the free tier**. Most of them have little or no Python
experience.

## Layout

| Path | Content |
|---|---|
| `day-01/solutions/` | models, prompting, augmentation, RAG, RAG evaluation and optimization |
| `day-02/solutions/` | `00_guardrails`, `01_function_calling`, `02_mcp`, `03_context_engineering`, `04_agents` |
| `python_cheatsheet.ipynb` | Python basics (and Pydantic) for participants |
| `lib/` | shared code of the notebooks (see below) |
| `data/codebase/roomie/` | Roomie: fictional FastAPI service for meeting room booking – the *target* of the assistant |
| `data/knowledge_base/` | company rules as Markdown (rule ids like `API-07`, `SEC-04`, `TEST-07`); `archive/` = outdated versions on purpose |
| `data/issue_tracker/tickets.json` | ticket export of Team Workplace (owners of Roomie) |
| `data/evaluation/` | retrieval evaluation dataset (`file:start-end` ground truth), built by `build_evaluation_dataset.py` |
| `data/skills/` | Agent Skills of Team Workplace (used in context engineering) |
| `data/cache/embeddings.sqlite` | checked-in embedding cache (see `data/cache/README.md`) |
| `setup/install_dependencies.py` | installs the locked dependencies into the Colab kernel |
| `_legacy/` | the old version of the workshop (bookstore domain) – don't use or update it |

Important modules in `lib/`: `environment.load_environment()` (API key and default
models, Colab secrets or `.env`), `retry.call_with_retry()` (rate limits, 503s,
fallback model), `rag.py` (chunking, embedding with cache, ingestion),
`evaluation.py`, `completion.py`, and one helper module per day-2 lesson
(`mcp_client.py`, `knowledge_base.py`, `context_engineering.py`, `coding_agent.py`).

## Rules

- **Only solutions are maintained.** The maintainer creates the exercise versions
  (without solutions) by hand. Don't create exercise notebooks.
- **The maintainer edits and commits the notebooks, too.** Edit `.ipynb` files *in
  place* (load the JSON, change only the affected cells, save). Never regenerate a
  whole notebook from another source – that would overwrite the maintainer's changes.
- **Don't commit or push** unless asked. The maintainer pushes.
- **Never read or print `.env`.** LiteLLM tracebacks and `api_base` contain the API
  key in the URL – redact outputs (e.g. `sed -E 's/(key=|AIza)[A-Za-z0-9_-]+/\1REDACTED/g'`).
- **Roomie contains intentional bugs and rule violations** used by the exercises. Don't
  fix them in `data/codebase/roomie`:
  - `WORK-412`: timestamps without timezone offset lead to a 500 (violates API-07)
  - `WORK-421`: the availability view shows weekends
  - `roomie/notifications.py` logs meeting titles (violates SEC-04 / DP-01)
- If the knowledge base, the chunking or the embedding model change, the evaluation
  dataset and the embedding cache must be rebuilt (see `data/cache/README.md`).

## Notebook conventions

- Code and texts in **English**. Use the term **harness** for the program around the model.
- Every notebook starts with the same setup cell (`# >>> SETUP <<<`): it clones the
  repository in Colab, runs `setup/install_dependencies.py` and adds the repository
  root to `sys.path`. Copy it verbatim from an existing notebook.
- Structure of a lesson: title and intro with "During this lesson you will learn",
  setup, then sections `Exercise NN` (cells with `# TODO:` comments, solved),
  `Example` (ready to run), `(Optional) Exercise`, "What did we learn?", and
  `Learnings` at the end. Mention the number of requests in a `>**Free tier:**` note.
- Keep exercises simple: TODOs are prompts, Markdown, short loops and `if`s – no JSON
  schema, no `async` plumbing. Put technical helpers into `lib/`.
- Models come from `load_environment()` – don't hard-code model ids in notebooks.
- Call every LLM and embedding API through `call_with_retry` (or `lib.rag`).

## Gemini free tier and LiteLLM

- Default models: `gemini/gemini-3.1-flash-lite` and `gemini/gemini-embedding-001`;
  fallback `gemini/gemini-3.5-flash-lite` (`lib/constants.py`). `gemini-2.5-flash-lite`
  no longer exists; `gemini-3.6-flash` is a thinking model (empty answers with small
  `max_tokens`).
- Limits: 15 requests per minute per generation model; embeddings 100 texts per minute
  and **1000 texts per day** (every text of a batch counts). Keep notebooks at about
  20–30 LLM requests.
- Gemini via LiteLLM: no `top_k`, no `seed`; `tool_choice="none"` is ignored;
  `safety_settings` don't block inputs. Implicit prompt caching works
  (`usage.prompt_tokens_details.cached_tokens`). Hand-written conversations with tool
  calls are accepted.
- MCP in notebooks: one connection per call (`async with`), sessions kept open across
  cells hang. Pass `env=dict(os.environ)` to server processes (Colab secrets are not
  visible in subprocesses). In servers, stdout is the protocol – log to stderr.

## Running and checking notebooks

```bash
uv sync
cd day-02/solutions/<lesson>
cp <lesson>.ipynb _run.ipynb
uv run jupyter nbconvert --to notebook --execute --allow-errors --ExecutePreprocessor.timeout=900 _run.ipynb --output _run_out.ipynb
# inspect the outputs (redact keys!), then delete _run*.ipynb
```

- Don't save the outputs of local test runs into the solution notebooks (they contain local paths).
- Running notebooks adds embeddings to `data/cache/embeddings.sqlite`; tell the
  maintainer instead of committing it silently.
- Roomie's own tests: `cd data/codebase/roomie && python -m pytest -q` (22 tests).
- Agent runs (`04_agents`) are not deterministic – run them more than once before
  drawing conclusions.
