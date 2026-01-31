from __future__ import annotations

from agent.state import IncidentData
from agent.tools.send_email import (
    _build_html_email,
    _build_plain_text_email,
    _format_crime_type,
)


def test_format_crime_type_rock_throwing() -> None:
    """Test formatting rock_throwing crime type."""
    assert _format_crime_type("rock_throwing") == "Rock Throwing"


def test_format_crime_type_molotov_cocktail() -> None:
    """Test formatting molotov_cocktail crime type."""
    assert _format_crime_type("molotov_cocktail") == "Molotov Cocktail"


def test_format_crime_type_stabbing() -> None:
    """Test formatting stabbing crime type."""
    assert _format_crime_type("stabbing") == "Stabbing"


def test_format_crime_type_shooting() -> None:
    """Test formatting shooting crime type."""
    assert _format_crime_type("shooting") == "Shooting"


def test_format_crime_type_ramming() -> None:
    """Test formatting ramming crime type."""
    assert _format_crime_type("ramming") == "Ramming"


def test_format_crime_type_theft() -> None:
    """Test formatting theft crime type."""
    assert _format_crime_type("theft") == "Theft"


def test_build_html_email_contains_terror_alert() -> None:
    """Test that HTML email contains terror incident alert header."""
    incident: IncidentData = {
        "location": "Test Location",
        "crime": "rock_throwing",
    }

    html = _build_html_email(incident, "2026-01-31T12:00:00Z")
    assert "Terror Incident Alert" in html
    assert "⚠️" in html


def test_build_html_email_contains_incident_details() -> None:
    """Test that HTML email contains all incident details."""
    incident: IncidentData = {
        "location": "Jerusalem Central",
        "crime": "molotov_cocktail",
    }
    timestamp = "2026-01-31T12:00:00Z"

    html = _build_html_email(incident, timestamp)

    assert "Jerusalem Central" in html
    assert "Molotov Cocktail" in html
    assert timestamp in html


def test_build_html_email_structure() -> None:
    """Test that HTML email has proper structure and styling."""
    incident: IncidentData = {
        "location": "Test Location",
        "crime": "stabbing",
    }

    html = _build_html_email(incident, "2026-01-31T12:00:00Z")

    # Check for HTML structure
    assert "<!DOCTYPE html>" in html
    assert '<html lang="en">' in html
    assert "<head>" in html
    assert "<body" in html

    # Check for table structure
    assert "<table" in html
    assert "Location:" in html
    assert "Incident Type:" in html
    assert "Timestamp:" in html

    # Check for styling
    assert "background-color: #dc3545" in html  # Red header
    assert "font-family: Arial" in html


def test_build_plain_text_email_contains_terror_alert() -> None:
    """Test that plain text email contains terror incident alert header."""
    incident: IncidentData = {
        "location": "Test Location",
        "crime": "rock_throwing",
    }

    text = _build_plain_text_email(incident, "2026-01-31T12:00:00Z")
    assert "TERROR INCIDENT ALERT" in text
    assert "=====================" in text


def test_build_plain_text_email_contains_incident_details() -> None:
    """Test that plain text email contains all incident details."""
    incident: IncidentData = {
        "location": "Tel Aviv",
        "crime": "shooting",
    }
    timestamp = "2026-01-31T12:00:00Z"

    text = _build_plain_text_email(incident, timestamp)

    assert "Tel Aviv" in text
    assert "Shooting" in text
    assert timestamp in text


def test_build_plain_text_email_structure() -> None:
    """Test that plain text email has proper structure."""
    incident: IncidentData = {
        "location": "Haifa",
        "crime": "ramming",
    }

    text = _build_plain_text_email(incident, "2026-01-31T12:00:00Z")

    # Check for section headers
    assert "INCIDENT DETAILS:" in text
    assert "-----------------" in text

    # Check for footer
    assert "Telegram Data Agent" in text
    assert "---" in text


def test_build_plain_text_email_with_special_characters() -> None:
    """Test that plain text email handles special characters in location."""
    incident: IncidentData = {
        "location": "Jerusalem - Old City",
        "crime": "theft",
    }

    text = _build_plain_text_email(incident, "2026-01-31T12:00:00Z")
    assert "Jerusalem - Old City" in text
    assert "Theft" in text


def test_build_html_email_with_special_characters() -> None:
    """Test that HTML email handles special characters in location."""
    incident: IncidentData = {
        "location": "Jerusalem - Old City",
        "crime": "theft",
    }

    html = _build_html_email(incident, "2026-01-31T12:00:00Z")
    assert "Jerusalem - Old City" in html
    assert "Theft" in html
