"""Credential-free, loopback-only contract check for unreviewed Claude Code versions.

This verifies observed behavior, not the integrity of a malicious provider binary.
No task text, user authentication, external endpoint or real inference is used.
"""

import json
import re
import shlex
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from .providers import _invalid_constant, _unique_object

_REQUIRED_HELP = (
    "--print",
    "--output-format",
    "--tools",
    "--safe-mode",
    "--strict-mcp-config",
    "--mcp-config",
    "--setting-sources",
    "--disable-slash-commands",
    "--no-chrome",
    "--no-session-persistence",
    "--permission-mode",
    "--system-prompt",
)
_CANARIES = (
    "PRIVATE_INSTRUCTION_CANARY",
    "PRIVATE_SKILL_CANARY",
    "PROJECT_INSTRUCTION_CANARY",
    "PRIVATE_AGENT_CANARY",
    "PRIVATE_COMMAND_CANARY",
    "PRIVATE_STYLE_CANARY",
)
# Top-level Messages request keys that can attach tools other than `tools` itself.
_TOOL_CHANNEL_KEYS = ("mcp_servers", "container")
_PROBE_TEXT = "Agent Ready capability probe. Return only the synthetic JSON response."
_RESPONSE_TEXT = '{"probe":"agent-ready"}'
# Never a real credential: the probe endpoint is loopback and accepts any key.
_PROBE_KEY = "agent-ready-probe-not-a-credential"
_CREDENTIALS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")


def _messages_path(path):
    return path == "/v1/messages" or path.startswith("/v1/messages?")


def _tripwire(path):
    """A local command that records that it ran. Hooks and MCP servers never reach the wire."""
    return [sys.executable, "-c", f"open({str(path)!r}, 'w').close()"]


def _seed_customizations(root, sentinels, label):
    """Seed every local customization class Claude Code reads from a config root."""
    claude = root / ".claude"
    for sub in ("skills/private", "agents", "commands", "output-styles"):
        (claude / sub).mkdir(parents=True, exist_ok=True, mode=0o700)
    (claude / "skills" / "private" / "SKILL.md").write_text(
        "---\nname: private\ndescription: PRIVATE_SKILL_CANARY\n---\nprivate"
    )
    (claude / "agents" / "private.md").write_text(
        "---\nname: private\ndescription: PRIVATE_AGENT_CANARY\n---\nPRIVATE_AGENT_CANARY"
    )
    (claude / "commands" / "private.md").write_text("PRIVATE_COMMAND_CANARY")
    (claude / "output-styles" / "private.md").write_text(
        "---\nname: private\ndescription: PRIVATE_STYLE_CANARY\n---\nPRIVATE_STYLE_CANARY"
    )
    hook = {"type": "command", "command": shlex.join(_tripwire(sentinels / f"{label}-hook"))}
    (claude / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    event: [{"hooks": [hook]}]
                    for event in ("UserPromptSubmit", "SessionStart", "Stop")
                },
                "outputStyle": "private",
            }
        )
    )
    command = _tripwire(sentinels / f"{label}-mcp")
    return {"mcpServers": {"private": {"command": command[0], "args": command[1:]}}}


def probe_claude(adapter, assessment_options):
    # Independent probe homes never receive the assessment credential.
    with TemporaryDirectory(prefix="agent-ready-contract-") as directory:
        runtime = Path(directory)
        sentinels = runtime / "sentinels"
        sentinels.mkdir()
        env = {
            k: v
            for k, v in assessment_options["env"].items()
            if k not in (*_CREDENTIALS, "ANTHROPIC_BASE_URL", "HOME", "USERPROFILE")
        }
        # Seed an untrusted original home, then exercise the same isolation helper as the
        # assessment. Nothing seeded there may reach the wire or execute.
        from .providers import isolated_claude_environment

        origin = runtime / "origin"
        mcp = _seed_customizations(origin, sentinels, "home")
        (origin / ".claude" / "CLAUDE.md").write_text(_CANARIES[0])
        (origin / ".claude.json").write_text(json.dumps(mcp))
        env["HOME"] = str(origin)
        env = isolated_claude_environment(env, runtime, copy_auth=False)
        # Project-level customizations the adapter's flags must exclude, since the working
        # directory is not isolated by a home change.
        cwd = runtime / "work"
        mcp = _seed_customizations(cwd, sentinels, "project")
        (cwd / "CLAUDE.md").write_text(_CANARIES[2])
        (cwd / ".mcp.json").write_text(json.dumps(mcp))
        env["ANTHROPIC_API_KEY"] = _PROBE_KEY
        options = {**assessment_options, "env": env, "cwd": cwd}
        help_result = adapter.runner([adapter.executable, "--help"], timeout=10, **options)
        if help_result.returncode or not all(
            re.search(r"(?<![\w-])" + re.escape(flag) + r"(?![\w-])", help_result.stdout)
            for flag in _REQUIRED_HELP
        ):
            raise ValueError("Required CLI controls missing")
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup()
                self.connection.settimeout(5)

            def _refuse(self):
                requests.append(None)  # outside the reviewed contract: never certified
                self.send_error(405)

            do_GET = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _refuse

            def do_HEAD(self):
                # Observed from the real CLI: a body-less connectivity check. Nothing else.
                if self.path != "/api/hello":
                    self._refuse()
                    return
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_POST(self):
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 1_000_000 or not _messages_path(self.path):
                        raise ValueError("Invalid probe request")
                    # The same strict decoding as assessment output: a duplicate "tools" key
                    # or a non-JSON constant is an ambiguous wire request, never certified.
                    payload = json.loads(
                        self.rfile.read(length),
                        object_pairs_hook=_unique_object,
                        parse_constant=_invalid_constant,
                    )
                    if not isinstance(payload, dict):
                        raise ValueError("Invalid probe request")
                    requests.append(payload)
                except (ValueError, OSError, RecursionError):
                    requests.append(None)
                    self.send_error(400)
                    return
                message = {
                    "id": "msg_probe",
                    "type": "message",
                    "role": "assistant",
                    "model": payload.get("model"),
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                }
                if payload.get("stream"):
                    events = [
                        ("message_start", {"type": "message_start", "message": message}),
                        (
                            "content_block_start",
                            {
                                "type": "content_block_start",
                                "index": 0,
                                "content_block": {"type": "text", "text": ""},
                            },
                        ),
                        (
                            "content_block_delta",
                            {
                                "type": "content_block_delta",
                                "index": 0,
                                "delta": {"type": "text_delta", "text": _RESPONSE_TEXT},
                            },
                        ),
                        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
                        (
                            "message_delta",
                            {
                                "type": "message_delta",
                                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                                "usage": {"output_tokens": 0},
                            },
                        ),
                        ("message_stop", {"type": "message_stop"}),
                    ]
                    body = "".join(
                        f"event: {name}\ndata: {json.dumps(data)}\n\n" for name, data in events
                    ).encode()
                    content_type = "text/event-stream"
                else:
                    message.update(
                        content=[{"type": "text", "text": _RESPONSE_TEXT}], stop_reason="end_turn"
                    )
                    body = json.dumps(message).encode()
                    content_type = "application/json"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        # Joined on close, so a request still being read when the CLI exits is inspected too.
        server.daemon_threads = False
        server.block_on_close = True
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        try:
            env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"
            result = adapter.runner(
                adapter.command(runtime), input=_PROBE_TEXT, timeout=60, **options
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        if result.returncode or not requests or not all(isinstance(r, dict) for r in requests):
            raise ValueError("Probe request/response failed")
        if any(sentinels.iterdir()):
            raise ValueError("A local hook or MCP server executed")
        # Every request the CLI makes must be tool-less, not merely the one carrying the task.
        if any(
            request.get("tools") != [] or any(key in request for key in _TOOL_CHANNEL_KEYS)
            for request in requests
        ):
            raise ValueError("Text-only tool contract failed")
        wire = json.dumps(requests)
        if _PROBE_TEXT not in wire or any(canary in wire for canary in _CANARIES):
            raise ValueError("Instruction isolation failed")
        if json.loads(
            result.stdout, object_pairs_hook=_unique_object, parse_constant=_invalid_constant
        ) != {"probe": "agent-ready"}:
            raise ValueError("JSON stdout contract failed")
