"""Credential-free, loopback-only contract check for unreviewed Codex versions.

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
    "--sandbox",
    "read-only",
    "--ignore-user-config",
    "--ignore-rules",
    "--ephemeral",
    "--skip-git-repo-check",
    "--color",
    "--config",
)
_CANARIES = ("PRIVATE_INSTRUCTION_CANARY", "PRIVATE_SKILL_CANARY")
_PROBE_TEXT = "Agent Ready capability probe. Return only the synthetic JSON response."
_RESPONSE_TEXT = '{"probe":"agent-ready"}'


def probe_codex(adapter, assessment_options):
    # Independent probe homes never receive even the copied assessment credential.
    with TemporaryDirectory(prefix="agent-ready-contract-") as directory:
        runtime = Path(directory)
        env = {
            k: v
            for k, v in assessment_options["env"].items()
            if k not in ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_HOME", "HOME", "USERPROFILE")
        }
        # Seed an untrusted original home, then exercise the same isolation helper
        # as assessment. The selected homes/cwd must remain empty of instructions.
        from .providers import isolated_codex_environment

        origin = runtime / "origin"
        origin.mkdir()
        original_codex = origin / ".codex"
        original_codex.mkdir()
        (original_codex / "AGENTS.md").write_text(_CANARIES[0])
        skill = origin / ".agents" / "skills" / "private"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: private\ndescription: PRIVATE_SKILL_CANARY\n---\nprivate"
        )
        env.update(HOME=str(origin), USERPROFILE=str(origin), CODEX_HOME=str(original_codex))
        env = isolated_codex_environment(env, runtime, copy_auth=False)
        cwd = runtime / "work"
        cwd.mkdir()
        options = {**assessment_options, "env": env, "cwd": cwd}
        help_result = adapter.runner([adapter.executable, "exec", "--help"], timeout=10, **options)
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

            def do_POST(self):
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 1_000_000 or self.path != "/v1/responses":
                        raise ValueError("Invalid probe request")
                    # The same strict decoding as assessment output: a duplicate "tools" key
                    # or a non-JSON constant is an ambiguous wire request, never certified.
                    payload = json.loads(
                        self.rfile.read(length),
                        object_pairs_hook=_unique_object,
                        parse_constant=_invalid_constant,
                    )
                    requests.append(payload)
                except (ValueError, OSError, RecursionError):
                    requests.append(None)
                    self.send_error(400)
                    return
                item = {
                    "id": "msg_probe",
                    "type": "message",
                    "status": "completed",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": _RESPONSE_TEXT, "annotations": []}],
                }
                response = {
                    "id": "resp_probe",
                    "object": "response",
                    "status": "completed",
                    "model": "gpt-5.5",
                    "output": [item],
                    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                }
                events = [
                    {
                        "type": "response.created",
                        "response": {**response, "status": "in_progress", "output": []},
                    },
                    {
                        "type": "response.output_item.added",
                        "output_index": 0,
                        "item": {**item, "status": "in_progress", "content": []},
                    },
                    {
                        "type": "response.output_text.delta",
                        "item_id": "msg_probe",
                        "output_index": 0,
                        "content_index": 0,
                        "delta": _RESPONSE_TEXT,
                    },
                    {"type": "response.output_item.done", "output_index": 0, "item": item},
                    {"type": "response.completed", "response": response},
                ]
                body = "".join("data: " + json.dumps(e) + "\n\n" for e in events).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
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
            args = adapter.command(runtime)[:-1]
            settings = {
                "model_provider": '"agent_ready_probe"',
                "model_providers.agent_ready_probe.name": '"agent_ready_probe"',
                "model_providers.agent_ready_probe.base_url": json.dumps(
                    f"http://127.0.0.1:{server.server_port}/v1"
                ),
                "model_providers.agent_ready_probe.wire_api": '"responses"',
                "model_providers.agent_ready_probe.requires_openai_auth": "false",
                "model_providers.agent_ready_probe.request_max_retries": "0",
                "model_providers.agent_ready_probe.stream_max_retries": "0",
            }
            for key, value in settings.items():
                args.extend(["-c", key + "=" + value])
            result = adapter.runner(args + ["-"], input=_PROBE_TEXT, timeout=30, **options)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        if result.returncode or len(requests) != 1 or not isinstance(requests[0], dict):
            raise ValueError("Probe request/response failed")
        request = requests[0]
        if request.get("tools") != [] or request.get("model") != "gpt-5.5":
            raise ValueError("Text-only model/tool contract failed")
        wire = json.dumps(request)
        if _PROBE_TEXT not in wire or any(canary in wire for canary in _CANARIES):
            raise ValueError("Instruction isolation failed")
        if json.loads(
            result.stdout, object_pairs_hook=_unique_object, parse_constant=_invalid_constant
        ) != {"probe": "agent-ready"}:
            raise ValueError("JSON stdout contract failed")
