"""AWS utility functions shared across tools.

Provides common functionality for AWS service interactions including
retry logic and timestamp formatting.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Callable, TypeVar

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 1.0

T = TypeVar("T")


def get_current_timestamp() -> str:
    """Get current UTC timestamp as ISO 8601 string.

    Returns:
        ISO 8601 formatted timestamp string (e.g., "2026-01-31T12:30:45Z").
    """
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_year_month_from_iso(iso_timestamp: str) -> str:
    """Extract year-month string from ISO 8601 timestamp.

    Args:
        iso_timestamp: ISO 8601 formatted timestamp string.

    Returns:
        Year-month string in format "YYYY-MM" (e.g., "2026-01").
    """
    return iso_timestamp[:7]


def execute_with_retry(
    operation: Callable[[], T],
    operation_name: str,
    *,
    raise_on_service_unavailable: bool = True,
) -> T | None:
    """Execute an AWS operation with retry logic for transient errors.

    Retries on transient errors with exponential backoff.

    Args:
        operation: A callable that performs the AWS operation.
        operation_name: Human-readable name for logging purposes.
        raise_on_service_unavailable: If True, raises on ServiceUnavailable.
            If False, logs error and returns None.

    Returns:
        The result of the operation, or None if ServiceUnavailable and
        raise_on_service_unavailable is False.

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
                    "%s failed with ServiceUnavailable: %s",
                    operation_name,
                    str(e),
                )
                if raise_on_service_unavailable:
                    raise
                return None

            last_exception = e
            delay = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "%s attempt %d/%d failed with %s. Retrying in %.1f seconds...",
                operation_name,
                attempt,
                MAX_RETRIES,
                error_code,
                delay,
            )
            time.sleep(delay)

    logger.error(
        "%s failed after %d retries: %s",
        operation_name,
        MAX_RETRIES,
        str(last_exception),
    )
    raise last_exception  # type: ignore[misc]
