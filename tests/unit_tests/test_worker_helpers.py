"""Tests for worker node helper functions."""

from typing import Any

from agent.nodes.worker import _build_user_prompt


class TestBuildUserPrompt:
    """Tests for _build_user_prompt function."""

    def test_builds_prompt_with_incident_data(self) -> None:
        state: dict[str, Any] = {
            "incident_data": {"location": "Jerusalem", "crime": "rock_throwing"},
            "requires_email_alert": True,
            "plan_reason": "Relevant incident detected",
        }
        prompt = _build_user_prompt(state)  # type: ignore[arg-type]

        assert "## Current Plan" in prompt
        assert "requires_email_alert: True" in prompt
        assert "plan_reason: Relevant incident detected" in prompt
        assert "## Incident Data" in prompt
        assert "location: Jerusalem" in prompt
        assert "crime: rock_throwing" in prompt

    def test_builds_prompt_without_incident_data(self) -> None:
        state: dict[str, Any] = {
            "incident_data": None,
            "requires_email_alert": False,
            "plan_reason": "Event not relevant",
        }
        prompt = _build_user_prompt(state)  # type: ignore[arg-type]

        assert "## Current Plan" in prompt
        assert "requires_email_alert: False" in prompt
        assert "plan_reason: Event not relevant" in prompt
        assert "No incident data available" in prompt

    def test_uses_default_plan_reason_when_missing(self) -> None:
        state: dict[str, Any] = {
            "incident_data": None,
            "requires_email_alert": False,
        }
        prompt = _build_user_prompt(state)  # type: ignore[arg-type]

        assert "No reason provided" in prompt

    def test_includes_execution_instruction(self) -> None:
        state: dict[str, Any] = {
            "incident_data": {"location": "Hebron", "crime": "stabbing"},
            "requires_email_alert": False,
            "plan_reason": "Test reason",
        }
        prompt = _build_user_prompt(state)  # type: ignore[arg-type]

        assert "Execute the appropriate tools" in prompt
