"""Tests for AWS utility functions."""

import re

from agent.utils.aws import extract_year_month_from_iso, get_current_timestamp


class TestGetCurrentTimestamp:
    """Tests for get_current_timestamp function."""

    def test_returns_iso_8601_format(self) -> None:
        timestamp = get_current_timestamp()
        # Should match pattern like "2026-01-31T12:30:45Z"
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        assert re.match(pattern, timestamp) is not None

    def test_returns_string(self) -> None:
        timestamp = get_current_timestamp()
        assert isinstance(timestamp, str)

    def test_has_correct_length(self) -> None:
        timestamp = get_current_timestamp()
        # "YYYY-MM-DDTHH:MM:SSZ" = 20 characters
        assert len(timestamp) == 20


class TestExtractYearMonthFromIso:
    """Tests for extract_year_month_from_iso function."""

    def test_extracts_year_month_from_valid_timestamp(self) -> None:
        assert extract_year_month_from_iso("2026-01-31T12:30:45Z") == "2026-01"

    def test_extracts_year_month_from_different_dates(self) -> None:
        assert extract_year_month_from_iso("2025-12-15T00:00:00Z") == "2025-12"
        assert extract_year_month_from_iso("2024-06-01T23:59:59Z") == "2024-06"

    def test_handles_edge_months(self) -> None:
        assert extract_year_month_from_iso("2026-01-01T00:00:00Z") == "2026-01"
        assert extract_year_month_from_iso("2026-12-31T23:59:59Z") == "2026-12"

    def test_returns_first_seven_characters(self) -> None:
        result = extract_year_month_from_iso("2026-01-31T12:30:45Z")
        assert len(result) == 7
