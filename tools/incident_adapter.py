"""
Incident adapter for MVP.

Provides interface to fetch and process incidents.
Uses static demo data from configs/incident_data.json for demonstration purposes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from tools.schemas import Incident


class IncidentAdapter:
    """
    Adapter for incident management.

    This adapter uses static demo data for demonstration purposes.
    In a production environment, this would connect to a real incident management system.
    """

    def __init__(self):
        """
        Initialize the incident adapter.

        Uses static demo data from configs/incident_data.json.
        """
        self.data_path = Path(__file__).parent.parent / "configs" / "incident_data.json"

    def get_all_incidents(self, limit: int = 50) -> List[Incident]:
        """
        Fetch all incidents.

        Args:
            limit: Maximum number of incidents to return

        Returns:
            List of Incident objects.
        """
        if self.data_path.exists():
            with open(self.data_path, "r") as f:
                data = json.load(f)
                incidents = []
                for incident_data in data.get("incidents", [])[:limit]:
                    # Parse timestamps
                    incident_data["reported_at"] = datetime.fromisoformat(
                        incident_data["reported_at"]
                    )
                    if incident_data.get("resolved_at"):
                        incident_data["resolved_at"] = datetime.fromisoformat(
                            incident_data["resolved_at"]
                        )
                    incidents.append(Incident(**incident_data))
                return incidents
        return []

    def get_open_incidents(self) -> List[Incident]:
        """
        Fetch only open/active incidents.

        Returns:
            List of open Incident objects.
        """
        all_incidents = self.get_all_incidents(limit=100)
        return [
            incident
            for incident in all_incidents
            if incident.status in ["Open", "In Progress"]
        ]

    def get_critical_incidents(self) -> List[Incident]:
        """
        Fetch only critical severity incidents.

        Returns:
            List of critical Incident objects.
        """
        all_incidents = self.get_all_incidents(limit=100)
        return [
            incident for incident in all_incidents if incident.severity == "Critical"
        ]

    def get_incident_by_id(self, incident_id: str) -> Optional[Incident]:
        """
        Fetch a specific incident by ID.

        Args:
            incident_id: The incident ID to fetch

        Returns:
            Incident object if found, None otherwise.
        """
        all_incidents = self.get_all_incidents(limit=100)
        return next((inc for inc in all_incidents if inc.id == incident_id), None)

    def get_incident_by_title(self, title_keyword: str) -> Optional[Incident]:
        """
        Find an incident by searching for a keyword in the title.

        Args:
            title_keyword: Keyword to search for in incident titles

        Returns:
            First matching Incident object if found, None otherwise.
        """
        all_incidents = self.get_all_incidents(limit=100)
        title_keyword_lower = title_keyword.lower()
        return next(
            (inc for inc in all_incidents if title_keyword_lower in inc.title.lower()),
            None,
        )

    def get_incidents_by_email(self, email_id: str) -> List[Incident]:
        """
        Get incidents related to a specific email.

        Args:
            email_id: Email ID to search for

        Returns:
            List of related Incident objects.
        """
        all_incidents = self.get_all_incidents(limit=100)
        return [inc for inc in all_incidents if inc.related_email_id == email_id]

    def format_incident_summary(self, incident: Incident) -> str:
        """
        Format a single incident for readable display.

        Args:
            incident: Incident object to format

        Returns:
            Formatted string representation.
        """
        severity_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}

        status_emoji = {"Open": "🆕", "In Progress": "⚙️", "Resolved": "✅"}

        lines = []
        lines.append(
            f"{severity_emoji.get(incident.severity, '⚪')} {status_emoji.get(incident.status, '❓')} **{incident.title}**"
        )
        lines.append(f"   ID: {incident.id}")
        lines.append(f"   Status: {incident.status} | Severity: {incident.severity}")
        lines.append(
            f"   Reported: {incident.reported_at.strftime('%Y-%m-%d %I:%M %p')} by {incident.reported_by}"
        )

        if incident.assigned_to:
            lines.append(f"   Assigned to: {incident.assigned_to}")

        if incident.resolved_at:
            lines.append(
                f"   Resolved: {incident.resolved_at.strftime('%Y-%m-%d %I:%M %p')}"
            )

        lines.append(f"   Impact: {incident.impact}")

        if incident.affected_services:
            lines.append(
                f"   Affected Services: {', '.join(incident.affected_services[:3])}"
            )
            if len(incident.affected_services) > 3:
                lines.append(f"      ...and {len(incident.affected_services) - 3} more")

        return "\n".join(lines)

    def format_incident_details(self, incident: Incident) -> str:
        """
        Format full incident details for display.

        Args:
            incident: Incident object to format

        Returns:
            Detailed formatted string representation.
        """
        severity_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}

        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(
            f"{severity_emoji.get(incident.severity, '⚪')} **INCIDENT: {incident.title}**"
        )
        lines.append(f"{'='*60}\n")

        lines.append(f"**ID:** {incident.id}")
        lines.append(f"**Status:** {incident.status}")
        lines.append(f"**Severity:** {incident.severity}")
        lines.append(
            f"**Reported:** {incident.reported_at.strftime('%Y-%m-%d %I:%M %p')} by {incident.reported_by}"
        )

        if incident.assigned_to:
            lines.append(f"**Assigned to:** {incident.assigned_to}")

        if incident.resolved_at:
            lines.append(
                f"**Resolved:** {incident.resolved_at.strftime('%Y-%m-%d %I:%M %p')}"
            )

        lines.append(f"\n**Impact:**\n{incident.impact}")

        if incident.affected_services:
            lines.append("\n**Affected Services:**")
            for service in incident.affected_services:
                lines.append(f"  - {service}")

        lines.append(f"\n**Description:**\n{incident.description}")

        if incident.root_cause:
            lines.append(f"\n**Root Cause:**\n{incident.root_cause}")

        if incident.resolution:
            lines.append(f"\n**Resolution:**\n{incident.resolution}")

        if incident.timeline:
            lines.append("\n**Timeline:**")
            for event in incident.timeline:
                lines.append(f"  • {event}")

        if incident.related_email_id:
            lines.append(f"\n**Related Email:** {incident.related_email_id}")

        lines.append(f"\n{'='*60}")

        return "\n".join(lines)

    def format_incidents_for_display(self, incidents: List[Incident]) -> str:
        """Format multiple incidents for readable display."""
        if not incidents:
            return "No incidents found."

        formatted = [f"**{len(incidents)} Incident(s):**\n"]

        for i, incident in enumerate(incidents, 1):
            formatted.append(f"{i}. {self.format_incident_summary(incident)}")
            formatted.append("")

        return "\n".join(formatted)


def fetch_all_incidents(limit: int = 50) -> dict:
    """
    Tool function to fetch all incidents.
    Compatible with StrandsAgents tool interface.
    """
    try:
        adapter = IncidentAdapter()
        incidents = adapter.get_all_incidents(limit=limit)

        return {
            "incidents": [incident.model_dump(mode="json") for incident in incidents]
        }
    except Exception as e:
        return {"error": f"Failed to fetch incidents: {str(e)}"}


def fetch_open_incidents() -> dict:
    """Tool function to fetch open/active incidents."""
    try:
        adapter = IncidentAdapter()
        incidents = adapter.get_open_incidents()

        return {
            "incidents": [incident.model_dump(mode="json") for incident in incidents]
        }
    except Exception as e:
        return {"error": f"Failed to fetch open incidents: {str(e)}"}


def fetch_critical_incidents() -> dict:
    """Tool function to fetch critical severity incidents."""
    try:
        adapter = IncidentAdapter()
        incidents = adapter.get_critical_incidents()

        return {
            "incidents": [incident.model_dump(mode="json") for incident in incidents]
        }
    except Exception as e:
        return {"error": f"Failed to fetch critical incidents: {str(e)}"}


def fetch_incident_details(incident_id: str) -> dict:
    """
    Tool function to fetch details of a specific incident by ID.

    Args:
        incident_id: The incident ID to fetch

    Returns:
        Dictionary with incident details.
    """
    try:
        adapter = IncidentAdapter()
        incident = adapter.get_incident_by_id(incident_id)

        if not incident:
            return {"error": f"Incident {incident_id} not found"}

        return {"incident": incident.model_dump(mode="json")}
    except Exception as e:
        return {"error": f"Failed to fetch incident details: {str(e)}"}


def search_incident_by_title(title_keyword: str) -> dict:
    """
    Tool function to search for an incident by title keyword.

    Args:
        title_keyword: Keyword to search for in incident titles

    Returns:
        Dictionary with incident details if found.
    """
    try:
        adapter = IncidentAdapter()
        incident = adapter.get_incident_by_title(title_keyword)

        if not incident:
            return {"error": f"No incident found matching '{title_keyword}'"}

        return {"incident": incident.model_dump(mode="json")}
    except Exception as e:
        return {"error": f"Failed to search incidents: {str(e)}"}


def fetch_incidents_by_email(email_id: str) -> dict:
    """
    Tool function to fetch incidents related to a specific email.

    Args:
        email_id: Email ID to search for

    Returns:
        Dictionary with related incidents.
    """
    try:
        adapter = IncidentAdapter()
        incidents = adapter.get_incidents_by_email(email_id)

        return {
            "incidents": [incident.model_dump(mode="json") for incident in incidents],
            "email_id": email_id,
        }
    except Exception as e:
        return {"error": f"Failed to fetch incidents for email: {str(e)}"}
