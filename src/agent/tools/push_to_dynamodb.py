"""DynamoDB upsert tool for storing incident data organized by month.

Incidents are stored in monthly partitions (e.g., "2026-01") with idempotent
upserts using a hashed incident ID to prevent duplicates.
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

import boto3

from agent.state import IncidentData
from agent.utils import (
    execute_with_retry,
    extract_year_month_from_iso,
    get_current_timestamp,
)

logger = logging.getLogger(__name__)


def _generate_incident_id(incident: IncidentData, created_at: str) -> str:
    """Generate a unique incident ID by hashing location, crime, and timestamp.

    Args:
        incident: The incident data to generate an ID for.
        created_at: ISO 8601 timestamp string for the incident.

    Returns:
        A SHA-256 hash string uniquely identifying the incident.
    """
    key_string = f"{incident['location']}:{incident['crime']}:{created_at}"
    return hashlib.sha256(key_string.encode()).hexdigest()


def _get_dynamodb_table() -> Any:
    """Get DynamoDB table resource from environment configuration.

    Returns:
        boto3 DynamoDB Table resource.

    Raises:
        KeyError: If DYNAMODB_TABLE_NAME environment variable is not set.
    """
    table_name = os.environ["DYNAMODB_TABLE_NAME"]
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )
    return dynamodb.Table(table_name)


def _get_partition_key_name() -> str:
    """Get DynamoDB partition key name from environment.

    Returns:
        Partition key attribute name (defaults to "year_month").
    """
    return os.environ.get("DYNAMODB_PARTITION_KEY", "year_month")


def push_to_dynamodb(incident: IncidentData) -> dict[str, Any]:
    """Upsert an incident to DynamoDB organized by year-month.

    Incidents are stored in monthly partitions with the partition key being
    the year-month (e.g., "2026-01"). Each incident is assigned a unique ID
    based on a hash of its location, crime type, and timestamp to ensure
    idempotent upserts.

    If the incident already exists in the monthly partition (based on its
    incident ID), the operation returns early without modification.

    Args:
        incident: The incident data to store.

    Returns:
        A dictionary with operation result:
        - {"ok": True, "year_month": str, "incident_id": str} on success
        - {"ok": True, "year_month": str, "incident_id": str, "duplicate": True}
          if incident already exists

    Raises:
        ClientError: If a DynamoDB operation fails after retries.
        KeyError: If required environment variables are not set.
    """
    created_at = get_current_timestamp()
    year_month = extract_year_month_from_iso(created_at)
    incident_id = _generate_incident_id(incident, created_at)

    logger.info(
        "Upserting incident to DynamoDB: year_month=%s, incident_id=%s",
        year_month,
        incident_id,
    )

    table = _get_dynamodb_table()
    partition_key = _get_partition_key_name()

    # Build the incident entry with its ID
    incident_entry = {
        "incident_id": incident_id,
        "location": incident["location"],
        "crime": incident["crime"],
        "created_at": created_at,
    }

    # Check if monthly partition exists and if incident is a duplicate
    def get_existing_item() -> dict[str, Any] | None:
        response = table.get_item(Key={partition_key: year_month})
        return response.get("Item")

    existing_item = execute_with_retry(get_existing_item, "DynamoDB get_item")

    if existing_item is not None:
        # Check for duplicate incident
        existing_incidents: list[dict[str, Any]] = existing_item.get("incidents", [])
        existing_ids = {inc.get("incident_id") for inc in existing_incidents}

        if incident_id in existing_ids:
            logger.info(
                "Duplicate incident detected, skipping: year_month=%s, incident_id=%s",
                year_month,
                incident_id,
            )
            return {
                "ok": True,
                "year_month": year_month,
                "incident_id": incident_id,
                "duplicate": True,
            }

        # Append to existing partition
        def update_item() -> None:
            table.update_item(
                Key={partition_key: year_month},
                UpdateExpression="SET incidents = list_append(incidents, :new_incident)",
                ExpressionAttributeValues={":new_incident": [incident_entry]},
            )

        execute_with_retry(update_item, "DynamoDB update_item")
        logger.info(
            "Appended incident to existing partition: year_month=%s, incident_id=%s",
            year_month,
            incident_id,
        )
    else:
        # Create new monthly partition
        def put_item() -> None:
            table.put_item(
                Item={
                    partition_key: year_month,
                    "incidents": [incident_entry],
                }
            )

        execute_with_retry(put_item, "DynamoDB put_item")
        logger.info(
            "Created new partition with incident: year_month=%s, incident_id=%s",
            year_month,
            incident_id,
        )

    return {
        "ok": True,
    }
