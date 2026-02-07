"""Tests for ActionPlan and WorkerAction Pydantic model validation."""

import pytest
from pydantic import ValidationError

from agent.state import ActionPlan, WorkerAction


class TestWorkerAction:
    """Tests for WorkerAction model."""

    def test_valid_send_email_action(self) -> None:
        action = WorkerAction(
            action="send_email",
            location="Jerusalem",
            crime="stabbing",
        )
        assert action.action == "send_email"
        assert action.location == "Jerusalem"
        assert action.crime == "stabbing"

    def test_valid_push_to_dynamodb_action(self) -> None:
        action = WorkerAction(
            action="push_to_dynamodb",
            location="Hebron",
            crime="rock_throwing",
        )
        assert action.action == "push_to_dynamodb"
        assert action.crime == "rock_throwing"

    def test_invalid_action_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkerAction(
                action="delete_record",  # type: ignore[arg-type]
                location="Jerusalem",
                crime="stabbing",
            )

    def test_invalid_crime_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkerAction(
                action="send_email",
                location="Jerusalem",
                crime="arson",  # type: ignore[arg-type]
            )

    def test_missing_location_raises(self) -> None:
        with pytest.raises(ValidationError):
            WorkerAction(action="send_email", crime="stabbing")  # type: ignore[call-arg]


class TestActionPlan:
    """Tests for ActionPlan model."""

    def test_empty_actions_list(self) -> None:
        plan = ActionPlan(actions=[])
        assert plan.actions == []

    def test_single_action(self) -> None:
        plan = ActionPlan(
            actions=[
                WorkerAction(
                    action="push_to_dynamodb",
                    location="Nablus",
                    crime="shooting",
                ),
            ]
        )
        assert len(plan.actions) == 1
        assert plan.actions[0].action == "push_to_dynamodb"

    def test_email_then_dynamodb_plan(self) -> None:
        plan = ActionPlan(
            actions=[
                WorkerAction(
                    action="send_email",
                    location="Jerusalem",
                    crime="stabbing",
                ),
                WorkerAction(
                    action="push_to_dynamodb",
                    location="Jerusalem",
                    crime="stabbing",
                ),
            ]
        )
        assert len(plan.actions) == 2
        assert plan.actions[0].action == "send_email"
        assert plan.actions[1].action == "push_to_dynamodb"

    def test_invalid_action_in_list_raises(self) -> None:
        with pytest.raises(ValidationError):
            ActionPlan(
                actions=[
                    {  # type: ignore[list-item]
                        "action": "noop",
                        "location": "Test",
                        "crime": "theft",
                    },
                ]
            )
