import json
import subprocess
from urllib.request import Request, urlopen

import pytest
from test_contract import valid_assessment

from agent_ready.engine import AssessmentEngine
from agent_ready.providers import ClaudeAdapter, ProviderError

_FLAGS = (
    "--print --output-format --tools --safe-mode --strict-mcp-config --mcp-config "
    "--setting-sources --disable-slash-commands --no-chrome --no-session-persistence "
    "--permission-mode --system-prompt"
)
_PROBE_TEXT = "Agent Ready capability probe. Return only the synthetic JSON response."


class ContractRunner:
    """Stands in for the Claude Code CLI: posts what a real CLI would send to the loopback probe."""

    def __init__(self, version="2.1.281 (Claude Code)", defect=None):
        self.version = version
        self.defect = defect
        self.live_calls = 0
        self.probe_calls = 0
        self.probe_envs = []

    def __call__(self, args, **kwargs):
        if args[-1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=self.version, stderr="")
        if args[-1:] == ["--help"]:
            flags = _FLAGS
            if self.defect == "missing_flag":
                flags = flags.replace("--safe-mode", "")
            return subprocess.CompletedProcess(args, 0, stdout=flags, stderr="")
        base = kwargs["env"].get("ANTHROPIC_BASE_URL", "")
        if base.startswith("http://127.0.0.1:"):
            self.probe_calls += 1
            self.probe_envs.append(dict(kwargs["env"]))
            assert "actual private task" not in kwargs["input"]
            body = {
                "model": "claude-probe",
                "stream": True,
                "tools": [],
                "system": [{"type": "text", "text": "You assess software work."}],
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": kwargs["input"]}]}
                ],
            }
            if self.defect == "tools":
                body["tools"] = [{"name": "Bash", "input_schema": {"type": "object"}}]
            if self.defect == "missing_tools":
                del body["tools"]
            if self.defect == "leak":
                body["system"].append({"type": "text", "text": "PRIVATE_INSTRUCTION_CANARY"})
            if self.defect == "project_leak":
                body["system"].append({"type": "text", "text": "PROJECT_INSTRUCTION_CANARY"})
            data = json.dumps(body).encode()
            if self.defect == "duplicate_request_keys":
                # A permissive decoder keeps the LAST "tools" and would certify a tool-exposing CLI.
                data = (
                    b'{"model":"claude-probe","tools":[{"name":"Bash"}],"tools":[],'
                    b'"messages":[{"role":"user","content":"' + _PROBE_TEXT.encode() + b'"}]}'
                )
            path = "/v1/messages?beta=true"
            if self.defect == "unexpected_path":
                path = "/v1/complete"
            posts = 0 if self.defect == "no_request" else 1
            if self.defect == "second_request_with_tools":
                posts = 2
            for index in range(posts):
                payload = data
                if index == 1:
                    payload = json.dumps({**body, "tools": [{"name": "Bash"}]}).encode()
                try:
                    with urlopen(
                        Request(
                            base + path, data=payload, headers={"Content-Type": "application/json"}
                        ),
                        timeout=5,
                    ) as response:
                        response.read()
                except OSError:
                    pass  # a rejected probe request is the server's verdict, not the runner's
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=(
                    '{"probe":"bad","probe":"agent-ready"}'
                    if self.defect == "duplicate_keys"
                    else "not json"
                    if self.defect == "output"
                    else '{"probe":"agent-ready"}\n'
                ),
                stderr="",
            )
        self.live_calls += 1
        payload = valid_assessment()
        payload["provider_evidence"] = {"version": "forged", "compatibility": "SUPPORTED"}
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")


@pytest.mark.parametrize(
    "version,classification",
    [
        ("2.1.258 (Claude Code)", "SUPPORTED"),
        ("2.1.281 (Claude Code)", "COMPATIBLE_UNVERIFIED"),
        ("3.0.0 (Claude Code)", "COMPATIBLE_UNVERIFIED"),
    ],
)
def test_reviewed_or_capability_verified_claude_is_accepted(version, classification):
    runner = ContractRunner(version)
    result = AssessmentEngine({"claude": ClaudeAdapter(runner=runner)}).assess(
        "actual private task", "claude"
    )
    assert result["provider_evidence"] == {
        "provider": "claude",
        "version": version,
        "compatibility": classification,
        "capability_probe": "REVIEWED_VERSION" if classification == "SUPPORTED" else "PASSED",
    }
    assert runner.live_calls == 1
    assert runner.probe_calls == (0 if classification == "SUPPORTED" else 1)


@pytest.mark.parametrize(
    "defect",
    [
        "missing_flag",
        "tools",
        "missing_tools",
        "leak",
        "project_leak",
        "output",
        "no_request",
        "duplicate_keys",
        "duplicate_request_keys",
        "unexpected_path",
        "second_request_with_tools",
    ],
)
def test_incompatible_claude_fails_before_private_assessment(defect):
    runner = ContractRunner(defect=defect)
    adapter = ClaudeAdapter(runner=runner)
    with pytest.raises(ProviderError, match="INCOMPATIBLE"):
        adapter.assess("actual private task")
    assert adapter.evidence["compatibility"] == "INCOMPATIBLE"
    assert runner.live_calls == 0


@pytest.mark.parametrize(
    "reported", ["claude 2.1.281", "2.1.281", "", "2.1.281 (Claude Code) extra"]
)
def test_unrecognised_claude_version_response_fails_closed(reported):
    runner = ContractRunner(version=reported)
    with pytest.raises(ProviderError, match="INCOMPATIBLE"):
        ClaudeAdapter(runner=runner).assess("actual private task")
    assert runner.live_calls == 0 and runner.probe_calls == 0


def test_claude_probe_never_receives_assessment_credentials(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "real-assessment-secret")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "real-oauth-secret")
    runner = ContractRunner()
    ClaudeAdapter(runner=runner).assess("actual private task")
    (env,) = runner.probe_envs
    assert "real-assessment-secret" not in env.values()
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in env


def test_claude_compatibility_is_rechecked_not_cached_on_version_alone():
    runner = ContractRunner()
    adapter = ClaudeAdapter(runner=runner)
    adapter.assess("actual private task")
    runner.defect = "tools"
    with pytest.raises(ProviderError):
        adapter.assess("actual private task")
    assert runner.live_calls == 1


def test_public_schema_accepts_claude_evidence():
    from agent_ready.contracts import validate_assessment

    payload = valid_assessment()
    payload["provider_evidence"] = {
        "provider": "claude",
        "version": "2.1.281 (Claude Code)",
        "compatibility": "COMPATIBLE_UNVERIFIED",
        "capability_probe": "PASSED",
    }
    assert validate_assessment(payload) is payload


@pytest.mark.parametrize(
    "provider,version",
    [("claude", "codex-cli 0.154.0"), ("codex", "2.1.281 (Claude Code)")],
)
def test_public_schema_rejects_mismatched_provider_and_version(provider, version):
    from agent_ready.contracts import AssessmentValidationError, validate_assessment

    payload = valid_assessment()
    payload["provider_evidence"] = {
        "provider": provider,
        "version": version,
        "compatibility": "COMPATIBLE_UNVERIFIED",
        "capability_probe": "PASSED",
    }
    with pytest.raises(AssessmentValidationError):
        validate_assessment(payload)
