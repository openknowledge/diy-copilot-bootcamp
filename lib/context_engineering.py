"""Helpers for the context engineering lesson (day-02/solutions/03_context_engineering).

They keep the notebook short: counting tokens, the prepared coding session, the tool loop,
loading skills and shrinking conversations.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml
from litellm import completion, completion_cost, token_counter

from lib.constants import CODEBASE_PATH, DEFAULT_GENERATION_MODEL
from lib.retry import call_with_retry

# --- Tokens and costs ----------------------------------------------------------


def count_tokens(text: str, model: str = DEFAULT_GENERATION_MODEL) -> int:
    """Estimates the number of tokens of a text.

    LiteLLM counts locally with a generic tokenizer. For Gemini it underestimates by about 20% -
    good enough to compare variants. The exact numbers are in `response.usage`.
    """
    return token_counter(model=model, text=text)


def cached_tokens(response) -> int:
    """The number of prompt tokens that came from the provider's cache."""
    details = response.usage.prompt_tokens_details
    return (details.cached_tokens if details else None) or 0


def print_usage(label: str, response) -> None:
    """Prints the token usage and the costs of a response (cached tokens are cheaper)."""
    try:
        costs = f"{completion_cost(completion_response=response):.6f} USD"
    except Exception:
        costs = "unknown"
    print(f"{label:28} prompt tokens: {response.usage.prompt_tokens:6}   cached: {cached_tokens(response):6}   costs: {costs}")


def message_text(message: dict) -> str:
    """The text of a message as it is sent to the model (content or tool call)."""
    if message.get("tool_calls"):
        return json.dumps(message["tool_calls"])
    return message["content"] or ""


def history_tokens(messages: list[dict], model: str = DEFAULT_GENERATION_MODEL) -> int:
    """Estimates the number of tokens of a conversation."""
    return sum(count_tokens(message_text(m), model) for m in messages)


def _context_part(message: dict) -> str:
    if message["role"] == "tool":
        return "tool results"
    if message["role"] == "user" and len(message["content"]) > 1000:
        return "pasted logs and test output"
    return {"system": "system prompt", "user": "developer messages", "assistant": "assistant messages"}[message["role"]]


def token_breakdown(messages: list[dict], tool_declarations: list[dict], model: str = DEFAULT_GENERATION_MODEL) -> pd.DataFrame:
    """Tokens per part of the context (system prompt, tool results, ...), largest first."""
    rows = [{"part": _context_part(m), "tokens": count_tokens(message_text(m), model)} for m in messages]
    rows.append({"part": "tool declarations", "tokens": count_tokens(json.dumps(tool_declarations), model)})
    return pd.DataFrame(rows).groupby("part")["tokens"].sum().sort_values(ascending=False).to_frame()


def token_growth(messages: list[dict], tool_declarations: list[dict], model: str = DEFAULT_GENERATION_MODEL) -> pd.DataFrame:
    """The requests a harness sends during the conversation and their prompt tokens.

    The harness calls the model after every message of the developer and after every tool result,
    each time with everything that came before.
    """
    declarations = count_tokens(json.dumps(tool_declarations), model)
    rows, sent_in_total = [], 0
    for index, message in enumerate(messages):
        if message["role"] in ("user", "tool"):
            prompt_tokens = history_tokens(messages[: index + 1], model) + declarations
            sent_in_total += prompt_tokens
            rows.append({
                "request": len(rows) + 1,
                "after": f"{message['role']}: {message_text(message)[:40]}",
                "prompt tokens": prompt_tokens,
                "sent in total": sent_in_total,
            })
    return pd.DataFrame(rows).set_index("request")


# --- The read_file tool ---------------------------------------------------------


def read_file(path: str) -> str:
    """Reads a file of the Roomie code base."""
    file = (CODEBASE_PATH / path).resolve()
    if not file.is_relative_to(CODEBASE_PATH.resolve()) or not file.is_file():
        return f"Error: '{path}' is not a file of the Roomie code base."
    return file.read_text()


READ_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Reads a file of the Roomie code base and returns its content.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path relative to the repository root, e.g. 'roomie/models.py'."}},
            "required": ["path"],
        },
    },
}


# --- The tool loop (see the function calling lesson) ----------------------------------


def execute_tool_call(tool_call, tools: dict) -> str:
    """Executes a tool call and always returns a string for the model - also in case of errors."""
    name = tool_call.function.name
    if name not in tools:
        return f"Error: unknown tool '{name}'. Available tools: {list(tools)}"
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        return "Error: the arguments are not valid JSON."
    try:
        return str(tools[name](**arguments))
    except Exception as error:
        return f"Error while executing {name}: {type(error).__name__}: {error}"


@dataclass
class ToolLoopResult:
    answer: str
    requests: int
    prompt_tokens: int
    costs: float


def run_tool_loop(messages: list[dict], tools: dict, tool_declarations: list[dict], model: str, max_steps: int = 5) -> ToolLoopResult:
    """Calls the model with the conversation; executes tool calls until the model answers with text.

    Prints every tool call. Doesn't change the given list of messages.
    """
    messages = list(messages)
    prompt_tokens, costs = 0, 0.0
    for step in range(1, max_steps + 1):
        response = call_with_retry(completion, model=model, messages=messages, tools=tool_declarations, temperature=0.0)
        prompt_tokens += response.usage.prompt_tokens
        try:
            costs += completion_cost(completion_response=response)
        except Exception:
            pass
        message = response.choices[0].message
        messages.append(message.model_dump())
        if not message.tool_calls:
            return ToolLoopResult(message.content or "", step, prompt_tokens, costs)
        for tool_call in message.tool_calls:
            print(f"[step {step}] {tool_call.function.name}({tool_call.function.arguments})")
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": execute_tool_call(tool_call, tools)})
    return ToolLoopResult("I could not finish the task within the allowed number of steps.", max_steps, prompt_tokens, costs)


def run_assistant(system_prompt: str, question: str, tools: dict, tool_declarations: list[dict], model: str, max_steps: int = 5) -> str:
    """Answers a question, letting the model call tools as often as it needs (up to max_steps)."""
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": question}]
    return run_tool_loop(messages, tools, tool_declarations, model, max_steps).answer


# --- Skills ------------------------------------------------------------------------


def read_skill(skill_dir: Path) -> dict:
    """Reads the SKILL.md file of a skill: YAML frontmatter between '---' lines, followed by the instructions."""
    _, frontmatter, body = (skill_dir / "SKILL.md").read_text().split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    return {"name": metadata["name"], "description": metadata["description"], "instructions": body.strip(), "path": skill_dir}


def load_skills(skills_path: Path) -> dict[str, dict]:
    """Reads all skills in a folder. Returns a dict: name -> {name, description, instructions, path}."""
    skill_dirs = sorted(d for d in Path(skills_path).iterdir() if (d / "SKILL.md").exists())
    return {skill["name"]: skill for skill in map(read_skill, skill_dirs)}


# --- Shrinking conversations ------------------------------------------------------


def turn_starts(messages: list[dict]) -> list[int]:
    """Indices of the messages where a turn starts (messages of the developer)."""
    return [index for index, message in enumerate(messages) if message["role"] == "user"]


def clear_old_tool_results(messages: list[dict], keep_last: int = 1) -> list[dict]:
    """Returns a copy of the conversation in which only the last tool results keep their content.

    Older results are replaced by a placeholder that tells the model how to get them again.
    The tool calls stay, so the structure of the conversation is still valid.
    """
    calls = {call["id"]: call["function"] for m in messages for call in m.get("tool_calls") or []}
    tool_indices = [index for index, message in enumerate(messages) if message["role"] == "tool"]
    to_clear = set(tool_indices[: max(len(tool_indices) - keep_last, 0)])
    cleared = []
    for index, message in enumerate(messages):
        if index in to_clear:
            call = calls[message["tool_call_id"]]
            message = {**message, "content": f"[Result removed to save context. Call {call['name']}({call['arguments']}) again if you need it.]"}
        cleared.append(message)
    return cleared


def format_transcript(messages: list[dict], max_chars: int = 600) -> str:
    """Turns messages into a plain text transcript; long contents (files, logs) are shortened."""
    lines = []
    for message in messages:
        if message.get("tool_calls"):
            calls = ", ".join(f"{c['function']['name']}({c['function']['arguments']})" for c in message["tool_calls"])
            lines.append(f"ASSISTANT called {calls}")
            continue
        content = message["content"]
        if len(content) > max_chars:
            content = content[:max_chars] + f" [... {len(content) - max_chars} more characters]"
        lines.append(f"{message['role'].upper()}: {content}")
    return "\n\n".join(lines)


# --- The prepared coding session (bug WORK-412) -------------------------------------------

_TRACEBACK = """Traceback (most recent call last):
  File "/app/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 165, in __call__
    await self.app(scope, receive, _send)
  File "/app/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/app/.venv/lib/python3.12/site-packages/starlette/routing.py", line 715, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/app/.venv/lib/python3.12/site-packages/starlette/routing.py", line 735, in app
    await route.handle(scope, receive, send)
  File "/app/.venv/lib/python3.12/site-packages/starlette/routing.py", line 288, in handle
    await self.app(scope, receive, send)
  File "/app/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 301, in app
    raw_response = await run_endpoint_function(dependant=dependant, values=values, is_coroutine=is_coroutine)
  File "/app/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 214, in run_endpoint_function
    return await run_in_threadpool(dependant.call, **values)
  File "/app/roomie/routers/bookings.py", line 20, in create_booking
    return service.create_booking(request, user)
  File "/app/roomie/services/booking_service.py", line 36, in create_booking
    validate_new_booking(request, room, existing, now)
  File "/app/roomie/services/booking_rules.py", line 111, in validate_new_booking
    check_advance_window(request.start, now)
  File "/app/roomie/services/booking_rules.py", line 61, in check_advance_window
    if start <= now:
TypeError: can't compare offset-naive and offset-aware datetimes"""

# A server log as developers paste it: the same traceback for every failing request
_SERVER_LOG = "\n".join(
    f"2026-03-03 10:{minute:02d}:14,118 INFO  roomie.access request_id=req-{minute:04x} GET /api/v2/rooms/availability -> 200\n"
    f"2026-03-03 10:{minute:02d}:31,502 ERROR roomie.main request_id=req-{minute + 100:04x} POST /api/v2/bookings -> 500\n{_TRACEBACK}"
    for minute in range(10, 22)
)

_PYTEST_OUTPUT = """============================= test session starts ==============================
platform linux -- Python 3.12.7, pytest-8.4.2, pluggy-1.6.0
rootdir: /home/dev/roomie
configfile: pyproject.toml
collected 23 items

tests/test_booking_rules.py ..........                                    [ 43%]
tests/test_bookings_api.py ........F                                     [ 82%]
tests/test_rooms_api.py ....                                             [100%]

=================================== FAILURES ===================================
__________________ test_booking_without_timezone_is_rejected ___________________

client = <starlette.testclient.TestClient object at 0x7f3a2c1b9d90>

    def test_booking_without_timezone_is_rejected(client):
        \"\"\"Regression test for WORK-412.\"\"\"
        payload = booking_payload()
        payload["start"] = "2026-03-03T14:00:00"
        payload["end"] = "2026-03-03T15:00:00"
>       response = client.post("/api/v2/bookings", json=payload, headers=ALICE)

tests/test_bookings_api.py:76:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
""" + _TRACEBACK.split("\n", 1)[1] + """
=========================== short test summary info ============================
FAILED tests/test_bookings_api.py::test_booking_without_timezone_is_rejected - TypeError: can't compare offset-naive and offset-aware datetimes
========================= 1 failed, 22 passed in 0.84s ========================="""

SESSION_SYSTEM_PROMPT = (
    "You are a coding assistant for Team Workplace, the team that owns Roomie, the meeting room booking service. "
    "Use the read_file tool to look at the code. Follow the company guidelines and keep your answers short."
)


def _tool_call(call_id: str, name: str, **arguments) -> dict:
    return {"role": "assistant", "content": None, "tool_calls": [{"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}]}


def _tool_result(call_id: str, content: str) -> dict:
    return {"role": "tool", "tool_call_id": call_id, "content": content}


def build_work_412_session() -> list[dict]:
    """The messages of a coding session in which a developer works on bug WORK-412 with the assistant."""
    return [
        {"role": "system", "content": SESSION_SYSTEM_PROMPT},
        {"role": "user", "content": f"The mobile app team reports 500 errors when they create bookings (WORK-412). Here is the server log:\n```\n{_SERVER_LOG}\n```"},
        {"role": "assistant", "content": (
            "All failing requests end with `TypeError: can't compare offset-naive and offset-aware datetimes` in `check_advance_window` "
            "(`roomie/services/booking_rules.py`). The mobile app sends `start`/`end` without offset, e.g. `2026-03-03T10:00:00`. "
            "Pydantic parses them as naive datetimes, and comparing them with the timezone-aware `now` raises the error. "
            "According to API-07, such timestamps must be rejected with a 422 - a 500 is always a bug (API-06).")},
        {"role": "user", "content": "Could we simply assume Berlin time for timestamps without offset? The mobile team would like that."},
        {"role": "assistant", "content": (
            "Technically yes, but I would not do it: API-07 requires rejecting timestamps without offset, guessing hides client bugs, "
            "and around the daylight saving time switch local times are ambiguous (see ADR-0004 and WORK-389). "
            "I recommend rejecting them with a 422 and a dedicated error code, so that clients can show a clear message.")},
        {"role": "user", "content": (
            "Agreed. Decision: we reject timestamps without offset with the new error code ROOM-422-NAIVE-TIME "
            "(exception class NaiveTimestampError). We don't guess the timezone. The check becomes the first rule in "
            "validate_new_booking, in a new function check_timezone_aware. The mobile team agreed to always send offsets.")},
        {"role": "assistant", "content": "Got it: new rule `check_timezone_aware` as the first rule in `validate_new_booking`, raising `NaiveTimestampError` with the code `ROOM-422-NAIVE-TIME`. Let's look at the code."},
        {"role": "user", "content": "Show me the booking rules."},
        _tool_call("call_1", "read_file", path="roomie/services/booking_rules.py"),
        _tool_result("call_1", read_file("roomie/services/booking_rules.py")),
        {"role": "assistant", "content": "`validate_new_booking` runs six rules in a fixed order: slot alignment, duration, business hours, advance window, capacity and overlap. `check_advance_window` is the first rule that compares with `now` - that's where it crashes."},
        {"role": "user", "content": "How are the errors defined?"},
        _tool_call("call_2", "read_file", path="roomie/errors.py"),
        _tool_result("call_2", read_file("roomie/errors.py")),
        {"role": "assistant", "content": "Every error is a subclass of `RoomieError` with a `status_code` and a stable `code`. A central handler converts them into `{\"error\": {\"code\": ..., \"message\": ...}}`."},
        {"role": "user", "content": "And how are the API tests set up?"},
        _tool_call("call_3", "read_file", path="tests/conftest.py"),
        _tool_result("call_3", read_file("tests/conftest.py")),
        {"role": "assistant", "content": "The `client` fixture creates the app with in-memory fakes and a `FakeClock` frozen on Monday, 2 March 2026, 09:00 Berlin time. `booking_payload()` and `at()` build requests; `ALICE`, `BOB` and `FIONA` are the API keys."},
        {"role": "user", "content": f"I wrote the regression test. It fails as expected:\n```\n{_PYTEST_OUTPUT}\n```"},
        {"role": "assistant", "content": "Good - the test reproduces the bug (TEST-07): it fails with the `TypeError`. After the fix it should get a 422 with the new error code."},
        {"role": "user", "content": "Unrelated question: how long do we keep application logs?"},
        {"role": "assistant", "content": "30 days in the central log platform (SEC-05, DP-03)."},
    ]


def print_conversation(messages: list[dict], width: int = 110) -> None:
    """Prints one line per message: role and the beginning of the content."""
    for message in messages:
        if message.get("tool_calls"):
            function = message["tool_calls"][0]["function"]
            content = f"(tool call: {function['name']}({function['arguments']}))"
        else:
            content = message["content"]
        print(f"{message['role']:10} {content[:width].replace(chr(10), ' ')}")
