"""OpenAI compatible API, so that OpenWebUI (or any OpenAI client) can use the assistants as models.

Only the parts OpenWebUI needs: ``GET /v1/models`` and ``POST /v1/chat/completions``
(with and without streaming).

Run locally:  uv run uvicorn copilot.openai_api:app --port 8200
"""

import json
import logging
import threading
import time
import uuid
from contextlib import asynccontextmanager
from typing import Iterator

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from copilot import settings
from copilot.assistant import guarded_answer, rag_answer
from copilot.knowledge_base import index

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("copilot.api")

MODELS = {
    "roomie-rag": "RAG over the company knowledge base",
    "roomie-rag-guarded": "RAG over the company knowledge base, with guardrails",
}



def _build_index() -> None:
    try:
        index.build()
    except Exception as error:  # noqa: BLE001
        logger.error("building the index failed: %s", type(error).__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the index at startup, but don't block or crash the server if it fails
    # (e.g. missing API key) - the first request tries again.
    threading.Thread(target=_build_index, daemon=True).start()
    yield


app = FastAPI(title="Roomie copilot", version="0.1.0", lifespan=lifespan)


def check_api_key(authorization: str | None) -> None:
    if settings.COPILOT_API_KEY and authorization != f"Bearer {settings.COPILOT_API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API key")


class ChatRequest(BaseModel):
    model: str
    messages: list[dict]
    stream: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "index_chunks": len(index.chunks)}


@app.get("/v1/models")
def list_models(authorization: str | None = Header(default=None)) -> dict:
    check_api_key(authorization)
    return {
        "object": "list",
        "data": [
            {"id": model_id, "object": "model", "created": 0, "owned_by": "team-workplace", "description": description}
            for model_id, description in MODELS.items()
        ],
    }


def _answer(request: ChatRequest) -> Iterator[str]:
    """Runs the assistant; errors are shown as text in the chat instead of breaking the stream."""
    try:
        if request.model == "roomie-rag":
            yield from rag_answer(request.messages, stream=request.stream)
        else:
            yield from guarded_answer(request.messages)
    except Exception as error:  # noqa: BLE001
        logger.exception("request failed")
        # Never include the error message itself: LiteLLM errors can contain the API key
        yield f"\n\n⚠️ The assistant failed ({type(error).__name__}). See `docker compose logs copilot`."


def _chunk(completion_id: str, model: str, delta: dict, finish_reason: str | None = None) -> str:
    payload = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    return f"data: {json.dumps(payload)}\n\n"


@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest, authorization: str | None = Header(default=None)):
    check_api_key(authorization)
    if request.model not in MODELS:
        raise HTTPException(status_code=404, detail=f"Unknown model {request.model!r}. Available: {', '.join(MODELS)}")
    if not request.messages or request.messages[-1].get("role") != "user":
        raise HTTPException(status_code=400, detail="The last message must be a user message.")
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"

    if request.stream:
        def events() -> Iterator[str]:
            yield _chunk(completion_id, request.model, {"role": "assistant", "content": ""})
            for piece in _answer(request):
                yield _chunk(completion_id, request.model, {"content": piece})
            yield _chunk(completion_id, request.model, {}, finish_reason="stop")
            yield "data: [DONE]\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    content = "".join(_answer(request))
    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
