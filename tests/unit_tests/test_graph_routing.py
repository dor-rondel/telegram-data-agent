"""Tests for graph routing functions."""

from typing import Any

from agent.graph import route_after_evaluate, route_after_plan


class TestRouteAfterEvaluate:
    """Tests for route_after_evaluate function."""

    def test_routes_to_plan_when_score_meets_threshold(self) -> None:
        state: dict[str, Any] = {
            "evaluation_score": 0.8,
            "threshold": 0.75,
            "iteration": 1,
            "max_iterations": 5,
        }
        assert route_after_evaluate(state) == "plan"  # type: ignore[arg-type]

    def test_routes_to_plan_when_score_equals_threshold(self) -> None:
        state: dict[str, Any] = {
            "evaluation_score": 0.75,
            "threshold": 0.75,
            "iteration": 1,
            "max_iterations": 5,
        }
        assert route_after_evaluate(state) == "plan"  # type: ignore[arg-type]

    def test_routes_to_end_when_max_iterations_reached(self) -> None:
        state: dict[str, Any] = {
            "evaluation_score": 0.5,
            "threshold": 0.75,
            "iteration": 5,
            "max_iterations": 5,
        }
        assert route_after_evaluate(state) == "__end__"  # type: ignore[arg-type]

    def test_routes_to_translate_to_continue_loop(self) -> None:
        state: dict[str, Any] = {
            "evaluation_score": 0.5,
            "threshold": 0.75,
            "iteration": 2,
            "max_iterations": 5,
        }
        assert route_after_evaluate(state) == "translate"  # type: ignore[arg-type]

    def test_uses_default_values_when_missing(self) -> None:
        state: dict[str, Any] = {}
        # score=0.0, threshold=0.75, iteration=0, max_iterations=5
        assert route_after_evaluate(state) == "translate"  # type: ignore[arg-type]

    def test_high_score_bypasses_iteration_check(self) -> None:
        state: dict[str, Any] = {
            "evaluation_score": 1.0,
            "threshold": 0.75,
            "iteration": 10,
            "max_iterations": 5,
        }
        assert route_after_evaluate(state) == "plan"  # type: ignore[arg-type]


class TestRouteAfterPlan:
    """Tests for route_after_plan function."""

    def test_routes_to_end_when_skip_processing_true(self) -> None:
        state: dict[str, Any] = {"skip_processing": True}
        assert route_after_plan(state) == "__end__"  # type: ignore[arg-type]

    def test_routes_to_worker_when_skip_processing_false(self) -> None:
        state: dict[str, Any] = {"skip_processing": False}
        assert route_after_plan(state) == "worker"  # type: ignore[arg-type]

    def test_routes_to_worker_when_skip_processing_missing(self) -> None:
        state: dict[str, Any] = {}
        assert route_after_plan(state) == "worker"  # type: ignore[arg-type]
