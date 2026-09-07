"""Opt-in offline capability check of the real pinned Codex binary. No inference.

Run: python tests/probe_codex.py
Only a loopback fake Responses endpoint is used; no user credentials are copied.
"""

import http.server
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_ready.providers import CodexAdapter, ProviderError  # noqa: E402

requests = []


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        requests.append(json.loads(body))
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b'{"error":{"message":"offline probe completed"}}')

    def log_message(self, *args):
        pass


httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=httpd.serve_forever, daemon=True)
thread.start()


def runner(args, **kwargs):
    if args[-1:] != ["--version"]:
        overrides = {
            "model_provider": '"offline_probe"',
            "model_providers.offline_probe.name": '"offline_probe"',
            "model_providers.offline_probe.base_url": json.dumps(
                f"http://127.0.0.1:{httpd.server_port}/v1"
            ),
            "model_providers.offline_probe.wire_api": '"responses"',
            "model_providers.offline_probe.request_max_retries": "0",
            "model_providers.offline_probe.stream_max_retries": "0",
        }
        args = args[:-1]
        for key, value in overrides.items():
            args += ["-c", key + "=" + value]
        args += ["-"]
    kwargs["timeout"] = 30
    return subprocess.run(args, **kwargs)


try:
    with TemporaryDirectory(prefix="agent-ready-probe-origin-") as origin:
        home = Path(origin)
        (home / "AGENTS.md").write_text("PRIVATE_INSTRUCTION_CANARY")
        skill = home / ".agents" / "skills" / "private"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: private\ndescription: PRIVATE_SKILL_CANARY\n---\nprivate"
        )
        with patch.dict(os.environ, {"CODEX_HOME": origin, "HOME": origin, "USERPROFILE": origin}):
            with patch.dict(
                os.environ,
                {
                    key: ""
                    for key in (
                        "OPENAI_API_KEY",
                        "CODEX_API_KEY",
                        "ANTHROPIC_API_KEY",
                        "CLAUDE_CODE_OAUTH_TOKEN",
                    )
                },
            ):
                try:
                    CodexAdapter(runner=runner).assess(
                        "Analyze this synthetic task; do not execute it."
                    )
                except ProviderError:
                    pass  # Fake endpoint deliberately refuses inference.
    assert len(requests) == 1, f"Expected one local request, got {len(requests)}"
    assert requests[0].get("tools") == [], "Provider exposed tools"
    serialized = json.dumps(requests[0])
    assert "PRIVATE_INSTRUCTION_CANARY" not in serialized
    assert "PRIVATE_SKILL_CANARY" not in serialized
    print(
        "PASS: Codex 0.153.4, one loopback request, zero tools, no private instruction/skill canaries, no inference."
    )
finally:
    httpd.shutdown()
    httpd.server_close()
    thread.join()
