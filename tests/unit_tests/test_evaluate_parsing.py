"""Tests for EvaluationResponse Pydantic model validation."""

import pytest
from pydantic import ValidationError

from agent.state import EvaluationResponse


class TestEvaluationResponse:
    """Tests for EvaluationResponse model."""

    def test_valid_score_and_feedback(self) -> None:
        result = EvaluationResponse(score=8.5, feedback="")
        assert result.score == 8.5
        assert result.feedback == ""

    def test_integer_score(self) -> None:
        result = EvaluationResponse(score=10, feedback="great")
        assert result.score == 10.0
        assert result.feedback == "great"

    def test_zero_score(self) -> None:
        result = EvaluationResponse(score=0, feedback="Poor translation")
        assert result.score == 0.0

    def test_max_score(self) -> None:
        result = EvaluationResponse(score=10, feedback="")
        assert result.score == 10.0


class TestEvaluationResponseValidationErrors:
    """Tests for EvaluationResponse validation failures."""

    def test_score_above_max_raises(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationResponse(score=11, feedback="")

    def test_score_below_min_raises(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationResponse(score=-1, feedback="")

    def test_missing_score_raises(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationResponse(feedback="test")  # type: ignore[call-arg]

    def test_missing_feedback_raises(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationResponse(score=8.0)  # type: ignore[call-arg]
