"""DynamoDB upsert tool for storing incident data organized by month.

Incidents are stored in monthly partitions (e.g., "2026-01") with idempotent
upserts using a hashed incident ID to prevent duplicates.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.exceptions import ClientError

from agent.state import IncidentData

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 1.0


def _generate_incident_id(incident: IncidentData) -> str:
    """Generate a unique incident ID by hashing location, crime, and timestamp.

    Args:
        incident: The incident data to generate an ID for.

    Returns:
        A SHA-256 hash string uniquely identifying the incident.
    """
    key_string = f"{incident['location']}:{incident['crime']}:{incident['created_at']}"
    return hashlib.sha256(key_string.encode()).hexdigest()


def _extract_year_month(unix_timestamp: int) -> str:
    """Extract year-month string from Unix timestamp.

    Args:
        unix_timestamp: Unix timestamp in seconds.

    Returns:
        Year-month string in format "YYYY-MM" (e.g., "2026-01").
    """
    dt = datetime.fromtimestamp(unix_timestamp, tz=UTC)
    return dt.strftime("%Y-%m")


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


def _execute_with_retry(operation: Any, operation_name: str) -> Any:
    """Execute a DynamoDB operation with retry logic for transient errors.

    Retries on transient errors with exponential backoff.
    ServiceUnavailable errors are logged and raised immediately without retry.

    Args:
        operation: A callable that performs the DynamoDB operation.
        operation_name: Human-readable name for logging purposes.

    Returns:
        The result of the operation.

    Raises:
        ClientError: If a non-retryable error occurs or all retries are exhausted.
    """
    last_exception: ClientError | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return operation()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")

            if error_code == "ServiceUnavailable":
                logger.error(
                    "DynamoDB %s failed with ServiceUnavailable (no retry): %s",
                    operation_name,
                    str(e),
                )
                raise

            last_exception = e
            delay = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "DynamoDB %s attempt %d/%d failed with %s. Retrying in %.1f seconds...",
                operation_name,
                attempt,
                MAX_RETRIES,
                error_code,
                delay,
            )
            time.sleep(delay)

    logger.error(
        "DynamoDB %s failed after %d retries: %s",
        operation_name,
        MAX_RETRIES,
        str(last_exception),
    )
    raise last_exception  # type: ignore[misc]


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
    year_month = _extract_year_month(incident["created_at"])
    incident_id = _generate_incident_id(incident)

    logger.info(
        "Upserting incident to DynamoDB: year_month=%s, incident_id=%s",
        year_month,
        incident_id,
    )

    table = _get_dynamodb_table()

    # Build the incident entry with its ID
    incident_entry = {
        "incident_id": incident_id,
        "location": incident["location"],
        "crime": incident["crime"],
        "created_at": incident["created_at"],
    }

    # Check if monthly partition exists and if incident is a duplicate
    def get_existing_item() -> dict[str, Any] | None:
        response = table.get_item(Key={"year_month": year_month})
        return response.get("Item")

    existing_item = _execute_with_retry(get_existing_item, "get_item")

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
                Key={"year_month": year_month},
                UpdateExpression="SET incidents = list_append(incidents, :new_incident)",
                ExpressionAttributeValues={":new_incident": [incident_entry]},
            )

        _execute_with_retry(update_item, "update_item")
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
                    "year_month": year_month,
                    "incidents": [incident_entry],
                }
            )

        _execute_with_retry(put_item, "put_item")
        logger.info(
            "Created new partition with incident: year_month=%s, incident_id=%s",
            year_month,
            incident_id,
        )

    return {
        "ok": True,
    }
