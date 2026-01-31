"""Tests for worker should_continue function."""

from typing import Any

from agent.nodes.worker import should_continue


class TestShouldContinue:
    """Tests for should_continue function."""

    def test_returns_end_when_should_end_true(self) -> None:
        state: dict[str, Any] = {"should_end": True}
        assert should_continue(state) == "end"  # type: ignore[arg-type]

    def test_returns_worker_when_should_end_false(self) -> None:
        state: dict[str, Any] = {"should_end": False}
        assert should_continue(state) == "worker"  # type: ignore[arg-type]

    def test_returns_worker_when_should_end_missing(self) -> None:
        state: dict[str, Any] = {}
        assert should_continue(state) == "worker"  # type: ignore[arg-type]
