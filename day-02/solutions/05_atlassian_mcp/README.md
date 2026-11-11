# Atlassian Remote MCP 
In `03_agents.ipynb` Exercise 3 we already pointed an ADK agent at a **local**
stdio MCP server (`bookstore_mcp_server.py`). The same client pattern works
unchanged against a **hosted, third-party** MCP server. To make that point we
take a guided tour: one MCP server, three different clients, no tool code
written along the way. Only the final step is code in this repository.

## Read the Atlassian Remote MCP docs (browser)

Open <https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/>
and look at the things that matter to us as MCP **clients**:

- **Endpoint:** `https://mcp.atlassian.com/v1/mcp` (HTTP, not stdio).
- **Auth:** OAuth 2.1 with browser-based consent — no API token to copy
  around, no app to register.
- **What it exposes:** Jira (search/create/update issues), Confluence
  (summarize/create/query pages), Compass (components, dependencies),
  cross-product linking. The exact tool *names* are not in the docs — we
  discover those next.

The takeaway: this is just an MCP server. Anything that speaks MCP can talk to
it.

## Inspect the server with MCP Inspector (no agent yet)

Before plugging it into any LLM, we look at it through
[MCP Inspector](https://github.com/modelcontextprotocol/inspector) — the
"Postman for MCP servers". Inspector lets us see exactly which tools a server
advertises and call them by hand.

```bash
npx @modelcontextprotocol/inspector npx -y mcp-remote https://mcp.atlassian.com/v1/mcp
```

The first run pops a browser for the Atlassian OAuth flow. After approval, Inspector's UI shows:

- the **list of tools** the server actually exposes, with their JSON schemas
  (`getJiraIssue`, `searchJiraIssues`, `getConfluencePage`, …),
- a form per tool where we can fill in arguments and **invoke the tool
  directly**, no LLM in the loop,
- the raw JSON request/response so we can see what an agent would see.


## Wire the same server into Claude Code

To show that the protocol is the contract, we connect the exact same server to
a general-purpose CLI client — Claude Code:

```bash
claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp
```

Then in a `claude` session, ask: *"List my open Jira issues."* Claude
discovers the same tools Inspector showed us, picks one, calls it, and
summarizes the result. We have not written a single line of code.

## Connect our ADK agent (the code in this repo)

Finally we plug the same server into our own agent built with Google ADK. This
is the only step that lives in this repository:

```bash
uv run python atlassian_mcp_agent.py
```

The script (`atlassian_mcp_agent.py`) is intentionally short — it reuses the
exact `Agent` + `McpToolset(StdioConnectionParams(...))` pattern from
`03_agents.ipynb` Exercise 3, with two differences:

1. It runs as a standalone process (`asyncio.run(main())`) instead of in
   Jupyter — the OAuth callback that `mcp-remote` listens for tends to die
   mid-handshake inside the notebook event loop.
2. The MCP server it spawns is `npx -y mcp-remote https://mcp.atlassian.com/v1/mcp`
   instead of our local `bookstore_mcp_server.py`.

You can pass your own prompt:

```bash
uv run python atlassian_mcp_agent.py "Summarize the open issues assigned to me in project XYZ"
```

The agent's `>>> Tool Call:` lines will reference the same Atlassian tool
names you saw in Inspector — that's the whole point.

## Why the proxy?

`mcp-remote` shows up in two of the previous steps — Inspector and our ADK
script. Claude Code is the exception: it speaks Streamable HTTP and runs the
OAuth 2.1 dance natively, so it connects to `https://mcp.atlassian.com/v1/mcp`
directly. It is worth understanding why the other two clients can't.

There are two mismatches between the Atlassian server and most MCP clients:

**Transport.** Atlassian publishes two endpoints:

- `https://mcp.atlassian.com/v1/mcp` — Streamable HTTP (current).
- `https://mcp.atlassian.com/v1/sse` — SSE (legacy, deprecated after
  2026-06-30).

Google ADK's `McpToolset` ships `StdioConnectionParams` and
`SseConnectionParams`, but no Streamable-HTTP client. So purely on transport,
you *could* point ADK at the SSE endpoint via `SseConnectionParams` until
mid-2026. After the SSE sunset, ADK has no way to reach Atlassian directly.

**Auth — the real blocker.** Atlassian requires OAuth 2.1 with dynamic client
registration. Even when a client speaks HTTP, it has to:

1. Hit the server's discovery endpoint.
2. Register itself dynamically as an OAuth client.
3. Spin up a localhost listener for the redirect.
4. Open a browser, walk the user through Atlassian consent, exchange the code
   for tokens.
5. Persist and refresh those tokens on subsequent runs.

`SseConnectionParams` only takes a static `headers` dict. It has no helper for
any of this. To use it directly you would have to build the OAuth dance
yourself.

**What `mcp-remote` actually does.** A small Node program that:

- runs as a stdio MCP server (so any stdio-capable client can spawn it),
- speaks Streamable HTTP to the real server underneath,
- implements the full OAuth 2.1 dance once, including the browser callback
  and token caching under `~/.mcp-auth/`.

In short: if your client already speaks Streamable HTTP and OAuth 2.1
natively (Claude Code does), you don't need the proxy. For everything else —
Inspector, ADK, and most of the ecosystem today — `mcp-remote` is the easy
way to avoid building that plumbing yourself.

## Prerequisites for the last step


- An **Atlassian Cloud** site with Jira access (free account is fine —
  <https://www.atlassian.com/try/cloud/signup>).
- **Node.js v18+** on your `PATH` (`node --version`).
- A local browser for the one-time OAuth consent. Tokens are cached under
  `~/.mcp-auth/`, so it only happens once per machine.
- The workshop's Python environment (`uv sync` at the repo root) — no extra
  Python packages needed.

## Troubleshooting

- `npx: command not found` → install Node.js v18+ and re-open the shell.
