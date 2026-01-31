from agent.nodes.translate import _build_user_prompt


def test_build_user_prompt_without_feedback() -> None:
    prompt = _build_user_prompt(
        text="שלום",
        feedback="",
        previous_translation="",
    )
    assert "Text to translate:" in prompt
    assert "שלום" in prompt
    assert "Your previous translation attempt was reviewed" not in prompt
    assert "Previous translation:" not in prompt


def test_build_user_prompt_ignores_feedback_without_previous_translation() -> None:
    prompt = _build_user_prompt(
        text="שלום",
        feedback="Use a more natural phrasing.",
        previous_translation="",
    )
    assert "Text to translate:" in prompt
    assert "שלום" in prompt
    assert "Your previous translation attempt was reviewed" not in prompt


def test_build_user_prompt_includes_feedback_and_previous_translation() -> None:
    prompt = _build_user_prompt(
        text="שלום",
        feedback="Use a more natural phrasing.",
        previous_translation="Hello",
    )
    assert "Your previous translation attempt was reviewed" in prompt
    assert "Use a more natural phrasing." in prompt
    assert "Previous translation:" in prompt
    assert "Hello" in prompt
    assert "Text to translate:" in prompt
    assert "שלום" in prompt
