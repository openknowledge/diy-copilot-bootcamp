"""A small coding agent for the agents lesson (day-02/solutions/04_agents).

The agent works on a copy of the Roomie code base (the *workspace*), so that it can't break the
original. The tools are plain Python functions with docstrings - our own agent loop uses the
hand-written declarations in TOOL_DECLARATIONS, frameworks like Google ADK generate them from the
docstrings.
"""

import ast
import difflib
import json
import logging
import shutil
import subprocess
import sys
import tempfile
import warnings
from collections.abc import Callable
from pathlib import Path

from litellm import completion

from lib.constants import CODEBASE_PATH
from lib.retry import call_with_retry

WORKSPACE = Path(tempfile.gettempdir()) / "roomie-workspace"
_IGNORED = shutil.ignore_patterns("__pycache__", ".pytest_cache")


def create_workspace() -> Path:
    """Creates a fresh copy of the Roomie code base for the agent (an existing copy is replaced)."""
    shutil.rmtree(WORKSPACE, ignore_errors=True)
    shutil.copytree(CODEBASE_PATH, WORKSPACE, ignore=_IGNORED)
    return WORKSPACE


def _workspace_files() -> list[Path]:
    return sorted(p for p in WORKSPACE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts)


def _resolve(path: str) -> Path:
    """Resolves a path from the model - it must stay inside the workspace."""
    file = (WORKSPACE / path).resolve()
    if not file.is_relative_to(WORKSPACE.resolve()):
        raise ValueError(f"'{path}' is outside of the repository.")
    return file


# --- The tools of the agent ------------------------------------------------------------


def list_files(directory: str = ".") -> str:
    """Lists all files of the repository or of one of its directories.

    Args:
        directory: A directory relative to the repository root, e.g. 'roomie/services'. Default: the whole repository.
    """
    folder = _resolve(directory)
    return "\n".join(str(p.relative_to(WORKSPACE)) for p in _workspace_files() if p.is_relative_to(folder)) or "No files."


def read_file(path: str) -> str:
    """Returns the content of a file of the repository.

    Args:
        path: The path relative to the repository root, e.g. 'roomie/models.py'.
    """
    file = _resolve(path)
    if not file.is_file():
        return f"Error: the file '{path}' does not exist. Use list_files to see all files."
    return file.read_text()


def search_code(text: str) -> str:
    """Searches all files of the repository for a text and returns the matching lines as 'path:line: content'.

    Args:
        text: The exact text to search for, e.g. a function name or an error code.
    """
    matches = []
    for file in _workspace_files():
        for number, line in enumerate(file.read_text().splitlines(), start=1):
            if text in line:
                matches.append(f"{file.relative_to(WORKSPACE)}:{number}: {line.strip()}")
    if len(matches) > 50:
        return "\n".join(matches[:50]) + f"\n... {len(matches) - 50} more matches. Search for a more specific text."
    return "\n".join(matches) or "No matches."


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replaces a piece of text in a file. To add code, use the lines next to the new code as old_text and repeat them in new_text.

    Args:
        path: The path relative to the repository root.
        old_text: The exact text to replace. It must occur exactly once in the file.
        new_text: The text that replaces old_text.
    """
    file = _resolve(path)
    if not file.is_file():
        return f"Error: the file '{path}' does not exist."
    content = file.read_text()
    occurrences = content.count(old_text)
    if occurrences == 0:
        return f"Error: old_text was not found in {path}. Read the file again and copy the text exactly."
    if occurrences > 1:
        return f"Error: old_text occurs {occurrences} times in {path}. Add surrounding lines so that it is unique."
    file.write_text(content.replace(old_text, new_text))
    return f"Edited {path}."


def run_tests() -> str:
    """Runs all tests of the repository with pytest and returns the output (only the end of long outputs)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "--color=no", "-p", "no:cacheprovider"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=180,
    )
    output = result.stdout + result.stderr
    # Long outputs would fill the context (see the context engineering lesson)
    return output if len(output) <= 3000 else "[... beginning of the output removed ...]\n" + output[-3000:]


TOOLS = {"list_files": list_files, "read_file": read_file, "search_code": search_code, "edit_file": edit_file, "run_tests": run_tests}


def _declaration(name: str, description: str, parameters: dict[str, str], required: list[str]) -> dict:
    properties = {parameter: {"type": "string", "description": text} for parameter, text in parameters.items()}
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {"type": "object", "properties": properties, "required": required}}}


TOOL_DECLARATIONS = [
    _declaration("list_files", "Lists all files of the repository or of one of its directories.",
                 {"directory": "A directory relative to the repository root, e.g. 'roomie/services'. Default: the whole repository."}, []),
    _declaration("read_file", "Returns the content of a file of the repository.",
                 {"path": "The path relative to the repository root, e.g. 'roomie/models.py'."}, ["path"]),
    _declaration("search_code", "Searches all files of the repository for a text and returns the matching lines as 'path:line: content'.",
                 {"text": "The exact text to search for, e.g. a function name or an error code."}, ["text"]),
    _declaration("edit_file", "Replaces a piece of text in a file. To add code, use the lines next to the new code as old_text and repeat them in new_text.",
                 {"path": "The path relative to the repository root.",
                  "old_text": "The exact text to replace. It must occur exactly once in the file.",
                  "new_text": "The text that replaces old_text."}, ["path", "old_text", "new_text"]),
    _declaration("run_tests", "Runs all tests of the repository with pytest and returns the output.", {}, []),
]


# --- Checking the result ------------------------------------------------------------


def count_tests() -> int:
    """The number of tests pytest finds in the workspace."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=WORKSPACE, capture_output=True, text=True, timeout=180,
    )
    return sum(1 for line in result.stdout.splitlines() if "::" in line)


def show_diff() -> None:
    """Prints the changes of the agent: the differences between the workspace and the original code base."""
    changed = False
    for file in _workspace_files():
        relative = file.relative_to(WORKSPACE)
        original = CODEBASE_PATH / relative
        before = original.read_text().splitlines(keepends=True) if original.exists() else []
        diff = "".join(difflib.unified_diff(before, file.read_text().splitlines(keepends=True), f"a/{relative}", f"b/{relative}"))
        if diff:
            changed = True
            print(diff)
    if not changed:
        print("No changes.")


# --- The agent loop -------------------------------------------------------------------------


def _short(text: str, length: int = 100) -> str:
    text = str(text).replace("\n", " ")
    return text if len(text) <= length else text[:length] + " ..."


def run_agent(
    system_prompt: str,
    task: str,
    model: str,
    approve: Callable[[str, dict], bool] | None = None,
    max_steps: int = 30,
) -> str:
    """Works on a task with the tools until the model answers with text (or max_steps is reached).

    It's the tool loop of the function calling lesson - with a goal instead of a question, more steps,
    and an optional approval function that is asked before every tool call.

    Parameters
    ----------
    system_prompt : str
        Instructions for the agent (incl. the project instructions)
    task : str
        The task for the agent
    model : str
        The LiteLLM model name
    approve : Callable[[str, dict], bool] | None
        Called with the tool name and the arguments before a tool runs. If it returns False, the tool
        doesn't run and the model is told so.
    max_steps : int
        Maximum number of model calls

    Returns
    -------
    str
        The final answer of the agent
    """
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": task}]
    for step in range(1, max_steps + 1):
        response = call_with_retry(completion, model=model, messages=messages, tools=TOOL_DECLARATIONS, temperature=0.0)
        message = response.choices[0].message
        messages.append(message.model_dump())
        if not message.tool_calls:
            print(f"[step {step}] done")
            return message.content or ""
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = None
            print(f"[step {step}] {name}({_short(tool_call.function.arguments, 90)})")
            if name not in TOOLS:
                result = f"Error: unknown tool '{name}'. Available tools: {list(TOOLS)}"
            elif arguments is None:
                result = "Error: the arguments are not valid JSON."
            elif approve is not None and not approve(name, arguments):
                result = "The developer did not approve this action. Don't try it again; find another way or explain the problem."
                print("           ✋ not approved")
            else:
                try:
                    result = str(TOOLS[name](**arguments))
                except Exception as error:
                    result = f"Error while executing {name}: {type(error).__name__}: {error}"
            print(f"           -> {_short(result)}")
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
    return "The agent did not finish the task within the allowed number of steps."


# --- Finding code: a repository map --------------------------------------------------------------


def repo_map() -> str:
    """A compact overview of the Python code: classes and function signatures per file, without bodies."""
    lines = []
    for file in _workspace_files():
        if file.suffix != ".py":
            continue
        tree = ast.parse(file.read_text())
        entries = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                entries.append(f"  def {node.name}({ast.unparse(node.args)})")
            elif isinstance(node, ast.ClassDef):
                entries.append(f"  class {node.name}")
                entries += [f"    def {n.name}({ast.unparse(n.args)})" for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if entries:
            lines.append(str(file.relative_to(WORKSPACE)))
            lines += entries
    return "\n".join(lines)


# --- Google ADK -------------------------------------------------------------------------------------


def quiet_adk() -> None:
    """Hides the warnings and log messages of Google ADK and LiteLLM that are not relevant for the lesson."""
    warnings.filterwarnings("ignore")
    for name in ("google_adk", "google.adk", "LiteLLM", "litellm", "httpx"):
        logging.getLogger(name).setLevel(logging.ERROR)


def adk_approval_callback(approve: Callable[[str, dict], bool]):
    """Turns an approval function into a `before_tool_callback` for Google ADK.

    ADK calls the callback before every tool call. If it returns a dict, ADK doesn't run the tool and
    uses the dict as the result instead; if it returns None, the tool runs.
    """
    def before_tool_callback(tool, args, tool_context):
        print(f"[tool] {tool.name}({_short(json.dumps(args), 90)})")
        if not approve(tool.name, args):
            print("           ✋ not approved")
            return {"result": "The developer did not approve this action. Don't try it again; find another way or explain the problem."}
        return None

    return before_tool_callback


async def run_adk_agent(agent, task: str) -> str:
    """Runs a Google ADK agent with a task in a new session and returns its final answer."""
    from google.adk.runners import InMemoryRunner

    runner = InMemoryRunner(agent=agent, app_name="diy-copilot")
    events = await runner.run_debug(task, quiet=True)
    final = [event for event in events if event.is_final_response() and event.content and event.content.parts]
    return "".join(part.text or "" for part in final[-1].content.parts) if final else ""


# --- Independent checks of the agent's work ------------------------------------------------------

_LOG_CHECK = '''
import logging
from datetime import datetime, timezone
from roomie.models import Booking
from roomie.notifications import Notifier

records = []
handler = logging.Handler()
handler.emit = lambda record: records.append(record.getMessage())
logging.getLogger("roomie").addHandler(handler)
logging.getLogger("roomie").setLevel(logging.DEBUG)

now = datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc)
booking = Booking(booking_id="bk_1", room_id="A1-02", owner_id="u_123", title="Performance review with Anna",
                  start=now, end=now, attendees=2, created_at=now)
notifier = Notifier()
notifier.booking_confirmed(booking)
notifier.booking_cancelled(booking)
notifier.rooms_released([booking])
print("LOGGED" if any("Performance review" in r for r in records) else "NOT_LOGGED")
print("SENT" if any("Performance review" in m for m in notifier.sent) else "NOT_SENT")
'''


def check_meeting_titles_not_logged() -> None:
    """Checks the notifications of the workspace: titles must still be sent, but not logged (SEC-04)."""
    result = subprocess.run([sys.executable, "-c", _LOG_CHECK], cwd=WORKSPACE, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"❌ The check failed:\n{result.stderr[-1000:]}")
        return
    print(f"{'✅' if 'NOT_LOGGED' in result.stdout else '❌'} Meeting titles are not logged")
    print(f"{'✅' if 'SENT' in result.stdout.split() else '❌'} Notifications still contain the title")
