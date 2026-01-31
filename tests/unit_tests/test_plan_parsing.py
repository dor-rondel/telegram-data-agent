import json

import pytest

import agent.nodes.plan as plan_module


def test_parse_plan_response_not_relevant_includes_reason() -> None:
    result = plan_module._parse_plan_response(
        '{"relevant": false, "reason": "Not Judea & Samaria"}'
    )
    assert result == {"relevant": False, "reason": "Not Judea & Samaria"}


def test_parse_plan_response_missing_relevant_defaults_to_not_relevant() -> None:
    result = plan_module._parse_plan_response('{"reason": "Unknown"}')
    assert result["relevant"] is False
    assert result["reason"] == "Unknown"


def test_parse_plan_response_not_relevant_default_reason() -> None:
    result = plan_module._parse_plan_response("{}")
    assert result == {"relevant": False, "reason": "Event not relevant"}


def test_parse_plan_response_relevant_valid_crime() -> None:
    result = plan_module._parse_plan_response(
        "\n".join(
            [
                "{",
                '  "relevant": true,',
                '  "location": "Jerusalem",',
                '  "crime": "shooting",',
                '  "requires_email_alert": true',
                "}",
            ]
        )
    )
    assert result == {
        "relevant": True,
        "location": "Jerusalem",
        "crime": plan_module.CrimeType.SHOOTING.value,
        "requires_email_alert": True,
    }


def test_parse_plan_response_relevant_missing_optional_fields_defaults() -> None:
    result = plan_module._parse_plan_response('{"relevant": true, "crime": "theft"}')
    assert result["relevant"] is True
    assert result["location"] == ""
    assert result["crime"] == plan_module.CrimeType.THEFT.value
    assert result["requires_email_alert"] is False


def test_parse_plan_response_invalid_json_raises() -> None:
    with pytest.raises(json.JSONDecodeError):
        plan_module._parse_plan_response("not-json")


def test_parse_plan_response_invalid_crime_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"Invalid crime type"):
        plan_module._parse_plan_response(
            '{"relevant": true, "location": "Ariel", "crime": "arson"}'
        )


def test_build_incident_data_returns_location_and_crime() -> None:
    result = plan_module._build_incident_data(
        location="Jerusalem",
        crime=plan_module.CrimeType.ROCK_THROWING.value,
    )

    assert result == {
        "location": "Jerusalem",
        "crime": plan_module.CrimeType.ROCK_THROWING.value,
    }
