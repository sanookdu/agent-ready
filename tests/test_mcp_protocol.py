import json
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent_ready.contracts import validate_assessment


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_real_stdio_server_exposes_only_text_assessment():
    params = StdioServerParameters(command=sys.executable, args=["-m", "agent_ready.mcp_server"])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            init = await session.initialize()
            assert init.capabilities.resources is None
            assert init.capabilities.prompts is None
            tools = (await session.list_tools()).tools
            assert [tool.name for tool in tools] == ["assess_work_unit"]
            schema = tools[0].inputSchema
            assert set(schema["properties"]) == {"text", "provider"}
            assert schema["additionalProperties"] is False
            for args in (
                {"path": "/not/read", "provider": "codex"},
                {"text": "", "provider": "codex"},
                {"text": 123, "provider": "codex"},
                {"text": "Task", "provider": "other"},
                {"text": "Task", "provider": "codex", "command": "echo nope"},
            ):
                result = await session.call_tool("assess_work_unit", args)
                assert result.isError
                assert result.structuredContent is None
            assert (await session.call_tool("read_file", {"path": "/not/read"})).isError


@pytest.mark.anyio
@pytest.mark.parametrize("case", ["ready", "clarify", "split", "hold", "malformed", "failure"])
async def test_stdio_full_engine_and_provider_boundary(case):
    helper = Path(__file__).parent / "helpers" / "fake_host.py"
    params = StdioServerParameters(command=sys.executable, args=[str(helper), "mcp", case])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            for provider in ("codex", "claude"):
                # A path-like string is treated literally; no source loader runs.
                result = await session.call_tool(
                    "assess_work_unit", {"text": "/not/read/task.md", "provider": provider}
                )
                if case in ("malformed", "failure"):
                    assert result.isError
                    assert result.structuredContent is None
                    assert "private-canary" not in str(result)
                else:
                    assert not result.isError
                    assessment = validate_assessment(result.structuredContent)
                    assert assessment["disposition"] == case.upper()
                    assert json.loads(result.content[0].text) == assessment
