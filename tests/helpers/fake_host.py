"""Test-only subprocess boundary; never installed as a provider or production mode."""

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from agent_ready import providers  # noqa: E402

temporary_auth = TemporaryDirectory(prefix="agent-ready-test-auth-")
os.environ["CODEX_HOME"] = temporary_auth.name
mode, case = sys.argv[1:3]


def fake_run(args, **kwargs):
    if args[-1:] == ["--version"]:
        version = "codex-cli 0.153.4" if args[0] == "codex" else "2.1.258 (Claude Code)"
        return subprocess.CompletedProcess(args, 0, stdout=version, stderr="")
    if case == "failure":
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="private-canary")
    output = (
        '{"disposition":"READY"}'
        if case == "malformed"
        else (ROOT / "examples" / (case + ".json")).read_text()
    )
    return subprocess.CompletedProcess(args, 0, stdout=output, stderr="")


providers.subprocess.run = fake_run
if mode == "mcp":
    from agent_ready.mcp_server import main

    main()
else:
    from agent_ready.cli import main

    raise SystemExit(main(sys.argv[3:]))
