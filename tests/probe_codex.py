"""Opt-in real Codex contract check: loopback only, no auth or inference."""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_ready.codex_compatibility import probe_codex  # noqa: E402
from agent_ready.providers import CodexAdapter  # noqa: E402

if __name__ == "__main__":
    adapter = CodexAdapter()
    options = dict(
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
        env={"PATH": os.environ["PATH"]},
    )
    probe_codex(adapter, options)
    version = subprocess.run(["codex", "--version"], text=True, capture_output=True, check=True)
    print(
        "PASS:",
        version.stdout.strip(),
        "required flags, one loopback request, zero tools, no private canaries, JSON output; no inference.",
    )
