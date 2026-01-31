"""SES email tool for sending terror incident alert notifications.

Uses AWS SES to send styled HTML emails notifying recipients of terror
incidents with full incident details.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from agent.state import IncidentData

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 1.0


def _get_ses_client() -> Any:
    """Get SES client from environment configuration.

    Returns:
        boto3 SES client.

    Raises:
        KeyError: If required environment variables are not set.
    """
    return boto3.client(
        "ses",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )


def _format_crime_type(crime: str) -> str:
    """Format crime type for human-readable display.

    Args:
        crime: The crime type identifier (e.g., "rock_throwing").

    Returns:
        Human-readable crime type (e.g., "Rock Throwing").
    """
    return crime.replace("_", " ").title()


def _build_html_email(incident: IncidentData) -> str:
    """Build styled HTML email body for terror incident alert.

    Args:
        incident: The incident data to include in the email.

    Returns:
        HTML-formatted email body string.
    """
    crime_display = _format_crime_type(incident["crime"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terror Incident Alert</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">⚠️ Terror Incident Alert</h1>
    </div>
    <div style="background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 5px 5px;">
        <p style="margin-top: 0;">A terror incident has been reported and requires your attention.</p>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #dee2e6; font-weight: bold; width: 30%;">Location:</td>
                <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{incident["location"]}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Incident Type:</td>
                <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{crime_display}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Timestamp:</td>
                <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{incident["created_at"]}</td>
            </tr>
        </table>
        <p style="margin-bottom: 0; font-size: 12px; color: #6c757d;">
            This is an automated alert from the Telegram Data Agent.
        </p>
    </div>
</body>
</html>"""


def _build_plain_text_email(incident: IncidentData) -> str:
    """Build plain text email body for terror incident alert.

    Args:
        incident: The incident data to include in the email.

    Returns:
        Plain text email body string.
    """
    crime_display = _format_crime_type(incident["crime"])

    return f"""TERROR INCIDENT ALERT
=====================

A terror incident has been reported and requires your attention.

INCIDENT DETAILS:
-----------------
Location: {incident["location"]}
Incident Type: {crime_display}
Timestamp: {incident["created_at"]}

---
This is an automated alert from the Telegram Data Agent."""


def _execute_with_retry(operation: Any, operation_name: str) -> Any:
    """Execute an SES operation with retry logic for transient errors.

    Retries on transient errors with exponential backoff.
    ServiceUnavailable errors are logged and return None immediately without retry.

    Args:
        operation: A callable that performs the SES operation.
        operation_name: Human-readable name for logging purposes.

    Returns:
        The result of the operation, or None if ServiceUnavailable.

    Raises:
        ClientError: If a non-retryable, non-ServiceUnavailable error occurs
            or all retries are exhausted.
    """
    last_exception: ClientError | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return operation()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")

            if error_code == "ServiceUnavailable":
                logger.error(
                    "SES %s failed with ServiceUnavailable (early return): %s",
                    operation_name,
                    str(e),
                )
                return None

            last_exception = e
            delay = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "SES %s attempt %d/%d failed with %s. Retrying in %.1f seconds...",
                operation_name,
                attempt,
                MAX_RETRIES,
                error_code,
                delay,
            )
            time.sleep(delay)

    logger.error(
        "SES %s failed after %d retries: %s",
        operation_name,
        MAX_RETRIES,
        str(last_exception),
    )
    raise last_exception  # type: ignore[misc]


def send_email(incident: IncidentData) -> dict[str, Any]:
    """Send a terror incident alert email via AWS SES.

    Sends a styled HTML email (with plain text fallback) to notify the
    configured recipient about a terror incident. Uses exponential backoff
    retry logic for transient errors.

    If the email fails to send after all retries or due to service
    unavailability, the function logs the error and returns success to
    avoid crashing the agent.

    Args:
        incident: The incident data to include in the alert email.

    Returns:
        A dictionary with operation result:
        - {"alert_complete": True, "message_id": str} on successful send
        - {"alert_complete": True, "error": str} if send failed but gracefully handled
    """
    sender_email = os.environ.get("SES_SENDER_EMAIL", "")
    recipient_email = os.environ.get("SES_RECIPIENT_EMAIL", "")

    if not sender_email or not recipient_email:
        error_msg = "SES_SENDER_EMAIL or SES_RECIPIENT_EMAIL not configured"
        logger.error(error_msg)
        return {"alert_complete": True, "error": error_msg}

    crime_display = _format_crime_type(incident["crime"])
    subject = f"Terror Incident Alert: {crime_display} at {incident['location']}"

    html_body = _build_html_email(incident)
    text_body = _build_plain_text_email(incident)

    logger.info(
        "Sending terror incident alert email to %s for incident at %s",
        recipient_email,
        incident["location"],
    )

    try:
        ses_client = _get_ses_client()

        def send_operation() -> dict[str, Any]:
            return ses_client.send_email(
                Source=sender_email,
                Destination={"ToAddresses": [recipient_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": text_body, "Charset": "UTF-8"},
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                },
            )

        result = _execute_with_retry(send_operation, "send_email")

        if result is None:
            # ServiceUnavailable case - early return without crashing
            return {
                "alert_complete": True,
                "error": "SES service unavailable",
            }

        message_id = result.get("MessageId", "unknown")
        logger.info(
            "Successfully sent terror incident alert email (MessageId: %s)",
            message_id,
        )
        return {"alert_complete": True, "message_id": message_id}

    except ClientError as e:
        # All retries exhausted - log error but don't crash
        error_msg = f"Failed to send email after {MAX_RETRIES} retries: {e}"
        logger.error(error_msg)
        return {"alert_complete": True, "error": error_msg}
