"""CLI-only explicit source loading. Never imported by the MCP interface."""

import json
import re
import subprocess
from pathlib import Path

MAX_FILE_BYTES = 400_000
_ISSUE = re.compile(r"([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9_.-]+)#([1-9][0-9]{0,9})")


class SourceError(ValueError):
    pass


def parse_issue_reference(source: str) -> tuple[str, str, int] | None:
    match = _ISSUE.fullmatch(source)
    return (match[1], match[2], int(match[3])) if match else None


def build_github_issue_command(owner: str, repo: str, number: int) -> list[str]:
    if parse_issue_reference(f"{owner}/{repo}#{number}") != (owner, repo, number):
        raise SourceError("Invalid GitHub Issue reference; use OWNER/REPO#NUMBER.")
    return ["gh", "issue", "view", str(number), "--repo", f"{owner}/{repo}", "--json", "title,body"]


def load_source(source: str) -> str:
    reference = parse_issue_reference(source)
    if reference:
        try:
            result = subprocess.run(
                build_github_issue_command(*reference),
                shell=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
        except FileNotFoundError:
            raise SourceError("gh is not installed or not on PATH.") from None
        except (OSError, UnicodeError, subprocess.TimeoutExpired):
            raise SourceError("GitHub Issue retrieval failed.") from None
        if result.returncode:
            raise SourceError(
                "GitHub Issue retrieval failed; check gh authentication and Issue access."
            )
        try:
            value = json.loads(result.stdout)
            if (
                not isinstance(value, dict)
                or not isinstance(value.get("title"), str)
                or not isinstance(value.get("body"), str)
            ):
                raise ValueError
            return value["title"] + "\n\n" + value["body"]
        except (ValueError, RecursionError):
            raise SourceError("gh returned invalid Issue data.") from None
    try:
        path = Path(source)
        if not path.is_file():
            raise OSError
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise SourceError("Input file exceeds the 400000 byte limit.")
        return data.decode("utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        if isinstance(error, SourceError):
            raise
        raise SourceError("Source is not a readable file containing UTF-8 text.") from None
