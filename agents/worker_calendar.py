"""
Calendar Worker Agent - Specialized agent for fetching calendar events.

This worker agent wraps the calendar adapter as a tool and can be called
by the Orchestrator agent using the Agents-as-Tools pattern.
"""

import sys
from pathlib import Path

# Add project root to sys.path for absolute imports
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Agent-specific model and region constants
CALENDAR_MODEL_ID = "eu.amazon.nova-lite-v1:0"
CALENDAR_REGION = "eu-central-1"

from strands import Agent, tool
from strands.models import BedrockModel

from tools.calendar_adapter import (CalendarAdapter, list_todays_meetings,
                                    update_event_agenda)


@tool
def get_todays_calendar_events() -> dict:
    """
    Retrieve all calendar events scheduled for today.

    Returns meetings and appointments with complete details including:
    - Meeting titles and descriptions
    - Start and end times
    - Attendee lists
    - Locations (physical or virtual)

    Use this to understand the user's daily schedule and time commitments.

    Returns:
        Dictionary containing today's calendar events with full metadata
    """
    return list_todays_meetings()


@tool
def get_event_details(title: str) -> dict:
    """
    Retrieve comprehensive details for a specific calendar event by title.

    Use this when you need complete information about a particular meeting,
    including attendees, location, description, and timing details.

    Args:
        title: Exact or partial title of the event (case-insensitive)

    Returns:
        Dictionary with full event details or error if event not found
    """
    adapter = CalendarAdapter()
    events = adapter.get_todays_events()
    for event in events:
        if event.title.strip().lower() == title.strip().lower():
            d = event.model_dump()
            d["start"] = event.start.isoformat()
            d["end"] = event.end.isoformat()
            return {"event": d}
    return {"error": f"No event found with title '{title}' for today."}


@tool
def set_event_agenda(event_title: str, agenda: str) -> dict:
    """
    Add or update the agenda/description for a calendar event.

    Use this when the user wants to prepare for a meeting by setting
    topics, discussion points, or action items in advance.

    Args:
        event_title: Title or partial title of the meeting to update
        agenda: Agenda content to add to the event description

    Returns:
        Dictionary with success status and confirmation message
    """
    return update_event_agenda(event_title, agenda)


def create_calendar_worker_agent(*args, **kwargs):
    """
    Create a calendar worker agent using agent-specific model and region constants.

    Returns:
        Agent instance for calendar operations
    """
    # Use agent-specific constants for model and region
    bedrock_model = BedrockModel(
        model_id=CALENDAR_MODEL_ID,
        region_name=CALENDAR_REGION,
        temperature=0.2,  # Low creativity for factual calendar data
        streaming=False,
    )

    # Create agent with calendar tools
    agent = Agent(
        model=bedrock_model,
        name="calendar_worker",
        tools=[get_todays_calendar_events, get_event_details, set_event_agenda],
        system_prompt="""You are a Calendar Worker Agent specialized in schedule management.

Provide clear, actionable calendar information:
- Present events chronologically with times
- Highlight conflicts and overlapping meetings
- Include attendee information for coordination
- Note virtual vs. physical locations

Be concise and focus on helping users manage their time effectively.""",
    )

    return agent


if __name__ == "__main__":
    # Test the Calendar Worker Agent
    agent = create_calendar_worker_agent()
    response = agent("What meetings do I have today?")
    print(response)
