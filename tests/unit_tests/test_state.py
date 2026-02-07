"""Tests for State type definitions and Pydantic models."""

import pytest
from pydantic import ValidationError

from agent.state import (
    ActionPlan,
    EvaluationResponse,
    IncidentCrime,
    IncidentDataModel,
    PlanResponse,
    WorkerAction,
)


class TestIncidentCrime:
    """Tests for IncidentCrime type alias."""

    def test_valid_crime_types(self) -> None:
        valid_crimes: list[IncidentCrime] = [
            "rock_throwing",
            "molotov_cocktail",
            "ramming",
            "stabbing",
            "shooting",
            "theft",
        ]
        # This just verifies the type alias accepts these values
        assert len(valid_crimes) == 6


class TestIncidentDataModel:
    """Tests for IncidentDataModel Pydantic model."""

    def test_valid_incident(self) -> None:
        model = IncidentDataModel(location="Jerusalem", crime="stabbing")
        assert model.location == "Jerusalem"
        assert model.crime == "stabbing"

    def test_incident_data_attributes(self) -> None:
        model = IncidentDataModel(location="Hebron", crime="rock_throwing")
        assert model.location == "Hebron"
        assert model.crime == "rock_throwing"

    def test_invalid_crime_raises(self) -> None:
        with pytest.raises(ValidationError):
            IncidentDataModel(location="Jerusalem", crime="arson")  # type: ignore[arg-type]


class TestPydanticModelsExist:
    """Smoke tests that all Pydantic models can be imported and instantiated."""

    def test_plan_response(self) -> None:
        obj = PlanResponse(relevant=False)
        assert obj.relevant is False

    def test_evaluation_response(self) -> None:
        obj = EvaluationResponse(score=5.0, feedback="ok")
        assert obj.score == 5.0

    def test_worker_action(self) -> None:
        obj = WorkerAction(action="send_email", location="Hebron", crime="shooting")
        assert obj.action == "send_email"

    def test_action_plan(self) -> None:
        obj = ActionPlan(actions=[])
        assert obj.actions == []
