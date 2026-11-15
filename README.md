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

| Notebook | Topic |
|---|---|
| `00_guardrails` | Guarding input, output and context: token limits, redaction, topic guard, LLM as a judge, indirect prompt injection |
| `01_function_calling` | Tools under the hood: tool declarations, tool calls, the tool loop, human in the loop |
| `02_mcp` | Model Context Protocol: JSON-RPC by hand, discovering and calling tools, writing an MCP server, resources and prompts |
| `03_context_engineering` | Where the tokens go, prompt caching, progressive disclosure with skills, history condensing |
| `04_agents` | A coding agent fixes a bug in Roomie: tools, `AGENTS.md`, agentic RAG, approval rules, Google ADK |

### New to Python?

`python_cheatsheet.ipynb` collects the Python basics needed in the workshop
(strings, lists, dictionaries, loops, functions, JSON, Pydantic, reading error
messages) with small examples you can run.

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
| `python_cheatsheet.ipynb` | Python basics for the workshop |
| `lib/` | Shared helpers (environment, retries, RAG, evaluation, MCP client, coding agent, ...) |
| `setup/` | Installs the dependencies into the Colab environment (used by the setup cell of every notebook) |
| `data/codebase/roomie/` | The fictional code base the assistant works on (runnable, with tests) |
| `data/knowledge_base/` | Internal knowledge for RAG: `domain/`, `engineering/`, `security/`, `hr/`, `it/` (outdated versions in `archive/` folders on purpose) |
| `data/issue_tracker/` | Ticket export of the team that owns Roomie |
| `data/evaluation/` | Evaluation dataset for the retrieval (+ script to rebuild it) |
| `data/skills/` | Skills of the team that owns Roomie (Agent Skills format) |
| `data/cache/` | Cache of embedding vectors, so the free tier limit of 1000 embeddings per day is not exceeded (see its README) |
| `AGENTS.md` | Instructions for coding agents working on this repository |
