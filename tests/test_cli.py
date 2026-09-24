import json

import pytest
from test_contract import valid_assessment
from test_engine_and_mcp import FakeProvider

from agent_ready.cli import main
from agent_ready.engine import AssessmentEngine


@pytest.mark.parametrize("disposition", ["READY", "CLARIFY", "SPLIT", "HOLD"])
@pytest.mark.parametrize("as_json", [False, True])
def test_cli_renders_valid_assessment(tmp_path, monkeypatch, capsys, disposition, as_json):
    task = tmp_path / "task.md"
    task.write_text("One synthetic work unit.")
    payload = valid_assessment(disposition)
    monkeypatch.setattr(
        "agent_ready.cli.default_engine", lambda: AssessmentEngine({"codex": FakeProvider(payload)})
    )
    args = ["assess", str(task), "--provider", "codex"] + (["--json"] if as_json else [])
    assert main(args) == 0
    output = capsys.readouterr()
    assert not output.err
    if as_json:
        assert json.loads(output.out) == payload
    else:
        assert disposition in output.out
        assert payload["next_action"] in output.out


def test_cli_malformed_output_is_nonzero_without_assessment(tmp_path, monkeypatch, capsys):
    task = tmp_path / "task.md"
    task.write_text("Task")
    monkeypatch.setattr(
        "agent_ready.cli.default_engine",
        lambda: AssessmentEngine({"codex": FakeProvider({"disposition": "READY"})}),
    )
    assert main(["assess", str(task), "--provider", "codex", "--json"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "schema" in output.err


def test_cli_invalid_file_returns_error(capsys):
    assert main(["assess", "does-not-exist.md", "--provider", "claude"]) == 1
    assert not capsys.readouterr().out


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as result:
        main(["--help"])
    assert result.value.code == 0
    assert "assess" in capsys.readouterr().out
