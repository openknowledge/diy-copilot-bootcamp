"""The two assistants offered as models in OpenWebUI.

* ``roomie-rag``          retrieval from the knowledge base + generation
* ``roomie-rag-guarded``  the same, wrapped in the guardrail pipeline

Both return the answer as text pieces (for streaming). Below the answer, a
collapsible block shows what happened behind the scenes (retrieved chunks,
guard decisions) – that's what the demo is about.
"""

import logging
from typing import Iterator

from copilot import guardrails, llm
from copilot.knowledge_base import SearchResult, format_results, index

logger = logging.getLogger("copilot.assistant")

SYSTEM_PROMPT = """You are the coding assistant of Team Workplace. The team develops Roomie, the meeting \
room booking service of the company (FastAPI, Python). You help developers with questions about the \
company's rules and conventions (engineering, security, data protection) and the Roomie domain \
(room booking policies).

Answer using the context from the internal knowledge base that is given with the question. Mention the \
rule ids (e.g. API-07, SEC-04) and the documents you used. If the context does not contain the answer, \
say so and do not make anything up."""

BLOCKED_RESPONSE = "I'm sorry, but I cannot help with that request."
META_START = "\n\n<details>"  # everything after this is meta information, not part of the answer


# --- Messages ---------------------------------------------------------------------


def message_text(message: dict) -> str:
    """The text of a chat message (content can be a string or a list of parts)."""
    content = message.get("content") or ""
    if isinstance(content, list):
        content = "\n".join(part.get("text", "") for part in content if part.get("type") == "text")
    return content


def clean_history(messages: list[dict]) -> list[dict]:
    """Keeps user/assistant/system messages and removes our meta blocks from earlier answers."""
    cleaned = []
    for message in messages:
        if message.get("role") not in ("system", "user", "assistant"):
            continue
        text = message_text(message)
        if message["role"] == "assistant":
            text = text.split(META_START)[0]
        cleaned.append({"role": message["role"], "content": text})
    return cleaned


def augment(question: str, results: list[SearchResult]) -> str:
    return f"""Context from our internal knowledge base:

{format_results(results)}

Question:
{question}"""


def build_messages(history: list[dict], question: str, results: list[SearchResult]) -> list[dict]:
    """System prompt + earlier conversation + the augmented question."""
    system = [m["content"] for m in history if m["role"] == "system"]
    conversation = [m for m in history[:-1] if m["role"] != "system"]
    return [
        {"role": "system", "content": "\n\n".join([SYSTEM_PROMPT, *system])},
        *conversation,
        {"role": "user", "content": augment(question, results)},
    ]


# --- Meta blocks --------------------------------------------------------------------


def retrieval_block(results: list[SearchResult]) -> str:
    items = "\n".join(
        f"{i}. `{r.chunk.location}` (similarity {r.score:.2f})\n\n```markdown\n{r.chunk.text}\n```"
        for i, r in enumerate(results, start=1)
    )
    return f"{META_START}\n<summary>📚 Knowledge base: {len(results)} chunks retrieved</summary>\n\n{items}\n</details>\n"


def guard_block(log: list[str], verdict: str) -> str:
    items = "\n".join(f"- {line}" for line in log)
    return f"{META_START}\n<summary>🛡️ Guardrails: {verdict}</summary>\n\n{items}\n</details>\n"


# --- Assistants -----------------------------------------------------------------------


def rag_answer(messages: list[dict], stream: bool = True) -> Iterator[str]:
    """RAG: search the knowledge base for the last user message, then answer."""
    history = clean_history(messages)
    question = history[-1]["content"]
    results = index.search(question)
    logger.info("roomie-rag: %d chunks retrieved (%s)", len(results), ", ".join(r.chunk.source for r in results))
    llm_messages = build_messages(history, question, results)
    if stream:
        yield from llm.stream(llm_messages)
    else:
        yield llm.complete(llm_messages)
    yield retrieval_block(results)


def guarded_answer(messages: list[dict]) -> Iterator[str]:
    """RAG wrapped in the guardrail pipeline of the workshop (cheap checks first)."""
    history = clean_history(messages)
    question = history[-1]["content"]
    log: list[str] = []

    # 1. Token limit
    too_long, tokens = guardrails.exceeds_input_token_limit(question)
    if too_long:
        log.append(f"⛔ Token limit: {tokens} tokens (limit {guardrails.settings.MAX_INPUT_TOKENS})")
        yield "Your input is too long. Please paste only the relevant part (e.g. the stack trace)."
        yield guard_block(log, "blocked by the token limit")
        return
    log.append(f"✅ Token limit: {tokens} / {guardrails.settings.MAX_INPUT_TOKENS} tokens")

    # 2. Redaction – of all user messages, earlier ones were sent unredacted by the UI
    findings = []
    for message in history:
        if message["role"] == "user":
            redaction = guardrails.redact(message["content"])
            message["content"] = redaction.text
            findings += redaction.findings
    question = history[-1]["content"]
    log.append(f"✏️ Redacted: {', '.join(sorted(set(findings)))}" if findings else "✅ Redaction: nothing found")

    # 3. Topic guard
    topic = guardrails.check_topic(question)
    if not topic.on_topic:
        log.append(f"⛔ Topic guard: similarity {topic.similarity:.3f} < {guardrails.settings.TOPIC_THRESHOLD} "
                   f"(most similar: “{topic.most_similar_example}”)")
        yield "I can only help with software development topics of Team Workplace."
        yield guard_block(log, "blocked by the topic guard")
        return
    log.append(f"✅ Topic guard: similarity {topic.similarity:.3f} (most similar: “{topic.most_similar_example}”)")

    # 4. Policy judge
    verdict = guardrails.check_policy(question)
    if not verdict.complies_with_policy:
        log.append(f"⛔ Policy judge: violates {', '.join(verdict.violated_rules) or 'the policy'} – {verdict.reason}")
        yield BLOCKED_RESPONSE
        yield guard_block(log, "blocked by the policy judge")
        return
    log.append("✅ Policy judge: complies with AI-02 and C-1..C-3")

    # Generation (not streamed: the output guard needs the complete answer)
    results = index.search(question)
    answer = llm.complete(build_messages(history, question, results))

    # 5. Output guard
    output = guardrails.check_output(answer)
    logger.info("roomie-rag-guarded: redacted=%s topic=%.3f output=%s", findings, topic.similarity, output.decision)
    if output.decision == "block":
        log.append(f"⛔ Output guard: {', '.join(output.findings)}")
        yield BLOCKED_RESPONSE
        yield guard_block(log, "answer blocked by the output guard")
        return
    if output.decision == "needs_approval":
        log.append(f"⚠️ Output guard: needs approval – {', '.join(output.findings)}")
        answer = f"> ⚠️ **Please review before running anything** – this answer contains: {', '.join(output.findings)}\n\n{answer}"
    else:
        log.append("✅ Output guard: nothing dangerous found")

    yield answer
    yield guard_block(log, "passed" + (" (with warning)" if output.decision == "needs_approval" else ""))
    yield retrieval_block(results)
