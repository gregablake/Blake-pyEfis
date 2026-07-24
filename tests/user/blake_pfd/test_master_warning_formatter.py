from pyefis.user.blake_pfd.master_warning import (
    format_ai_warning_text,
)


def test_formatter_includes_title_urgency_and_confidence() -> None:
    result = format_ai_warning_text(
        title="CHT Cooling Advisor",
        urgency_s=24.0,
        confidence=0.85,
    )

    assert result == (
        "AI CHT COOLING ADVISOR 24s 85%"
    )


def test_formatter_omits_missing_optional_values() -> None:
    result = format_ai_warning_text(
        title="Engine Trend",
    )

    assert result == "AI ENGINE TREND"


def test_formatter_clamps_negative_urgency() -> None:
    result = format_ai_warning_text(
        title="CHT",
        urgency_s=-4.0,
    )

    assert result == "AI CHT 0s"


def test_formatter_clamps_confidence_above_one() -> None:
    result = format_ai_warning_text(
        title="CHT",
        confidence=1.4,
    )

    assert result == "AI CHT 100%"


def test_formatter_clamps_negative_confidence() -> None:
    result = format_ai_warning_text(
        title="CHT",
        confidence=-0.4,
    )

    assert result == "AI CHT 0%"


def test_formatter_shortens_long_title() -> None:
    result = format_ai_warning_text(
        title=(
            "Extremely Long Predicted Engine "
            "Temperature Advisory"
        ),
        max_title_length=18,
    )

    assert result.startswith("AI ")
    assert "…" in result
    assert len(result.removeprefix("AI ")) == 18