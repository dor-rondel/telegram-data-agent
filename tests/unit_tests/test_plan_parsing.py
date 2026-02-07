"""Tests for PlanResponse Pydantic model validation."""

import pytest
from pydantic import ValidationError

from agent.state import PlanResponse


class TestPlanResponseNotRelevant:
    """Tests for non-relevant plan responses."""

    def test_not_relevant_includes_reason(self) -> None:
        result = PlanResponse(relevant=False, reason="Not Judea & Samaria")
        assert result.relevant is False
        assert result.reason == "Not Judea & Samaria"

    def test_not_relevant_default_reason(self) -> None:
        result = PlanResponse(relevant=False)
        assert result.relevant is False
        assert result.reason == ""

    def test_not_relevant_no_crime_required(self) -> None:
        result = PlanResponse(relevant=False, reason="Test")
        assert result.crime is None
        assert result.location == ""


class TestPlanResponseRelevant:
    """Tests for relevant plan responses."""

    def test_relevant_valid_crime(self) -> None:
        result = PlanResponse(
            relevant=True,
            location="Jerusalem",
            crime="shooting",
            requires_email_alert=True,
        )
        assert result.relevant is True
        assert result.location == "Jerusalem"
        assert result.crime == "shooting"
        assert result.requires_email_alert is True

    def test_relevant_defaults(self) -> None:
        result = PlanResponse(relevant=True, crime="theft")
        assert result.relevant is True
        assert result.location == ""
        assert result.crime == "theft"
        assert result.requires_email_alert is False

    def test_all_valid_crime_types(self) -> None:
        valid_crimes = [
            "rock_throwing",
            "molotov_cocktail",
            "ramming",
            "stabbing",
            "shooting",
            "theft",
        ]
        for crime in valid_crimes:
            result = PlanResponse(relevant=True, crime=crime)  # type: ignore[arg-type]
            assert result.crime == crime


class TestPlanResponseValidationErrors:
    """Tests for PlanResponse validation failures."""

    def test_invalid_crime_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            PlanResponse(relevant=True, location="Ariel", crime="arson")  # type: ignore[arg-type]

    def test_missing_relevant_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            PlanResponse()  # type: ignore[call-arg]
