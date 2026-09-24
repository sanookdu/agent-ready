"""Explicit sources in, validated assessment out; no automatic handoff."""

import argparse
import json
import sys

from .engine import default_engine
from .providers import ProviderError
from .sources import load_source


def _human(assessment: dict) -> str:
    lines = [
        assessment["disposition"] + " — " + assessment["summary"],
        "Next action: " + assessment["next_action"],
    ]
    for key, value in assessment.items():
        if key in ("disposition", "summary", "next_action"):
            continue
        label = key.replace("_", " ").capitalize()
        if isinstance(value, list):
            lines.append(label + ": " + ("; ".join(value) if value else "None"))
        elif isinstance(value, dict):
            lines.append(label + ": " + json.dumps(value, sort_keys=True))
        else:
            lines.append(label + ": " + value)
    # Model output is untrusted, including terminal control sequences.
    return "\n".join(
        "".join(char if char.isprintable() else " " for char in line) for line in lines
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Assess software work before autonomous implementation."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    assess = commands.add_parser("assess", help="Assess one explicit file or GitHub Issue")
    assess.add_argument("source", help="UTF-8 text/Markdown file or OWNER/REPO#NUMBER")
    assess.add_argument("--provider", required=True, choices=("codex", "claude"))
    assess.add_argument("--json", action="store_true", help="Print the validated JSON assessment")
    args = parser.parse_args(argv)
    try:
        result = default_engine().assess(load_source(args.source), args.provider)
    except (ValueError, ProviderError) as error:
        print("agent-ready: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2) if args.json else _human(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
