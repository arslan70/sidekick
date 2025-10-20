"""
Data schemas for the SideKick application.

Defines Pydantic models for structured data exchange between agents and tools.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    """Represents a calendar event."""

    title: str = Field(..., description="Event title")
    start: datetime = Field(..., description="Event start time")
    end: datetime = Field(..., description="Event end time")
    attendees: List[str] = Field(
        default_factory=list, description="List of attendee emails"
    )
    location: Optional[str] = Field(None, description="Event location")
    description: Optional[str] = Field(None, description="Event description")


class JiraIssue(BaseModel):
    """Represents a Jira issue."""

    key: str = Field(..., description="Issue key (e.g., PROJ-123)")
    summary: str = Field(..., description="Issue summary/title")
    status: str = Field(..., description="Current status")
    description: Optional[str] = Field(None, description="Issue description")
    assignee: Optional[str] = Field(None, description="Assignee username")
    due_date: Optional[datetime] = Field(None, description="Due date")
    labels: List[str] = Field(default_factory=list, description="Issue labels")
    linked_pages: List[str] = Field(
        default_factory=list, description="Linked Confluence pages"
    )


class KnowledgeChunk(BaseModel):
    """Represents a retrieved knowledge chunk from Bedrock KB."""

    text: str = Field(..., description="Retrieved text content")
    source_id: str = Field(..., description="Source document ID")
    source_uri: Optional[str] = Field(None, description="Source document URI/URL")
    score: float = Field(..., description="Relevance score (0.0-1.0)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class EmailMessage(BaseModel):
    """Represents an email message."""

    id: str = Field(..., description="Unique email ID")
    subject: str = Field(..., description="Email subject")
    sender: str = Field(..., description="Sender email address")
    timestamp: datetime = Field(..., description="Date/time email was received")
    body: str = Field(..., description="Email body content")
    is_urgent: bool = Field(
        default=False, description="Whether email is urgent/flagged"
    )


class ActionItem(BaseModel):
    """Represents an action item extracted from email or meeting."""

    description: str = Field(..., description="Action item description")
    deadline: Optional[datetime] = Field(None, description="Due date if specified")
    priority: str = Field(
        default="medium", description="Priority: low, medium, high, critical"
    )
    assigned_to: Optional[str] = Field(
        None, description="Person assigned to the action item"
    )
    dependencies: Optional[List[str]] = Field(
        None, description="Dependencies that must be completed first"
    )


class MeetingNotes(BaseModel):
    """Represents meeting notes with key information."""

    title: str = Field(..., description="Meeting title")
    date: datetime = Field(..., description="Meeting date/time")
    attendees: List[str] = Field(default_factory=list, description="Meeting attendees")
    summary: str = Field(..., description="Meeting summary")
    decisions: List[str] = Field(default_factory=list, description="Key decisions made")
    action_items: List[ActionItem] = Field(
        default_factory=list, description="Action items from meeting"
    )


class ReportTemplate(BaseModel):
    """Represents a report template structure."""

    title: str = Field(..., description="Report title")
    sections: List[str] = Field(
        default_factory=list, description="Section names in order"
    )
    content: dict = Field(
        default_factory=dict, description="Section name -> content mapping"
    )
    generated_date: datetime = Field(
        default_factory=datetime.now, description="Report generation date"
    )
    data_source: str = Field(
        ..., description="Data source identifier (e.g., DynamoDB table)"
    )


class SalesRecord(BaseModel):
    """Represents a sales record from DynamoDB."""

    sale_id: str = Field(..., description="Unique sale ID")
    date: datetime = Field(..., description="Sale date")
    customer: str = Field(..., description="Customer name")
    product: str = Field(..., description="Product name")
    revenue: float = Field(..., description="Sale revenue in USD")
    units_sold: int = Field(..., description="Number of units sold")
    region: str = Field(..., description="Sales region")
    sales_rep: str = Field(..., description="Sales representative name")


class Incident(BaseModel):
    """Represents an incident in the incident management system."""

    id: str = Field(..., description="Unique incident ID")
    title: str = Field(..., description="Incident title/summary")
    status: str = Field(
        ..., description="Current status (e.g., Open, In Progress, Resolved)"
    )
    severity: str = Field(
        ..., description="Incident severity (Critical, High, Medium, Low)"
    )
    impact: str = Field(..., description="Impact description")
    affected_services: List[str] = Field(
        default_factory=list, description="List of affected services"
    )
    assigned_to: Optional[str] = Field(
        None, description="Person/team assigned to the incident"
    )
    reported_by: str = Field(..., description="Person who reported the incident")
    reported_at: datetime = Field(..., description="Time when incident was reported")
    resolved_at: Optional[datetime] = Field(
        None, description="Time when incident was resolved"
    )
    description: str = Field(..., description="Detailed incident description")
    root_cause: Optional[str] = Field(
        None, description="Root cause analysis if available"
    )
    resolution: Optional[str] = Field(None, description="Resolution description")
    timeline: List[str] = Field(
        default_factory=list, description="Timeline of key events"
    )
    related_email_id: Optional[str] = Field(
        None, description="Related email ID if incident was reported via email"
    )


class DayPlan(BaseModel):
    """Represents a user's day plan."""

    events: List[CalendarEvent] = Field(
        default_factory=list, description="Calendar events"
    )
    issues: List[JiraIssue] = Field(default_factory=list, description="Jira issues")
    selected_item: Optional[str] = Field(None, description="Selected item key/id")
    steps: List[str] = Field(default_factory=list, description="Planned steps")
    context: List[KnowledgeChunk] = Field(
        default_factory=list, description="Retrieved context"
    )
