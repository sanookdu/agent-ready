"""Credential-free, loopback-only contract check for unreviewed Claude Code versions.

This verifies observed behavior, not the integrity of a malicious provider binary.
No task text, user authentication, external endpoint or real inference is used.
"""

import json
import re
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
_CANARIES = ("PRIVATE_INSTRUCTION_CANARY", "PRIVATE_SKILL_CANARY", "PROJECT_INSTRUCTION_CANARY")
_PROBE_TEXT = "Agent Ready capability probe. Return only the synthetic JSON response."
_RESPONSE_TEXT = '{"probe":"agent-ready"}'
# Never a real credential: the probe endpoint is loopback and accepts any key.
_PROBE_KEY = "agent-ready-probe-not-a-credential"
_CREDENTIALS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")


def _messages_path(path):
    return path == "/v1/messages" or path.startswith("/v1/messages?")


def probe_claude(adapter, assessment_options):
    # Independent probe homes never receive the assessment credential.
    with TemporaryDirectory(prefix="agent-ready-contract-") as directory:
        runtime = Path(directory)
        env = {
            k: v
            for k, v in assessment_options["env"].items()
            if k not in (*_CREDENTIALS, "ANTHROPIC_BASE_URL", "HOME", "USERPROFILE")
        }
        # Seed user and project instructions the selected flags must keep out of the request.
        home = runtime / "home"
        skill = home / ".claude" / "skills" / "private"
        skill.mkdir(parents=True, mode=0o700)
        (home / ".claude" / "CLAUDE.md").write_text(_CANARIES[0])
        (skill / "SKILL.md").write_text(
            "---\nname: private\ndescription: PRIVATE_SKILL_CANARY\n---\nprivate"
        )
        cwd = runtime / "work"
        cwd.mkdir()
        (cwd / "CLAUDE.md").write_text(_CANARIES[2])
        env.update(HOME=str(home), USERPROFILE=str(home), ANTHROPIC_API_KEY=_PROBE_KEY)
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

            def do_GET(self):
                requests.append(None)  # no read-side traffic is part of the reviewed contract
                self.send_error(404)

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
        server.daemon_threads = True
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
        # Every request the CLI makes must be tool-less, not merely the one carrying the task.
        if any(request.get("tools") != [] for request in requests):
            raise ValueError("Text-only tool contract failed")
        wire = json.dumps(requests)
        if _PROBE_TEXT not in wire or any(canary in wire for canary in _CANARIES):
            raise ValueError("Instruction isolation failed")
        if json.loads(
            result.stdout, object_pairs_hook=_unique_object, parse_constant=_invalid_constant
        ) != {"probe": "agent-ready"}:
            raise ValueError("JSON stdout contract failed")
