import pytest

from agent_ready.sources import (
    SourceError,
    build_github_issue_command,
    load_source,
    parse_issue_reference,
)


def test_reads_only_explicit_local_file(tmp_path):
    task = tmp_path / "task.md"
    task.write_text("Implement the bounded migration.", encoding="utf-8")
    assert load_source(str(task)) == "Implement the bounded migration."


def test_invalid_file_is_rejected():
    with pytest.raises(SourceError, match="not a readable file"):
        load_source("missing-task.md")


def test_parses_github_issue_reference():
    assert parse_issue_reference("octo/example#42") == ("octo", "example", 42)


def test_rejects_non_issue_reference():
    assert parse_issue_reference("notes.md") is None


def test_builds_non_shell_github_command():
    assert build_github_issue_command("octo", "example", 42) == [
        "gh",
        "issue",
        "view",
        "42",
        "--repo",
        "octo/example",
        "--json",
        "title,body",
    ]


def test_missing_gh_fails_closed(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("agent_ready.sources.subprocess.run", missing)
    with pytest.raises(SourceError, match="gh is not installed"):
        load_source("octo/example#42")


@pytest.mark.parametrize(
    "reference",
    [
        "octo/repo#0",
        "octo/repo#-1",
        "octo/repo#1;echo",
        "--repo/repo#1",
        "https://github.com/octo/repo/issues/1",
    ],
)
def test_invalid_issue_syntax_is_not_accepted(reference):
    assert parse_issue_reference(reference) is None


def test_github_title_and_body_only(monkeypatch):
    import subprocess

    def run(args, **kwargs):
        assert args == [
            "gh",
            "issue",
            "view",
            "42",
            "--repo",
            "octo/example",
            "--json",
            "title,body",
        ]
        assert kwargs["shell"] is False
        return subprocess.CompletedProcess(
            args, 0, stdout='{"title":"Synthetic title","body":"Synthetic task"}'
        )

    monkeypatch.setattr("agent_ready.sources.subprocess.run", run)
    assert load_source("octo/example#42") == "Synthetic title\n\nSynthetic task"


@pytest.mark.parametrize("stdout", ["not json", "[]", '{"title":null,"body":"text"}', "{}"])
def test_malformed_github_output_fails_closed(monkeypatch, stdout):
    import subprocess

    monkeypatch.setattr(
        "agent_ready.sources.subprocess.run",
        lambda *a, **kw: subprocess.CompletedProcess([], 0, stdout=stdout),
    )
    with pytest.raises(SourceError):
        load_source("octo/example#42")


def test_unreadable_utf8_file(tmp_path):
    task = tmp_path / "binary.md"
    task.write_bytes(b"\xff\xfe")
    with pytest.raises(SourceError):
        load_source(str(task))


def test_directory_cannot_be_loaded(tmp_path):
    with pytest.raises(SourceError):
        load_source(str(tmp_path))
