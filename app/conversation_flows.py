"""
Pre-built conversation flows for demos.

These ensure consistent, impressive demos by providing
structured conversation patterns.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ConversationTurn:
    """One turn in a conversation."""

    user_message: str
    expected_tools: List[str]  # Which tools should be called
    success_criteria: str  # What makes this turn successful


class DemoFlows:
    """Predefined conversation flows for the 3 main demos."""

    @staticmethod
    def morning_briefing() -> List[ConversationTurn]:
        """Demo 1: Morning AI Briefing."""
        return [
            ConversationTurn(
                user_message="Good morning! Help me plan my day.",
                expected_tools=["calendar_tool", "email_tool", "jira_tool"],
                success_criteria="Response includes calendar/meetings, urgent emails/action items, and Jira tasks.",
            )
        ]

    @staticmethod
    def report_generation() -> List[ConversationTurn]:
        """Demo 2: Intelligent Report Generation."""
        return [
            ConversationTurn(
                user_message="Generate a comprehensive Q3 2025 sales report with analysis across all regions",
                expected_tools=[
                    "knowledge_base_tool",
                    "aws_worker_tool",
                    "report_tool",
                ],
                success_criteria="Response includes sales/revenue report from DynamoDB data using the sales report template with regional analysis, top deals, and sales rep performance.",
            )
        ]

    @staticmethod
    def sales_report_detailed() -> List[ConversationTurn]:
        """Demo 2b: Detailed Sales Report Generation with Multi-Agent Orchestration."""
        return [
            ConversationTurn(
                user_message="I need a comprehensive sales report for Q3 2025. Please analyze our performance across all regions, identify top deals, and provide insights on sales rep performance.",
                expected_tools=[
                    "knowledge_base_tool",
                    "aws_worker_tool",
                    "report_tool",
                ],
                success_criteria="Orchestrator coordinates: 1) KB Worker retrieves sales_report_template.md, 2) AWS Worker queries DynamoDB SalesRecords table for Q3 2025 data, 3) Report Worker generates filled report with calculations, regional breakdowns, top 5 deals, sales rep rankings, and product category analysis.",
            )
        ]

    @staticmethod
    def presentation_creation() -> List[ConversationTurn]:
        """Demo 3: Presentation from Meeting Notes."""
        return [
            ConversationTurn(
                user_message="Create a presentation from these sprint retrospective notes: [paste notes]",
                expected_tools=["knowledge_base_tool", "presentation_tool"],
                success_criteria="Response includes slides/presentation and references sprint/retrospective.",
            )
        ]

    @staticmethod
    def all_demos() -> Dict[str, List[ConversationTurn]]:
        """All demo flows in a dict."""
        return {
            "morning_briefing": DemoFlows.morning_briefing(),
            "report_generation": DemoFlows.report_generation(),
            "sales_report_detailed": DemoFlows.sales_report_detailed(),
            "presentation_creation": DemoFlows.presentation_creation(),
        }


def validate_demo_flow(flow_name: str, actual_tools_called: List[str]) -> bool:
    """
    Validate that a demo flow called the expected tools.

    Args:
        flow_name: Name of the demo (morning_briefing, report_generation, presentation_creation)
        actual_tools_called: List of tool names that were actually called

    Returns:
        True if all expected tools were called
    """
    flows = DemoFlows.all_demos()
    if flow_name not in flows:
        return False

    expected_tools = set()
    for turn in flows[flow_name]:
        expected_tools.update(turn.expected_tools)

    actual_tools = set(actual_tools_called)

    return expected_tools.issubset(actual_tools)
