# Roomie copilot: OpenAI compatible API (port 8200) with RAG and guardrails
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY copilot ./copilot

# Mounted by docker-compose.yml
ENV KNOWLEDGE_BASE_PATH=/knowledge_base \
    SEED_CACHE_PATH=/seed/embeddings.sqlite \
    CACHE_PATH=/data/embeddings.sqlite

EXPOSE 8200
CMD ["uvicorn", "copilot.openai_api:app", "--host", "0.0.0.0", "--port", "8200"]
