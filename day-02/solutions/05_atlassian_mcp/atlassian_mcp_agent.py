"""Run an ADK agent against the Atlassian Remote MCP server.

Same agent + MCP pattern as 03_agents.ipynb (Exercise 3), but pointed at the
hosted Atlassian server (https://mcp.atlassian.com/v1/mcp) via the `mcp-remote`
Node proxy. We use a standalone script instead of a notebook because the OAuth
callback that mcp-remote spins up is fragile inside Jupyter's event loop.

Usage:
    uv run python atlassian_mcp_agent.py
    uv run python atlassian_mcp_agent.py "Show me my open Jira issues"

See README.md in this directory for prerequisites and the OAuth flow.
"""

import sys
sys.path.append("../../../")

import asyncio
import logging
import os
import uuid
import warnings

from dotenv import find_dotenv, load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

from lib.validation import validate_environment_for_model

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)

ATLASSIAN_MCP_URL = "https://mcp.atlassian.com/v1/mcp"
USER_ID = "user_1"
APP_NAME = "atlassian_mcp_app"

DEFAULT_PROMPT = (
    "List the Jira projects on my site, then show me the 5 most recently updated issues "
    "across all projects with their key, summary, status and assignee. "
    "Format the result as a markdown table."
)


def build_agent(adk_model: LiteLlm) -> Agent:
    return Agent(
        name="atlassian_mcp_agent",
        model=adk_model,
        description="An agent with read access to a participant's Atlassian Cloud site via the Atlassian Remote MCP server.",
        instruction=(
            "You are an Atlassian assistant. You can search Jira and summarize what you find. "
            "Use the available Atlassian tools to answer the user's questions. "
            "If a tool requires a project key or other identifier the user did not provide, ask for it."
        ),
        tools=[
            McpToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="npx",
                        args=["-y", "mcp-remote", ATLASSIAN_MCP_URL],
                    ),
                )
            )
        ],
    )


async def call_agent_async(query: str, runner: Runner, session_id: str) -> None:
    print(f"\n<<< User Query: {query}")

    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response_text = "Agent did not produce a final response."

    async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=content):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    print(f"\n>>> Tool Call: {part.function_call.name}({part.function_call.args})")
                if part.function_response:
                    response = part.function_response.response
                    if isinstance(response, dict):
                        result_str = str(response.get("result", response))
                    else:
                        result_str = str(response)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    print(f"<<< Tool Result: {result_str}")

        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break

    print(f"\n<<< Agent Response: {final_response_text}")


async def main(prompt: str) -> None:
    load_dotenv(find_dotenv())

    generation_provider = os.getenv("DEFAULT_GENERATION_PROVIDER")
    generation_model_name = os.getenv("DEFAULT_GENERATION_MODEL")
    generation_model = f"{generation_provider}/{generation_model_name}"
    validate_environment_for_model(model=generation_model)

    adk_model = LiteLlm(model=generation_model)
    agent = build_agent(adk_model)

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

    session_id = str(uuid.uuid4())
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)

    await call_agent_async(prompt, runner, session_id)


if __name__ == "__main__":
    user_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_PROMPT
    asyncio.run(main(user_prompt))
