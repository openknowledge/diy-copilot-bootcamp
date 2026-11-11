# DIY Copilot – Build Your Own Coding Assistant

A two-day hands-on workshop in which you build the building blocks of a coding
assistant yourself – and learn what is behind tools like GitHub Copilot,
Cursor or Claude Code, and how to adapt them to your own needs (e.g. by
connecting your own tools and knowledge bases).

## The scenario

Throughout the workshop the assistant works on **Roomie**, a small fictional
FastAPI service for booking meeting rooms (`data/codebase/roomie`).

Roomie has to follow the rules of our fictional company, which live in an
internal **knowledge base** (`data/knowledge_base`): business policies of the
facility management, company-wide engineering guidelines and security / data
protection requirements. No public model can know these rules – the
assistant learns them via Retrieval Augmented Generation (RAG). This makes it
easy to see when the assistant hallucinates and when it is grounded in
internal knowledge.

## Workshop content

### Day 1 – Foundations

| Notebook | Topic |
|---|---|
| `00_hello_genai` | Calling a model, messages and roles |
| `01_models` | Generation parameters, streaming |
| `02_prompting` | Prompting techniques for a developer support assistant, structured code review |
| `03_rag_basic` | Augmentation and Retrieval Augmented Generation over the knowledge base, RAG for code generation |
| `04_rag_evaluation` | Evaluating the retrieval (hit rate, MRR, precision) |
| `05_rag_optimization` | Embedding task types, chunk headers, query rewriting, HyDE, reranking |

### Day 2 – From assistant to agent

Guarding, function calling and agents.

## Setup

All notebooks run in **Google Colab**. You only need a
[Gemini API key](https://aistudio.google.com/apikey) (the free tier is
sufficient). Add it as a Colab secret named `GEMINI_API_KEY` (key icon in the
left sidebar) and grant the notebook access.

### Running locally (optional)

Prerequisites: Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Create a `.env` file in the repository root:

```
GEMINI_API_KEY=<your key>
# Optional overrides (LiteLLM model ids)
# DEFAULT_GENERATION_MODEL=gemini/gemini-3.1-flash-lite
# DEFAULT_EMBEDDING_MODEL=gemini/gemini-embedding-001
```

## Repository layout

| Path | Content |
|---|---|
| `day-01/`, `day-02/` | Workshop notebooks |
| `lib/` | Shared helpers (completion, RAG, evaluation, environment) |
| `data/codebase/roomie/` | The fictional code base the assistant works on (runnable, with tests) |
| `data/knowledge_base/` | Internal knowledge for RAG: `domain/`, `engineering/`, `security/` |
| `data/issue_tracker/` | Ticket export of the team that owns Roomie |
| `data/evaluation/` | Evaluation dataset for the retrieval (+ script to rebuild it) |
| `data/cache/` | Cache of embedding vectors, so the free tier limit of 1000 embeddings per day is not exceeded (see its README) |
