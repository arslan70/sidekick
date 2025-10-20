"""
Incident Worker Agent - Specialized agent for incident management.

Handles fetching, monitoring, and providing details about incidents.
Can be called by the Orchestrator using Agents-as-Tools pattern.
"""

import logging
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

# Agent-specific model constant
INCIDENT_MODEL_ID = "eu.amazon.nova-lite-v1:0"

from strands import Agent, tool
from strands.models import BedrockModel

# Configure logging for strands framework
logging.getLogger("strands").setLevel(
    logging.INFO
)  # Set to DEBUG for more detailed logs

# Configure logging for this module
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from incident_adapter import (fetch_all_incidents, fetch_critical_incidents,
                              fetch_incident_details, fetch_incidents_by_email,
                              fetch_open_incidents, search_incident_by_title)


@tool
def get_all_incidents(limit: int = 20) -> dict:
    """
    Retrieve all incidents in the system regardless of status.

    Returns comprehensive incident data including severity, status, and impact.
    Use this for broad incident visibility and historical tracking.

    Args:
        limit: Maximum number of incidents to retrieve (default: 20, max: 100)

    Returns:
        Dictionary with incident summaries, severity levels, and metadata
    """
    logger.info(f"Fetching all incidents with limit={limit}")
    try:
        result = fetch_all_incidents(limit=limit)
        logger.info(
            f"Successfully fetched {len(result.get('incidents', []))} incidents"
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching all incidents: {e}", exc_info=True)
        return {"error": f"Failed to fetch incidents: {str(e)}"}


@tool
def get_open_incidents() -> dict:
    """
    Retrieve only open/active incidents currently requiring attention.

    Returns incidents with status 'Open' or 'In Progress'.
    Use this to identify ongoing issues that need monitoring or resolution.

    Returns:
        Dictionary with active incident details prioritized by severity
    """
    logger.info("Fetching open incidents")
    try:
        result = fetch_open_incidents()
        logger.info(
            f"Successfully fetched {len(result.get('incidents', []))} open incidents"
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching open incidents: {e}", exc_info=True)
        return {"error": f"Failed to fetch open incidents: {str(e)}"}


@tool
def get_critical_incidents() -> dict:
    """
    Retrieve only critical severity incidents requiring immediate attention.

    Returns high-impact incidents affecting multiple users or critical systems.
    Use this to identify urgent issues that need escalation or immediate action.

    Returns:
        Dictionary with critical incident details, impact assessment, and status
    """
    logger.info("Fetching critical incidents")
    try:
        result = fetch_critical_incidents()
        logger.info(
            f"Successfully fetched {len(result.get('incidents', []))} critical incidents"
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching critical incidents: {e}", exc_info=True)
        return {"error": f"Failed to fetch critical incidents: {str(e)}"}


@tool
def get_incident_details(incident_id: str) -> dict:
    """
    Retrieve comprehensive details for a specific incident.

    Returns complete incident information including:
    - Timeline of events and updates
    - Root cause analysis (if available)
    - Affected services and user impact
    - Resolution steps and status
    - Assigned team and escalation path

    Use this for in-depth incident investigation and status updates.

    Args:
        incident_id: Unique incident identifier (e.g., 'INC-001', 'INC-042')

    Returns:
        Dictionary with full incident details, timeline, and resolution information
    """
    logger.info(f"Fetching incident details for: {incident_id}")
    try:
        result = fetch_incident_details(incident_id)
        logger.info(f"Successfully fetched details for {incident_id}")
        return result
    except Exception as e:
        logger.error(
            f"Error fetching incident details for {incident_id}: {e}", exc_info=True
        )
        return {"error": f"Failed to fetch incident details: {str(e)}"}


@tool
def search_incident(title_keyword: str) -> dict:
    """
    Search for incidents by keyword in title or description.

    Use this to find incidents related to specific services, errors, or symptoms.
    Helpful for identifying patterns or related incidents.

    Args:
        title_keyword: Search term to find in incident titles (e.g., "Database", "Login")

    Returns:
        Dictionary with matching incidents and relevance ranking
    """
    logger.info(f"Searching incidents with keyword: {title_keyword}")
    try:
        result = search_incident_by_title(title_keyword)
        logger.info("Search completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error searching incidents: {e}", exc_info=True)
        return {"error": f"Failed to search incidents: {str(e)}"}


@tool
def get_incidents_for_email(email_id: str) -> dict:
    """
    Retrieve incidents related to or mentioned in a specific email.

    Use this to correlate email notifications with incident tracking.
    Helpful when an urgent email references an ongoing incident.

    Args:
        email_id: Unique identifier of the email to find related incidents

    Returns:
        Dictionary with related incidents and correlation details
    """
    logger.info(f"Fetching incidents for email: {email_id}")
    try:
        result = fetch_incidents_by_email(email_id)
        logger.info(f"Successfully fetched incidents for email {email_id}")
        return result
    except Exception as e:
        logger.error(f"Error fetching incidents for email: {e}", exc_info=True)
        return {"error": f"Failed to fetch incidents for email: {str(e)}"}


def create_incident_worker_agent(*args, **kwargs):
    """
    Create and configure the Incident Worker Agent using agent-specific model constant.
    """
    logger.info("Creating Incident Worker Agent")

    model = BedrockModel(model_id=INCIDENT_MODEL_ID, temperature=0.2, streaming=False)
    agent = Agent(
        model=model,
        tools=[
            get_all_incidents,
            get_open_incidents,
            get_critical_incidents,
            get_incident_details,
            search_incident,
            get_incidents_for_email,
        ],
        system_prompt="""You are an Incident Worker Agent specialized in incident monitoring and response.

Provide clear, urgent incident information:
- Use severity indicators: 🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low
- Use status indicators: 🆕 Open, ⚙️ In Progress, ✅ Resolved
- Prioritize critical and open incidents first
- Include impact: affected services and user count
- Highlight timelines and next steps

Be factual, urgent when appropriate, and help users respond quickly to incidents.""",
    )
    logger.info("✅ Incident Worker Agent created successfully")
    return agent


if __name__ == "__main__":
    # Test the Incident Worker Agent
    agent = create_incident_worker_agent()
    response = agent("What critical incidents do we have?")
    print(response)
