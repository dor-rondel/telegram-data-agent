import json

import pytest

from agent.nodes.evaluate import _parse_evaluation_response


def test_parse_evaluation_response_normalizes_score_and_feedback() -> None:
    result = _parse_evaluation_response('{"score": 8.5, "feedback": ""}')
    assert result["score"] == pytest.approx(0.85)
    assert result["feedback"] == ""


def test_parse_evaluation_response_accepts_integer_score() -> None:
    result = _parse_evaluation_response('{"score": 10, "feedback": "great"}')
    assert result["score"] == pytest.approx(1.0)
    assert result["feedback"] == "great"


def test_parse_evaluation_response_invalid_json_raises() -> None:
    with pytest.raises(json.JSONDecodeError):
        _parse_evaluation_response("not-json")


def test_parse_evaluation_response_missing_keys_raises() -> None:
    with pytest.raises(KeyError):
        _parse_evaluation_response('{"score": 8.0}')
