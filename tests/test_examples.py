import json
from pathlib import Path

import pytest
from test_engine_and_mcp import FakeProvider

from agent_ready.engine import AssessmentEngine

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize("case", ["ready", "clarify", "split", "hold"])
def test_synthetic_semantic_contract(case):
    task = (EXAMPLES / (case + ".md")).read_text()
    expected = json.loads((EXAMPLES / (case + ".json")).read_text())
    result = AssessmentEngine({"codex": FakeProvider(expected)}).assess(task, "codex")
    assert result["disposition"] == case.upper()
    if case == "ready":
        assert not result["owner_clarifications"]
        assert not result["semantic_split_recommendation"]
        assert result["implementation_unknowns"]
        assert "40 modules" in task
    elif case == "clarify":
        assert result["owner_clarifications"] == ["Must active sessions survive the migration?"]
        assert result["implementation_unknowns"] == [
            "Locate the existing session serializer and storage adapter."
        ]
    elif case == "split":
        assert len(result["independent_decision_centers"]) == 2
        assert len(result["semantic_split_recommendation"]) == 2
    else:
        assert "signed interface specification" in result["next_action"]
