"""
Orchestrator Agent - Main agent coordinating Worker agents using Agents-as-Tools pattern.

The Orchestrator delegates specialized tasks to Worker agents (Calendar, Jira, KB)
and manages the conversational flow for daily planning assistance.
"""

import logging
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).parent))

from strands import Agent, tool
from strands.models import BedrockModel

# Configure logging for strands framework
# Note: Don't call basicConfig here as it's already configured in agent_runtime.py
logging.getLogger("strands").setLevel(logging.INFO)

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from agents.utils import extract_agent_response
from agents.worker_aws import create_aws_worker_agent
from agents.worker_calendar import create_calendar_worker_agent
from agents.worker_dynamodb_query import create_dynamodb_query_builder_agent
from agents.worker_email import create_email_worker_agent
from agents.worker_incident import create_incident_worker_agent
from agents.worker_jira import create_jira_worker_agent
from agents.worker_kb import create_kb_worker_agent
from agents.worker_report import create_report_worker_agent


def create_orchestrator_agent(
    model: str, region: str, guardrail_id: str = None, guardrail_version: str = None
) -> Agent:
    """
    Create orchestrator that coordinates 7 specialized workers.

    Workers:
    - Calendar: Meetings, schedules, availability
    - Email: Inbox management, action items
    - Jira: Task tracking, issue management
    - Incident: Incident management and monitoring
    - AWS: AWS service monitoring (READ-ONLY)
    - Knowledge Base: Document retrieval, templates
    - Report: Data analysis, PDF generation
    """

    logger.info(f"Creating Orchestrator Agent (model={model}, region={region})")

    # Create Bedrock model for orchestrator
    logger.info("Initializing Bedrock model for orchestrator")
    model_config = {
        "model_id": model,
        "region_name": region,
        "temperature": 0.7,  # Higher creativity for planning and synthesis
        "streaming": True,  # Enable streaming for real-time updates
    }

    # Add guardrail configuration if provided
    if guardrail_id:
        model_config["guardrail_id"] = guardrail_id
        model_config["guardrail_version"] = guardrail_version or "1"
        model_config["guardrail_trace"] = "enabled"
        logger.info(
            f"Guardrails enabled: {guardrail_id} v{model_config['guardrail_version']}"
        )

    bedrock_model = BedrockModel(**model_config)

    # Initialize all 7 workers
    logger.info("Initializing 7 worker agents...")
    calendar_worker = create_calendar_worker_agent()
    logger.info("✓ Calendar worker initialized")

    email_worker = create_email_worker_agent()
    logger.info("✓ Email worker initialized")

    jira_worker = create_jira_worker_agent()
    logger.info("✓ Jira worker initialized")

    incident_worker = create_incident_worker_agent()
    logger.info("✓ Incident worker initialized")

    aws_worker = create_aws_worker_agent()
    logger.info("✓ AWS worker initialized (READ-ONLY mode)")

    kb_worker = create_kb_worker_agent()
    logger.info("✓ Knowledge Base worker initialized")

    # Create DynamoDB Query Builder agent
    query_builder = create_dynamodb_query_builder_agent()
    logger.info("✓ DynamoDB Query Builder initialized")

    report_worker = create_report_worker_agent(
        kb_worker=kb_worker, aws_worker=aws_worker, query_builder=query_builder
    )
    logger.info(
        "✓ Report worker initialized (with KB, AWS, and Query Builder integration)"
    )

    # Helper function removed; extract text directly in each tool

    # Wrap each as a tool with enhanced docstrings
    @tool
    def calendar_tool(query: str) -> str:
        """
        Retrieve calendar information including today's meetings, schedules, and availability.

        Use this tool when the user asks about:
        - Today's meetings or schedule
        - Specific meeting details
        - Time availability or conflicts
        - Setting meeting agendas

        Args:
            query: Natural language query about calendar events

        Returns:
            Calendar information with meeting times, attendees, locations, and details
        """
        logger.info(f"Calendar tool called with query: {query}")
        try:
            response = calendar_worker(query)
            result = extract_agent_response(response)
            logger.info("Calendar tool completed successfully")
            return result
        except Exception as e:
            logger.error(f"Calendar worker error: {str(e)}", exc_info=True)
            return f"Calendar worker error: {str(e)}"

    @tool
    def email_tool(query: str) -> str:
        """
        Retrieve and analyze email messages, focusing on recent and urgent items.

        Use this tool when the user asks about:
        - Recent emails in their inbox
        - Urgent or flagged emails requiring immediate attention
        - Action items extracted from specific emails
        - Email summaries and priorities

        Args:
            query: Natural language query about emails

        Returns:
            Email summaries with sender, subject, urgency, and extracted action items
        """
        logger.info(f"Email tool called with query: {query}")
        try:
            response = email_worker(query)
            result = extract_agent_response(response)
            logger.info("Email tool completed successfully")
            return result
        except Exception as e:
            logger.error(f"Email worker error: {str(e)}", exc_info=True)
            return f"Email worker error: {str(e)}"

    @tool
    def jira_tool(query: str) -> str:
        """
        Access Jira project management and Confluence documentation.

        Use this tool when the user asks about:

        JIRA (Read):
        - Assigned Jira tasks or issues
        - High-priority or overdue items
        - Issue details and status
        - Searching for specific issues
        - Filtering by status (To Do, In Progress, Code Review, Done)

        JIRA (Write):
        - Update issue fields (summary, description, priority)
        - Add comments to issues
        - Change issue status (move to In Progress, Done, etc.)

        CONFLUENCE (IMPORTANT - Use this tool for ALL Confluence requests):
        - Retrieve specific Confluence pages by ID (e.g., "show confluence page 360449")
        - View Confluence page contents
        - Search Confluence documentation using CQL queries
        - Find documentation related to projects or issues

        Args:
            query: Natural language query about Jira issues or Confluence documentation

        Returns:
            Jira issue information, Confluence page content, or confirmation of updates
        """
        logger.info(f"Jira tool called with query: {query}")
        try:
            response = jira_worker(query)
            result = extract_agent_response(response)
            logger.info("Jira tool completed successfully")
            return result
        except Exception as e:
            logger.error(f"Jira worker error: {str(e)}", exc_info=True)
            return f"Jira worker error: {str(e)}"

    @tool
    def incident_tool(query: str) -> str:
        """
        Monitor and retrieve incident management information for system outages and issues.

        Use this tool when the user asks about:
        - Current incidents or outages
        - Critical or high-severity incidents
        - Specific incident details and status
        - Open incidents requiring attention
        - Incidents related to specific emails

        Args:
            query: Natural language query about incidents

        Returns:
            Incident details with severity, status, impact, affected services, and resolution timeline
        """
        logger.info(f"Incident tool called with query: {query}")
        try:
            response = incident_worker(query)
            result = extract_agent_response(response)
            logger.info("Incident tool completed successfully")
            return result
        except Exception as e:
            logger.error(f"Incident worker error: {str(e)}", exc_info=True)
            return f"Incident worker error: {str(e)}"

    @tool
    def aws_tool(query: str) -> str:
        """
        Monitor AWS services and retrieve resource information (READ-ONLY operations).

        Use this tool when the user asks about:
        - AWS resource status (EC2 instances, S3 buckets, Lambda functions)
        - Cloud infrastructure monitoring
        - AWS cost estimates and billing
        - CloudWatch metrics and alarms
        - Service configurations (read-only view)

        CRITICAL: This tool performs ONLY read-only operations. It CANNOT and WILL NOT:
        - Create, delete, or modify any resources
        - Start, stop, or terminate instances
        - Upload, write, or change data
        - Execute any mutative operations

        Args:
            query: Natural language query about AWS resources and services

        Returns:
            AWS resource information with status, configurations, and monitoring data
        """
        logger.info(f"AWS tool called with query: {query}")
        try:
            response = aws_worker(query)
            result = extract_agent_response(response)
            logger.info("AWS tool completed successfully")
            return result
        except Exception as e:
            logger.error(f"AWS worker error: {str(e)}", exc_info=True)
            return f"AWS worker error: {str(e)}"

    @tool
    def knowledge_base_tool(query: str) -> str:
        """
        Search organizational knowledge base for templates, procedures, and best practices.

        Use this tool when the user needs:
        - Runbooks and troubleshooting guides (e.g., S3 permissions runbook, incident response procedures)
        - Company templates or guidelines
        - Internal documentation and procedures (NOT Confluence - use jira_tool for Confluence)
        - Best practices and reference materials
        - Historical context from knowledge articles
        - Budget documents and financial reports

        NOTE: For Confluence pages, use jira_tool instead.

        Args:
            query: Search query describing needed information

        Returns:
            Relevant knowledge base articles with citations and source references
        """
        logger.info(f"Knowledge base tool called with query: {query}")
        try:
            response = kb_worker(query)
            result = extract_agent_response(response)
            logger.info("Knowledge base tool completed successfully")
            return result
        except Exception as e:
            logger.error(f"Knowledge base worker error: {str(e)}", exc_info=True)
            return f"Knowledge base worker error: {str(e)}"

    @tool
    def report_tool(query: str) -> str:
        """
        Generate data-driven reports and analytics for business insights.

        Use this tool when the user requests:
        - Sales reports for specific periods
        - Data analysis and trends
        - Executive summaries
        - Business intelligence insights

        Args:
            query: Request specifying report type and parameters

        Returns:
            Formatted report with data, insights, and visualizations
        """
        logger.info(f"Report tool called with query: {query}")
        try:
            response = report_worker(query)
            result = extract_agent_response(response)
            logger.info("Report tool completed successfully")
            return result
        except Exception as e:
            logger.error(f"Report worker error: {str(e)}", exc_info=True)
            return f"Report worker error: {str(e)}"

    # Concise system prompt focused on behavior and delegation strategy
    system_prompt = """You are an Enterprise AI Sidekick that helps employees maximize their productivity.

## Your Role

## Core Principles

**Proactive Intelligence**: Anticipate user needs and provide relevant context.
- Morning greetings → Comprehensive daily briefing
- Incident queries → Include severity, impact, and status
- AWS queries → Monitor resources and costs (read-only)
- Report requests → Find templates and generate with executive summaries
- JIRA queries → Can also search related Confluence documentation
- Documentation requests → Search Confluence pages and link to JIRA issues
- Runbook requests → Use knowledge_base_tool to find troubleshooting guides and procedures

**Intelligent Delegation**: Select the right tools based on user intent.
- Use multiple tools in parallel when appropriate (e.g., calendar + email + jira for daily planning)
- Chain tools logically (e.g., knowledge base → report generation)
- AWS tool for infrastructure monitoring ONLY (no modifications allowed)
- Handle errors gracefully and continue with available information
- For JIRA queries like "my tasks", "my issues", "show my tickets", call the JIRA tool IMMEDIATELY without asking for username or clarification - the user is already authenticated
- For ALL Confluence page requests (e.g., "show confluence page 360449"), use the jira_tool - it has full Confluence access
- For runbooks, troubleshooting guides, or procedures (e.g., "S3 permissions runbook"), use the knowledge_base_tool - it has access to all internal documentation

**Clear Communication**: Present information actionably.
- Explain your approach: "I'll check your calendar, emails, and any critical incidents..."
- Provide context: "You have 4 meetings today, including 2 that conflict..."
- Use formatting for clarity: bullet points, emojis, severity indicators
- Highlight urgent items: 🔴 Critical, 🟠 High Priority, 🟡 Needs Attention

**User-Centric Synthesis**: Combine results into coherent, prioritized insights.
- Identify conflicts and overlaps (e.g., double-booked meetings)
- Extract and prioritize action items
- Surface critical issues proactively
- Include AWS resource status when relevant

**AWS Safety Protocol**: The AWS tool is STRICTLY read-only. Never attempt to:
- Create, delete, or modify resources
- Execute any mutative operations
- If user asks for AWS changes, explain that only monitoring is available

You are efficient, insightful, and save employees hours every day.
"""

    # Create orchestrator with all 7 tools
    logger.info("Creating orchestrator agent with 7 tool wrappers")
    orchestrator = Agent(
        model=bedrock_model,
        name="orchestrator",
        tools=[
            calendar_tool,
            email_tool,
            jira_tool,
            incident_tool,
            aws_tool,
            knowledge_base_tool,
            report_tool,
        ],
        system_prompt=system_prompt,
    )
    logger.info("✅ Orchestrator agent created successfully with 7 workers")
    return orchestrator


if __name__ == "__main__":
    # Test the Orchestrator Agent
    orchestrator = create_orchestrator_agent(streaming=False)
    response = orchestrator("Help me plan my day")
    print(response)
