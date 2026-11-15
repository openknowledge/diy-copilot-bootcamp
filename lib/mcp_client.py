"""A small MCP client for the MCP lesson (day-02/solutions/02_mcp).

It hides the technical details of the MCP Python SDK (processes, sessions, async context managers),
so that the notebook can focus on the concepts: discovering and calling tools, resources and prompts.

Every function starts the server, does its work and stops the server again. That's slower than one
long-running connection, but robust in notebooks (sessions that stay open across cells can hang).
"""

import json
import os
import subprocess
import sys
import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import LATEST_PROTOCOL_VERSION


# The servers write their logs (stderr) into this file instead of the notebook output
SERVER_LOG = Path(tempfile.gettempdir()) / "mcp_servers.log"


@dataclass
class McpServer:
    """A local MCP server: a Python script that the client starts as a separate process."""

    name: str
    script: Path
    args: list[str] = field(default_factory=list)

    def parameters(self) -> StdioServerParameters:
        # The server process gets the environment of the notebook (API key, model defaults)
        return StdioServerParameters(command=sys.executable, args=[str(self.script), *self.args], env=dict(os.environ))


@asynccontextmanager
async def connect(server: McpServer):
    """Starts an MCP server and yields an initialized client session."""
    with open(SERVER_LOG, "a") as errlog:
        async with stdio_client(server.parameters(), errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()  # the handshake
                yield session


def _text(result) -> str:
    """The text of an MCP tool result (a list of content blocks)."""
    text = "\n".join(block.text for block in result.content if block.type == "text")
    return f"Error: {text}" if result.isError else text


async def list_tools(server: McpServer) -> list:
    """Asks a server which tools it offers (MCP method tools/list)."""
    async with connect(server) as session:
        return (await session.list_tools()).tools


async def call_tool(server: McpServer, name: str, arguments: dict) -> str:
    """Calls a tool of a server (MCP method tools/call) and returns the text of the result."""
    async with connect(server) as session:
        return _text(await session.call_tool(name, arguments))


def print_tools(tools: list) -> None:
    """Prints name, description and parameters (JSON schema) of tools."""
    for tool in tools:
        print(f"Tool:        {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Parameters:  {json.dumps(tool.inputSchema, indent=2)}\n")


async def list_resources(server: McpServer) -> list:
    """Asks a server which resources it offers (MCP methods resources/list and resources/templates/list).

    A resource has a fixed URI (e.g. 'file:///README.md'); a resource template has placeholders
    (e.g. 'ticket://{ticket_id}') and stands for many resources.
    """
    async with connect(server) as session:
        resources = (await session.list_resources()).resources
        templates = (await session.list_resource_templates()).resourceTemplates
        return list(resources) + list(templates)


async def read_resource(server: McpServer, uri: str) -> str:
    """Reads a resource of a server (MCP method resources/read) and returns its text."""
    async with connect(server) as session:
        result = await session.read_resource(uri)
        return "\n".join(content.text for content in result.contents if hasattr(content, "text"))


async def list_prompts(server: McpServer) -> list:
    """Asks a server which prompts it offers (MCP method prompts/list)."""
    async with connect(server) as session:
        return (await session.list_prompts()).prompts


async def get_prompt(server: McpServer, name: str, arguments: dict) -> list[dict]:
    """Gets a prompt from a server (MCP method prompts/get) and returns it as messages for the model."""
    async with connect(server) as session:
        result = await session.get_prompt(name, arguments)
        return [{"role": message.role, "content": message.content.text} for message in result.messages]


def print_resources(resources: list) -> None:
    """Prints the URI (or URI template) and the description of resources."""
    for resource in resources:
        uri = getattr(resource, "uriTemplate", None) or resource.uri
        print(f"Resource:    {uri}")
        print(f"Description: {resource.description}\n")


def print_prompts(prompts: list) -> None:
    """Prints name, description and arguments of prompts."""
    for prompt in prompts:
        arguments = ", ".join(f"{a.name}{'' if a.required else ' (optional)'}" for a in prompt.arguments or [])
        print(f"Prompt:      {prompt.name}({arguments})")
        print(f"Description: {prompt.description}\n")


def _exchange_by_hand(server: McpServer, steps: list[tuple[str, str, dict | None]]) -> None:
    """Starts a server, does the handshake and sends requests by hand; prints every JSON-RPC message."""
    with open(SERVER_LOG, "a") as errlog:
        process = subprocess.Popen([sys.executable, str(server.script), *server.args],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errlog, text=True, env=dict(os.environ))

        def send(message: dict) -> None:
            print(f">>> client: {json.dumps(message)}")
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()

        def receive() -> dict:
            message = json.loads(process.stdout.readline())
            text = json.dumps(message)
            print(f"<<< server: {text if len(text) <= 700 else text[:700] + ' ...'}\n")
            return message

        try:
            print("# Handshake: the client introduces itself, the server answers with its name and capabilities")
            send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": LATEST_PROTOCOL_VERSION, "capabilities": {},
                             "clientInfo": {"name": "diy-copilot-notebook", "version": "1.0"}}})
            receive()
            send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            print("    (a notification - no answer)\n")
            for request_id, (title, method, params) in enumerate(steps, start=2):
                print(f"# {title}")
                request = {"jsonrpc": "2.0", "id": request_id, "method": method}
                if params is not None:
                    request["params"] = params
                send(request)
                receive()
        finally:
            process.terminate()
            process.wait()


def talk_to_server_by_hand(server: McpServer, tool_name: str, arguments: dict) -> None:
    """Talks to a server without the SDK and prints every JSON-RPC message (one message per line on stdin/stdout)."""
    _exchange_by_hand(server, [
        ("Which tools do you offer?", "tools/list", None),
        ("Call a tool", "tools/call", {"name": tool_name, "arguments": arguments}),
    ])


def show_resource_and_prompt_messages(server: McpServer, uri: str, prompt_name: str, prompt_arguments: dict) -> None:
    """Shows the JSON-RPC messages for reading a resource and getting a prompt."""
    _exchange_by_hand(server, [
        ("Read a resource", "resources/read", {"uri": uri}),
        ("Get a prompt", "prompts/get", {"name": prompt_name, "arguments": prompt_arguments}),
    ])


def read_server_log(last_characters: int = 1500) -> str:
    """The end of the servers' log file (what the servers wrote to stderr)."""
    return SERVER_LOG.read_text()[-last_characters:] if SERVER_LOG.exists() else ""
