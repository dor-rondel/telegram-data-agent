"""Tools exposed to the ReAct agent.

Each tool is a stub (no real side effects). Replace implementations later.
"""

from agent.tools.push_to_dynamodb import push_to_dynamodb
from agent.tools.send_email import send_email

TOOLS = [send_email, push_to_dynamodb]

__all__ = ["TOOLS", "push_to_dynamodb", "send_email"]
