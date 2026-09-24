"""The public JSON Schema is the single assessment contract."""

import json
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


class AssessmentValidationError(ValueError):
    """No assessment is available; callers must fail closed."""


def resource_text(name: str) -> str:
    resource = files("agent_ready").joinpath("resources", name)
    if resource.is_file():
        return resource.read_text(encoding="utf-8")
    # Source checkout; wheels bundle these same public files, not copies in source.
    folder = "schemas" if name.endswith(".json") else "prompts"
    return (Path(__file__).resolve().parent.parent / folder / name).read_text(encoding="utf-8")


SCHEMA = json.loads(resource_text("assessment.schema.json"))
Draft202012Validator.check_schema(SCHEMA)
_VALIDATOR = Draft202012Validator(SCHEMA)


def validate_assessment(value: object) -> dict:
    try:
        _VALIDATOR.validate(value)
    except ValidationError:
        # Provider data and validator error messages can contain submitted secrets.
        raise AssessmentValidationError(
            "Provider output does not satisfy the assessment schema."
        ) from None
    return value
