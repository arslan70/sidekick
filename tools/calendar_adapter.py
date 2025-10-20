"""
Google Calendar adapter for MVP.

Provides a simple interface to fetch calendar events.
Currently uses local data files. Can be extended for real Google Calendar API.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from tools.schemas import CalendarEvent

logger = logging.getLogger(__name__)


class CalendarAdapter:
    """Adapter for Google Calendar."""

    def __init__(self):
        """
        Initialize the calendar adapter.

        Automatically detects if Google Calendar credentials are available.
        Falls back to static demo data if credentials are not configured.
        """
        self.data_path = Path(__file__).parent.parent / "configs" / "calendar_data.json"
        self.calendar_service = None
        self.use_static_data = True  # Default to True for demo

        # Try to initialize Google Calendar API
        if self._has_credentials():
            try:
                self.calendar_service = self._initialize_google_calendar()
                self.use_static_data = False
                logger.info("Calendar adapter initialized with Google Calendar API")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Google Calendar API, using static data: {e}"
                )
                self.use_static_data = True
        else:
            logger.info(
                "Calendar adapter initialized with static data (no credentials configured)"
            )

    def _has_credentials(self) -> bool:
        """
        Check if Google Calendar credentials are available.

        Returns:
            True if credentials are found, False otherwise.
        """
        # Check for credentials file or OAuth tokens
        creds_path = Path.home() / ".credentials" / "calendar_credentials.json"
        token_path = Path.home() / ".credentials" / "calendar_token.json"
        return creds_path.exists() or token_path.exists()

    def _initialize_google_calendar(self):
        """
        Initialize Google Calendar API client.

        Returns:
            Google Calendar service object.

        Raises:
            Exception: If initialization fails.
        """
        # Placeholder for future Google Calendar API integration
        # This would use google-auth and google-api-python-client
        raise NotImplementedError("Google Calendar API integration not yet implemented")

    def get_todays_events(self) -> List[CalendarEvent]:
        """
        Fetch today's calendar events.

        Returns:
            List of CalendarEvent objects for today.
        """
        # Check if data file exists
        if self.data_path.exists():
            with open(self.data_path, "r") as f:
                data = json.load(f)
                return [CalendarEvent(**event) for event in data.get("events", [])]

        # Generate sample events for today only if calendar_data.json doesn't exist
        # This is demo data for demonstration purposes
        logger.info("Generating sample calendar events (demo data)")
        now = datetime.now()
        today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
        today_10am = now.replace(hour=10, minute=0, second=0, microsecond=0)
        today_2pm = now.replace(hour=14, minute=0, second=0, microsecond=0)
        today_4pm = now.replace(hour=16, minute=0, second=0, microsecond=0)

        sample_events = [
            CalendarEvent(
                title="Daily Standup",
                start=today_9am,
                end=today_9am + timedelta(minutes=30),
                attendees=["team@company.com", "manager@company.com"],
                location="Virtual (Zoom)",
                description="Daily team sync-up",
            ),
            CalendarEvent(
                title="Sprint Planning",
                start=today_10am,
                end=today_10am + timedelta(hours=2),
                attendees=["team@company.com", "po@company.com"],
                location="Conference Room A",
                description="Planning for Sprint 42",
            ),
            CalendarEvent(
                title="Client Demo",
                start=today_2pm,
                end=today_2pm + timedelta(hours=1),
                attendees=["client@external.com", "sales@company.com"],
                location="Virtual (Teams)",
                description="Demo of new features for Q4 release",
            ),
            CalendarEvent(
                title="Team Retrospective",
                start=today_4pm,
                end=today_4pm + timedelta(minutes=45),
                attendees=["team@company.com"],
                location="Virtual (Zoom)",
                description="Sprint 41 retrospective",
            ),
        ]

        return sample_events

    def update_event_description(self, event_title: str, new_description: str) -> bool:
        """
        Update the description/agenda of an event.

        Args:
            event_title: Title of the event to update (case-insensitive partial match).
            new_description: New description/agenda to set.

        Returns:
            True if event was found and updated, False otherwise.
        """
        if not self.data_path.exists():
            return False

        with open(self.data_path, "r") as f:
            data = json.load(f)

        # Support both {"events": [...]} and [...] structures
        if isinstance(data, dict) and "events" in data:
            events = data["events"]
            is_dict = True
        elif isinstance(data, list):
            events = data
            is_dict = False
        else:
            return False

        updated = False
        for event_data in events:
            event_name = event_data.get("title") or event_data.get("summary", "")
            if event_title.lower() in event_name.lower():
                event_data["description"] = new_description
                updated = True
                break

        if updated:
            # Write back in the same structure
            with open(self.data_path, "w") as f:
                if is_dict:
                    json.dump({"events": events}, f, indent=2, default=str)
                else:
                    json.dump(events, f, indent=2, default=str)
            return True
        return False

    def format_events_for_display(self, events: List[CalendarEvent]) -> str:
        """
        Format events for readable display.

        Args:
            events: List of CalendarEvent objects.

        Returns:
            Formatted string representation of events.
        """
        if not events:
            return "No events scheduled for today."

        formatted = ["**Today's Calendar Events:**\n"]

        for i, event in enumerate(events, 1):
            formatted.append(f"{i}. **{event.title}**")
            formatted.append(
                f"   - Time: {event.start.strftime('%I:%M %p')} - {event.end.strftime('%I:%M %p')}"
            )
            if event.location:
                formatted.append(f"   - Location: {event.location}")
            if event.attendees:
                formatted.append(f"   - Attendees: {len(event.attendees)} person(s)")
            if event.description:
                formatted.append(f"   - Description: {event.description}")
            formatted.append("")

        return "\n".join(formatted)


def list_todays_meetings() -> dict:
    """
    Tool function to list today's meetings.
    Compatible with StrandsAgents tool interface.

    Returns:
        Dictionary with status and content.
    """
    try:
        adapter = CalendarAdapter()
        events = adapter.get_todays_events()

        def event_to_dict(event):
            d = event.model_dump()
            d["start"] = event.start.isoformat()
            d["end"] = event.end.isoformat()
            return d

        return {"events": [event_to_dict(event) for event in events]}
    except Exception as e:
        return {"events": [], "error": f"Failed to fetch calendar events: {str(e)}"}


def update_event_agenda(event_title: str, agenda: str) -> dict:
    """
    Update the agenda/description of a calendar event.
    Compatible with StrandsAgents tool interface.

    Args:
        event_title: Title or partial title of the event to update.
        agenda: New agenda/description content to set for the event.

    Returns:
        Dictionary with success status and message.
    """
    try:
        adapter = CalendarAdapter()
        success = adapter.update_event_description(event_title, agenda)

        if success:
            return {
                "success": True,
                "message": f"Successfully updated agenda for event matching '{event_title}'",
            }
        else:
            return {
                "success": False,
                "message": f"No event found matching '{event_title}'",
            }
    except Exception as e:
        return {"success": False, "error": f"Failed to update event: {str(e)}"}
