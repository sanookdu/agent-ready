import subprocess

import pytest

from agent_ready.providers import ClaudeAdapter, CodexAdapter, ProviderError


class FakeRunner:
    def __init__(self, result=None, error=None):
        self.result = result or subprocess.CompletedProcess([], 0, stdout="{}", stderr="")
        self.error = error
        self.calls = []

    def __call__(self, args, **kwargs):
        if args[-1:] == ["--version"] and not self.error:
            version = "codex-cli 0.153.4" if args[0] == "codex" else "2.1.258 (Claude Code)"
            return subprocess.CompletedProcess(args, 0, stdout=version, stderr="")
        self.calls.append((args, kwargs))
        if self.error:
            raise self.error
        return self.result


@pytest.mark.parametrize(
    ("adapter_class", "expected"),
    [
        (CodexAdapter, ["codex", "exec", "--sandbox", "read-only"]),
        (ClaudeAdapter, ["claude", "--print", "--output-format", "text", "--tools", ""]),
    ],
)
def test_adapters_invoke_constrained_provider_commands(adapter_class, expected):
    runner = FakeRunner()
    adapter = adapter_class(runner=runner)
    assert adapter.assess("prompt") == {}
    assert runner.calls[0][0][: len(expected)] == expected
    if adapter_class is CodexAdapter:
        command = runner.calls[0][0]
        assert command[command.index("--disable") + 1] == "goals"
    assert runner.calls[0][1]["input"] == "prompt"
    assert runner.calls[0][1]["shell"] is False


@pytest.mark.parametrize("adapter_class", [CodexAdapter, ClaudeAdapter])
def test_missing_provider_executable_fails_closed(adapter_class):
    with pytest.raises(ProviderError, match="not installed"):
        adapter_class(runner=FakeRunner(error=FileNotFoundError())).assess("prompt")


def test_provider_error_fails_closed():
    result = subprocess.CompletedProcess([], 1, stdout="", stderr="provider failed")
    with pytest.raises(ProviderError, match="provider failed"):
        CodexAdapter(runner=FakeRunner(result=result)).assess("prompt")


def test_malformed_json_fails_closed():
    result = subprocess.CompletedProcess([], 0, stdout="not json", stderr="")
    with pytest.raises(ProviderError, match="valid JSON"):
        ClaudeAdapter(runner=FakeRunner(result=result)).assess("prompt")
