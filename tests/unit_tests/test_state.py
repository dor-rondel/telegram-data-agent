"""Tests for State type definitions."""

from agent.state import IncidentCrime, IncidentData


class TestIncidentCrime:
    """Tests for IncidentCrime type alias."""

    def test_valid_crime_types(self) -> None:
        valid_crimes: list[IncidentCrime] = [
            "rock_throwing",
            "molotov_cocktail",
            "ramming",
            "stabbing",
            "shooting",
            "theft",
        ]
        # This just verifies the type alias accepts these values
        assert len(valid_crimes) == 6


class TestIncidentData:
    """Tests for IncidentData TypedDict."""

    def test_can_create_incident_data(self) -> None:
        incident: IncidentData = {
            "location": "Jerusalem",
            "crime": "rock_throwing",
        }
        assert incident["location"] == "Jerusalem"
        assert incident["crime"] == "rock_throwing"

    def test_incident_data_is_dict(self) -> None:
        incident: IncidentData = {
            "location": "Hebron",
            "crime": "stabbing",
        }
        assert isinstance(incident, dict)
