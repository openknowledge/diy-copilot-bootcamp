# Roomie demo image: API + web UI on port 8000
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Install the dependencies first (cached layer), then the code
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY roomie ./roomie

# Demo bookings for the next business days, no-show job active
ENV ROOMIE_DEMO_DATA=1 \
    ROOMIE_RUN_SCHEDULER=1

EXPOSE 8000
CMD ["uvicorn", "roomie.main:app", "--host", "0.0.0.0", "--port", "8000"]
