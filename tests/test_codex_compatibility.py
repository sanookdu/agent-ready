import json
import subprocess
from urllib.request import Request, urlopen

import pytest
from test_contract import valid_assessment

from agent_ready.engine import AssessmentEngine
from agent_ready.providers import CodexAdapter, ProviderError


class ContractRunner:
    def __init__(self, version="codex-cli 0.154.0", defect=None):
        self.version = version
        self.defect = defect
        self.live_calls = 0
        self.probe_calls = 0

    def __call__(self, args, **kwargs):
        if args[-1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=self.version, stderr="")
        if args[-1:] == ["--help"]:
            flags = "--sandbox read-only --ignore-user-config --ignore-rules --ephemeral --skip-git-repo-check --color --config"
            if self.defect == "missing_flag":
                flags = flags.replace("--ignore-rules", "")
            return subprocess.CompletedProcess(args, 0, stdout=flags, stderr="")
        setting = next(
            (a for a in args if a.startswith("model_providers.agent_ready_probe.base_url=")), None
        )
        if setting:
            self.probe_calls += 1
            assert not any(kwargs["env"].get(k) for k in ("OPENAI_API_KEY", "CODEX_API_KEY"))
            assert "actual private task" not in kwargs["input"]
            url = json.loads(setting.split("=", 1)[1]) + "/responses"
            body = {"model": "gpt-5.5", "tools": [], "input": kwargs["input"]}
            if self.defect == "tools":
                body["tools"] = [{"type": "function", "name": "shell"}]
            if self.defect == "missing_tools":
                del body["tools"]
            if self.defect == "leak":
                body["input"] += " PRIVATE_INSTRUCTION_CANARY"
            if self.defect != "no_request":
                with urlopen(
                    Request(
                        url,
                        data=json.dumps(body).encode(),
                        headers={"Content-Type": "application/json"},
                    ),
                    timeout=5,
                ) as response:
                    response.read()
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=(
                    '{"probe":"bad","probe":"agent-ready"}'
                    if self.defect == "duplicate_keys"
                    else "not json"
                    if self.defect == "output"
                    else '{"probe":"agent-ready"}'
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
        ("codex-cli 0.153.4", "SUPPORTED"),
        ("codex-cli 0.154.0", "COMPATIBLE_UNVERIFIED"),
        ("codex-cli 1.0.0", "COMPATIBLE_UNVERIFIED"),
    ],
)
def test_supported_or_capability_verified_provider_is_accepted(version, classification):
    runner = ContractRunner(version)
    result = AssessmentEngine({"codex": CodexAdapter(runner=runner)}).assess(
        "actual private task", "codex"
    )
    assert result["provider_evidence"]["version"] == version
    assert result["provider_evidence"]["compatibility"] == classification
    assert runner.live_calls == 1
    assert runner.probe_calls == (0 if classification == "SUPPORTED" else 1)


@pytest.mark.parametrize(
    "defect",
    ["missing_flag", "tools", "missing_tools", "leak", "output", "no_request", "duplicate_keys"],
)
def test_incompatible_contract_fails_before_private_assessment(defect):
    runner = ContractRunner(defect=defect)
    adapter = CodexAdapter(runner=runner)
    with pytest.raises(ProviderError, match="INCOMPATIBLE"):
        adapter.assess("actual private task")
    assert adapter.evidence["compatibility"] == "INCOMPATIBLE"
    assert runner.live_calls == 0


def test_compatibility_is_rechecked_not_cached_on_version_alone():
    runner = ContractRunner()
    adapter = CodexAdapter(runner=runner)
    adapter.assess("actual private task")
    runner.defect = "tools"
    with pytest.raises(ProviderError):
        adapter.assess("actual private task")
    assert runner.live_calls == 1


def test_cli_renders_host_provider_evidence():
    from agent_ready.cli import _human

    payload = valid_assessment()
    payload["provider_evidence"] = {
        "provider": "codex",
        "version": "codex-cli 0.154.0",
        "compatibility": "COMPATIBLE_UNVERIFIED",
        "capability_probe": "PASSED",
    }
    assert "codex-cli 0.154.0" in _human(payload)


def test_public_schema_rejects_unverified_compatibility_without_passed_probe():
    from agent_ready.contracts import AssessmentValidationError, validate_assessment

    payload = valid_assessment()
    payload["provider_evidence"] = {
        "provider": "codex",
        "version": "codex-cli 0.154.0",
        "compatibility": "COMPATIBLE_UNVERIFIED",
        "capability_probe": "REVIEWED_VERSION",
    }
    with pytest.raises(AssessmentValidationError):
        validate_assessment(payload)


@pytest.mark.parametrize(
    "version,defect",
    [("codex-cli 0.153.4", None), ("codex-cli 0.154.0", None), ("codex-cli 0.154.0", "tools")],
)
def test_cli_and_mcp_share_provider_contract(version, defect, monkeypatch, tmp_path, capsys):
    import asyncio

    from agent_ready import cli, mcp_server

    def engine():
        return AssessmentEngine({"codex": CodexAdapter(runner=ContractRunner(version, defect))})

    monkeypatch.setattr(cli, "default_engine", engine)
    monkeypatch.setattr(mcp_server, "default_engine", engine)
    source = tmp_path / "task.md"
    source.write_text("actual private task")
    status = cli.main(["assess", str(source), "--provider", "codex", "--json"])
    output = capsys.readouterr()
    result = asyncio.run(
        mcp_server.call_tool("assess_work_unit", {"provider": "codex", "text": source.read_text()})
    )
    if defect:
        assert status == 1 and result.isError
        assert not output.out and result.structuredContent is None
    else:
        assert status == 0 and not result.isError
        assert json.loads(output.out) == result.structuredContent
        assert json.loads(result.content[0].text) == result.structuredContent
