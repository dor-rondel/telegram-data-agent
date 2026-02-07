"""Tools available to the worker agent.

Each tool accepts an IncidentDataModel and returns a result dict.
"""

from agent.tools.push_to_dynamodb import push_to_dynamodb
from agent.tools.send_email import send_email

TOOLS = [send_email, push_to_dynamodb]

__all__ = ["TOOLS", "push_to_dynamodb", "send_email"]
