"""MCP server that exposes bookstore tools (read_book_database, order_book).

Run with:
    python bookstore_mcp_server.py

This server communicates over stdio and is meant to be launched by an
ADK agent via StdioConnectionParams.
"""

import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Resolve the path to the book database
# When launched from the notebook directory, we go up to the repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BOOK_DB = REPO_ROOT / "data" / "processed" / "gutenberg" / "books.db"

mcp = FastMCP("bookstore")


@mcp.tool()
def read_book_database() -> str:
    """Get information about all books of the bookstore including titles, authors, and ISBN numbers.

    Returns:
        The content of the book database as a JSON string.
    """
    print("<<< MCP Tool Call: read_book_database", file=sys.stderr)
    return BOOK_DB.read_text(encoding="utf-8")


@mcp.tool()
def order_book(isbn: str) -> str:
    """Order a book from the bookstore by its ISBN number.

    Args:
        isbn: The ISBN of the book to order (e.g., '978-3-51593-12345-6').

    Returns:
        A status message about the order.
    """
    print(f"<<< MCP Tool Call: order_book({isbn})", file=sys.stderr)
    with open(BOOK_DB, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        if item.get("metadata", {}).get("isbn") == isbn:
            title = item["metadata"]["title"]
            return f"Success: You ordered '{title}'!"

    return f"Error: No book found with ISBN {isbn}."


if __name__ == "__main__":
    mcp.run()
