import pytest

from agent_ready.contracts import AssessmentValidationError, validate_assessment


def valid_assessment(disposition="READY"):
    payload = {
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
    if disposition == "CLARIFY":
        payload["owner_clarifications"] = ["Must active sessions survive migration?"]
    elif disposition == "SPLIT":
        payload["independent_decision_centers"] = ["Authentication", "Usage analytics"]
        payload["semantic_split_recommendation"] = [
            "Implement authentication with its own acceptance suite.",
            "Implement usage analytics with independent verification.",
        ]
    return payload


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


@pytest.mark.parametrize("field", ["owner_clarifications", "semantic_split_recommendation"])
def test_ready_rejects_unresolved_owner_intent_or_split_recommendations(field):
    payload = valid_assessment()
    payload[field] = ["Must active sessions survive migration?"]
    with pytest.raises(AssessmentValidationError):
        validate_assessment(payload)


def test_clarify_requires_owner_clarification():
    payload = valid_assessment("CLARIFY")
    payload["owner_clarifications"] = []
    with pytest.raises(AssessmentValidationError):
        validate_assessment(payload)


@pytest.mark.parametrize("field", ["independent_decision_centers", "semantic_split_recommendation"])
@pytest.mark.parametrize("count", [0, 1])
def test_split_requires_at_least_two_centers_and_recommendations(field, count):
    payload = valid_assessment("SPLIT")
    payload[field] = payload[field][:count]
    with pytest.raises(AssessmentValidationError):
        validate_assessment(payload)


def test_split_rejects_unresolved_owner_clarification():
    payload = valid_assessment("SPLIT")
    payload["owner_clarifications"] = ["Must active sessions survive migration?"]
    with pytest.raises(AssessmentValidationError):
        validate_assessment(payload)


def test_ready_allows_implementation_unknowns_risks_and_coherent_decisions():
    payload = valid_assessment()
    payload["material_risks"] = ["Serializer performance needs verification."]
    payload["independent_decision_centers"] = ["Session migration under frozen compatibility."]
    assert validate_assessment(payload) == payload


@pytest.mark.parametrize("disposition", ["CLARIFY", "HOLD"])
def test_clarify_and_hold_do_not_require_other_arrays_to_be_empty(disposition):
    payload = valid_assessment("SPLIT")
    payload["disposition"] = disposition
    payload["owner_clarifications"] = ["Must active sessions survive migration?"]
    assert validate_assessment(payload) == payload


def test_split_allows_more_than_two_centers_and_recommendations():
    payload = valid_assessment("SPLIT")
    payload["independent_decision_centers"].append("Billing")
    payload["semantic_split_recommendation"].append("Implement billing with its own verification.")
    assert validate_assessment(payload) == payload
