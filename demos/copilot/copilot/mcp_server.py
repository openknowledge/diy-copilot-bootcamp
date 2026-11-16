"""MCP server that offers the search over the company knowledge base as a tool (level 4).

The same retrieval as in the ``roomie-rag`` model – but now the *client* decides when
to search: Claude Code (or any other MCP client) discovers the tool and calls it
whenever it needs a company rule.

Transport: Streamable HTTP on http://<host>:8100/mcp, so that it can run in its own
container and be shared by many clients (and registered in a gateway, level 5).

Run locally:  uv run --env-file ../.env python -m copilot.mcp_server
"""

import logging
import os
import threading

from mcp.server.fastmcp import FastMCP

from copilot.knowledge_base import format_results, index

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("copilot.mcp")

mcp = FastMCP(
    "company-knowledge-base",
    instructions="Search the internal knowledge base of the company before you apply or assume company rules.",
    # In Docker the server must listen on all interfaces; locally only on localhost
    # (FastMCP then also enables its DNS rebinding protection).
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8100")),
    # No session state needed: every tool call is independent. Works best behind a gateway.
    stateless_http=True,
    log_level="WARNING",
)


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Searches the company's internal knowledge base and returns the most relevant sections.

    The knowledge base contains business policies (e.g. meeting room booking in Berlin and
    Munich, desk sharing, parking), engineering guidelines (Python coding, API design,
    testing, git and code review) and security requirements (secrets, logging, data
    protection, use of AI assistants). Only current documents are searched. Use it whenever
    a question or a code change depends on internal rules or conventions of the company.
    Rules have ids like API-07, PY-03, TEST-07, SEC-04 or DP-01.

    Args:
        query: What to search for, phrased like the wording of a policy or guideline.
    """
    results = index.search(query)
    # Shown in `docker compose logs -f mcp` - nice to watch during the demo
    logger.info("search_knowledge_base(%r) -> %s", query, ", ".join(r.chunk.location for r in results))
    return format_results(results)


def _build_index() -> None:
    try:
        index.build()
    except Exception as error:  # noqa: BLE001
        logger.error("building the index failed: %s", type(error).__name__)


if __name__ == "__main__":
    threading.Thread(target=_build_index, daemon=True).start()
    mcp.run(transport="streamable-http")
