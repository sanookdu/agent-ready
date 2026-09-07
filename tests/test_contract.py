import pytest

from agent_ready.contracts import AssessmentValidationError, validate_assessment


def valid_assessment(disposition="READY"):
    return {
        "disposition": disposition,
        "governing_intent": "Deliver one bounded outcome.",
        "summary": "The work is assessable.",
        "owner_clarifications": [],
        "implementation_unknowns": ["Locate the existing serializer."],
        "independent_decision_centers": [],
        "semantic_split_recommendation": [],
        "verification_assessment": "One acceptance suite can decide the result.",
        "expected_rework_locality": "HIGH",
        "material_risks": [],
        "next_action": "Proceed with implementation.",
        "rationale": "Intent and verification are coherent.",
    }


@pytest.mark.parametrize("disposition", ["READY", "CLARIFY", "SPLIT", "HOLD"])
def test_valid_dispositions_validate(disposition):
    assert validate_assessment(valid_assessment(disposition))["disposition"] == disposition


def test_unknown_disposition_is_rejected():
    with pytest.raises(AssessmentValidationError):
        validate_assessment(valid_assessment("MAYBE"))


def test_missing_required_field_is_rejected():
    payload = valid_assessment()
    del payload["rationale"]
    with pytest.raises(AssessmentValidationError):
        validate_assessment(payload)


def test_invalid_rework_enum_is_rejected():
    payload = valid_assessment()
    payload["expected_rework_locality"] = "UNKNOWN"
    with pytest.raises(AssessmentValidationError):
        validate_assessment(payload)
