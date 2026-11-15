"""MCP server that offers the search over the company knowledge base as a tool.

It is the same function as in the function calling lesson - now in its own process, so that
any MCP client (our notebook, Claude Code, VS Code, ...) can discover and call it.
"""

import sys
from pathlib import Path

# Make the shared code of the workshop (lib) importable - the repository root is 3 folders up
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from lib.knowledge_base import search  # noqa: E402

mcp = FastMCP("company-knowledge-base", log_level="WARNING")


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Searches the company's internal knowledge base and returns the most relevant sections.

    The knowledge base contains business policies (e.g. meeting room booking in Berlin and
    Munich, desk sharing, parking), engineering guidelines (Python coding, API design,
    testing, git and code review) and security requirements (secrets, logging, data
    protection, use of AI assistants). Only current documents are searched. Use it whenever
    a question depends on internal rules or conventions of the company.

    Args:
        query: What to search for, phrased like the wording of a policy or guideline.
    """
    # Logs go to stderr: stdout is reserved for the messages of the MCP protocol
    print(f"search_knowledge_base({query!r})", file=sys.stderr)
    return search(query)


if __name__ == "__main__":
    mcp.run()
