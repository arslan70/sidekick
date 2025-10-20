"""
Email Worker Agent - Specialized agent for email management.

Handles fetching, summarizing, and extracting action items from emails.
Can be called by the Orchestrator using Agents-as-Tools pattern.
"""

import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

# Agent-specific model and region constants
EMAIL_MODEL_ID = "eu.amazon.nova-lite-v1:0"
EMAIL_REGION = "eu-central-1"

from email_adapter import (extract_action_items_from_email,
                           fetch_recent_emails, fetch_urgent_emails,
                           set_action_intelligence_agent)
from strands import Agent, tool
from strands.models import BedrockModel


@tool
def get_recent_emails(limit: int = 10) -> dict:
    """
    Retrieve the user's most recent emails from their inbox.

    Returns email summaries with sender, subject, preview, and timestamp.
    Use this to get an overview of recent communications.

    Args:
        limit: Maximum number of emails to retrieve (default: 10, max: 50)

    Returns:
        Dictionary with email metadata and preview content
    """
    return fetch_recent_emails(limit=limit)


@tool
def get_urgent_emails() -> dict:
    """
    Retrieve only urgent or high-priority emails requiring immediate attention.

    Returns emails marked as urgent, flagged, or from important senders.
    Use this to identify time-sensitive communications that need quick response.

    Returns:
        Dictionary with urgent email summaries prioritized by importance
    """
    return fetch_urgent_emails()


@tool
def extract_email_action_items(email_id: str) -> dict:
    """
    Extract actionable tasks and deadlines from a specific email.

    Analyzes email content to identify:
    - Requested actions and tasks
    - Deadlines and due dates
    - Required responses or deliverables

    Use this to convert emails into trackable action items.

    Args:
        email_id: Unique identifier of the email to analyze

    Returns:
        Dictionary with extracted action items, deadlines, and priority levels
    """
    return extract_action_items_from_email(email_id)


def create_email_worker_agent(*args, **kwargs):
    """
    Create an email worker agent using agent-specific model and region constants.
    """
    # Create action intelligence agent and set it globally
    try:
        from worker_email_actions import create_email_action_intelligence_agent

        action_agent = create_email_action_intelligence_agent()
        set_action_intelligence_agent(action_agent)
    except ImportError:
        print("Warning: Could not import email action intelligence agent")

    # Use agent-specific constants for model and region
    bedrock_model = BedrockModel(
        model_id=EMAIL_MODEL_ID,
        region_name=EMAIL_REGION,
        temperature=0.2,  # Low creativity for factual email processing
        streaming=False,
    )

    # Create agent with email tools
    agent = Agent(
        model=bedrock_model,
        name="email_worker",
        tools=[get_recent_emails, get_urgent_emails, extract_email_action_items],
        system_prompt="""You are an Email Worker Agent specialized in inbox management and communication analysis.

Provide actionable email insights:
- Prioritize by urgency and importance
- Highlight urgent items with indicators
- Extract key information: sender, subject, action items
- Identify deadlines and response requirements

Be efficient and help users quickly process their inbox.""",
    )

    return agent


if __name__ == "__main__":
    # Test the Email Worker Agent
    agent = create_email_worker_agent()
    response = agent("What urgent emails do I have?")
    print(response)
