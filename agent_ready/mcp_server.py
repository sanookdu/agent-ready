"""One local stdio analytical tool. No source loaders or execution tools."""

import asyncio
from typing import Literal

from jsonschema import Draft202012Validator
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool, ToolAnnotations

from .contracts import SCHEMA
from .engine import MAX_TEXT_CHARS, default_engine

INPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["text", "provider"],
    "properties": {
        "text": {
            "type": "string",
            "minLength": 1,
            "maxLength": MAX_TEXT_CHARS,
            "pattern": r"\S",
            "description": "Actual task text, never a file or URL to read.",
        },
        "provider": {"type": "string", "enum": ["codex", "claude"]},
    },
}
_TOOL = Tool(
    name="assess_work_unit",
    description="Assess text as READY, CLARIFY, SPLIT or HOLD. Does not execute work. Text is sent to the selected provider.",
    inputSchema=INPUT_SCHEMA,
    outputSchema=SCHEMA,
    annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=False, openWorldHint=True
    ),
)
server = Server("agent-ready")


def assess_work_unit(text: str, provider: Literal["codex", "claude"]) -> dict:
    return default_engine().assess(text, provider)


def mcp_tool_names() -> tuple[str, ...]:
    return (_TOOL.name,)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [_TOOL]


@server.call_tool(validate_input=False)
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    if name != _TOOL.name or not Draft202012Validator(INPUT_SCHEMA).is_valid(arguments):
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text", text="Invalid assessment request; supply text and provider only."
                )
            ],
        )
    try:
        assessment = await asyncio.to_thread(assess_work_unit, **arguments)
    except Exception:
        # Do not serialize provider errors, paths, credentials, or task content.
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text",
                    text="Assessment failed; no disposition produced. Check provider installation, supported version and authentication locally.",
                )
            ],
        )
    import json

    return CallToolResult(
        structuredContent=assessment,
        content=[TextContent(type="text", text=json.dumps(assessment))],
    )


async def _run() -> None:
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
