"""Tests for DynamoDB helper functions."""

from agent.state import IncidentDataModel
from agent.tools.push_to_dynamodb import _generate_incident_id


class TestGenerateIncidentId:
    """Tests for _generate_incident_id function."""

    def test_generates_sha256_hash(self) -> None:
        incident = IncidentDataModel(location="Jerusalem", crime="rock_throwing")
        created_at = "2026-01-31T12:00:00Z"

        result = _generate_incident_id(incident, created_at)

        # SHA-256 hash is 64 hex characters
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_input_produces_same_hash(self) -> None:
        incident = IncidentDataModel(location="Jerusalem", crime="stabbing")
        created_at = "2026-01-31T12:00:00Z"

        result1 = _generate_incident_id(incident, created_at)
        result2 = _generate_incident_id(incident, created_at)

        assert result1 == result2

    def test_different_location_produces_different_hash(self) -> None:
        incident1 = IncidentDataModel(location="Jerusalem", crime="stabbing")
        incident2 = IncidentDataModel(location="Hebron", crime="stabbing")
        created_at = "2026-01-31T12:00:00Z"

        result1 = _generate_incident_id(incident1, created_at)
        result2 = _generate_incident_id(incident2, created_at)

        assert result1 != result2

    def test_different_crime_produces_different_hash(self) -> None:
        incident1 = IncidentDataModel(location="Jerusalem", crime="stabbing")
        incident2 = IncidentDataModel(location="Jerusalem", crime="shooting")
        created_at = "2026-01-31T12:00:00Z"

        result1 = _generate_incident_id(incident1, created_at)
        result2 = _generate_incident_id(incident2, created_at)

        assert result1 != result2

    def test_different_timestamp_produces_different_hash(self) -> None:
        incident = IncidentDataModel(location="Jerusalem", crime="stabbing")

        result1 = _generate_incident_id(incident, "2026-01-31T12:00:00Z")
        result2 = _generate_incident_id(incident, "2026-01-31T12:00:01Z")

        assert result1 != result2
