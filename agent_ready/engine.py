"""Shared readiness semantics and validation for CLI and MCP."""

import json
from typing import Protocol

from .contracts import SCHEMA, resource_text, validate_assessment

MAX_TEXT_CHARS = 100_000


class Provider(Protocol):
    def assess(self, prompt: str) -> object: ...


class AssessmentEngine:
    def __init__(self, providers: dict[str, Provider]):
        self.providers = providers

    def assess(self, text: str, provider: str) -> dict:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Task text must be a non-empty string.")
        if len(text) > MAX_TEXT_CHARS:
            raise ValueError("Task text exceeds the 100000 character input limit.")
        if not isinstance(provider, str) or provider not in self.providers:
            raise ValueError("Select a supported provider: codex or claude.")
        # JSON escapes plus escaped angle brackets keep delimiters unambiguous.
        data = json.dumps(text, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e")
        model_schema = {**SCHEMA, "properties": dict(SCHEMA["properties"])}
        model_schema["properties"].pop("provider_evidence", None)
        prompt = (
            resource_text("readiness.md")
            + "\nOutput JSON Schema:\n"
            + json.dumps(model_schema)
            + "\n<untrusted_task_text>\n"
            + data
            + "\n</untrusted_task_text>\n"
        )
        adapter = self.providers[provider]
        result = adapter.assess(prompt)
        if isinstance(result, dict):
            result = dict(result)
            # Version/probe evidence is measured by the host, never model authority.
            result.pop("provider_evidence", None)
            evidence = getattr(adapter, "evidence", None)
            if evidence is not None:
                result["provider_evidence"] = dict(evidence)
        return validate_assessment(result)


def default_engine() -> AssessmentEngine:
    from .providers import ClaudeAdapter, CodexAdapter

    return AssessmentEngine({"codex": CodexAdapter(), "claude": ClaudeAdapter()})
