"""MCP server for the issue tracker of Team Workplace (read-only).

A second, independent server next to the knowledge base: with it, Claude Code can read a
ticket itself instead of the developer pasting it. In level 5 both servers are registered
in the gateway, and the key of a team decides which of them it gets.

Transport: Streamable HTTP on http://<host>:8101/mcp

Run locally:  uv run python -m copilot.tickets_mcp_server
"""

import json
import logging
import os

from mcp.server.fastmcp import FastMCP

from copilot import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("copilot.tickets")

mcp = FastMCP(
    "issue-tracker",
    instructions="Read-only access to the tickets of Team Workplace (ids like WORK-412).",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8101")),
    stateless_http=True,
    log_level="WARNING",
)


def _load_tickets() -> list[dict]:
    # Read on every call, so changes to the export are visible without a restart
    return json.loads(settings.TICKETS_PATH.read_text(encoding="utf-8"))


@mcp.tool()
def list_tickets(status: str | None = None, component: str | None = None) -> str:
    """Lists the tickets of Team Workplace (the team that owns Roomie), one line per ticket.

    Args:
        status: Optional filter, e.g. "open", "in progress", "done" or "rejected".
        component: Optional filter, e.g. "api", "availability", "bookings", "notifications".
    """
    tickets = [
        t for t in _load_tickets()
        if (status is None or t["status"] == status.lower()) and (component is None or t["component"] == component.lower())
    ]
    logger.info("list_tickets(status=%r, component=%r) -> %d ticket(s)", status, component, len(tickets))
    if not tickets:
        return "No tickets found."
    return "\n".join(f"{t['id']} [{t['status']}] {t['type']}, {t['component']}: {t['title']}" for t in tickets)


@mcp.tool()
def get_ticket(ticket_id: str) -> str:
    """Returns a ticket with all details (description, workaround or resolution, assignee) as JSON.

    Args:
        ticket_id: The id of the ticket, e.g. "WORK-412".
    """
    ticket = next((t for t in _load_tickets() if t["id"].lower() == ticket_id.strip().lower()), None)
    logger.info("get_ticket(%r) -> %s", ticket_id, "found" if ticket else "not found")
    if ticket is None:
        return f"Ticket {ticket_id} does not exist."
    return json.dumps(ticket, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
