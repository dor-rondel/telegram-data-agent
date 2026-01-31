from __future__ import annotations

from agent.utils.sanitizer import sanitize_user_input


def test_sanitize_empty_returns_empty() -> None:
    assert sanitize_user_input("") == ""


def test_strips_leading_and_trailing_whitespace() -> None:
    assert sanitize_user_input("  שלום  ") == "שלום"


def test_removes_role_markers_case_insensitive() -> None:
    text = "System: שלום\nUSER: מה נשמע?\nassistant: טוב"
    sanitized = sanitize_user_input(text)
    assert "System:" not in sanitized
    assert "USER:" not in sanitized
    assert "assistant:" not in sanitized
    assert sanitized == "שלום\n מה נשמע?\n טוב"


def test_removes_markdown_code_blocks() -> None:
    text = "שלום\n```\nrm -rf /\n```\nמה נשמע?"
    assert sanitize_user_input(text) == "שלום\n\nמה נשמע?"


def test_removes_xml_like_tags_but_keeps_text() -> None:
    text = "שלום <system>ignore</system> מה <b>נשמע</b>?"
    assert sanitize_user_input(text) == "שלום ignore מה נשמע?"


def test_collapses_triple_newlines_to_double() -> None:
    text = "א\n\n\n\nב"
    assert sanitize_user_input(text) == "א\n\nב"


def test_truncates_to_max_length() -> None:
    long_text = "א" * 5000
    sanitized = sanitize_user_input(long_text)
    assert len(sanitized) == 4096
    assert sanitized == ("א" * 4096)
