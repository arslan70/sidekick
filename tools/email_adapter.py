"""
Email adapter for MVP.

Provides interface to fetch and process emails.
Uses local data from configs/email_data.json
"""

import json
import os
import time

try:
    import boto3
except Exception:
    boto3 = None
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools.schemas import ActionItem, EmailMessage

# Global reference to action intelligence agent
_action_intelligence_agent = None


def set_action_intelligence_agent(agent):
    """Set the action intelligence agent for extraction."""
    global _action_intelligence_agent
    _action_intelligence_agent = agent


# Simple in-memory cache for summaries: email_id -> (summary, timestamp)
_SUMMARY_CACHE: Dict[str, Tuple[str, float]] = {}
_SUMMARY_CACHE_TTL = int(os.getenv("EMAIL_SUMMARY_CACHE_TTL", "300"))


class EmailAdapter:
    """Adapter for email."""

    def __init__(self):
        """
        Initialize the email adapter.

        Uses local data files from configs directory.
        """
        self.data_path = Path(__file__).parent.parent / "configs" / "email_data.json"

        # Initialize action intelligence agent if not set globally
        if _action_intelligence_agent is None:
            try:
                import sys

                sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
                from worker_email_actions import \
                    create_email_action_intelligence_agent

                self.action_agent = create_email_action_intelligence_agent()
            except ImportError:
                # Fallback to None if import fails
                self.action_agent = None
        else:
            self.action_agent = _action_intelligence_agent
        # Initialize Bedrock client lazily for LLM summarization if enabled
        self._use_llm = os.getenv("USE_LLM_EMAIL_SUMMARIES", "true").lower() == "true"
        self._bedrock_region = os.getenv("AWS_REGION", "eu-central-1")
        self.bedrock_runtime: Optional[object] = None
        if self._use_llm:
            try:
                self.bedrock_runtime = boto3.client(
                    "bedrock-runtime",
                    region_name=self._bedrock_region,
                )
            except Exception:
                # If Bedrock client can't be initialized, we'll fallback later
                self.bedrock_runtime = None

    def get_recent_emails(self, limit: int = 10) -> List[EmailMessage]:
        """
        Fetch recent emails.

        Args:
            limit: Maximum number of emails to return

        Returns:
            List of EmailMessage objects.
        """
        if self.data_path.exists():
            with open(self.data_path, "r") as f:
                data = json.load(f)
                emails = []
                for email_data in data.get("emails", [])[:limit]:
                    # Parse timestamp
                    email_data["timestamp"] = datetime.fromisoformat(
                        email_data["timestamp"]
                    )
                    emails.append(EmailMessage(**email_data))
                return emails
        return []

    def get_urgent_emails(self) -> List[EmailMessage]:
        """
        Fetch urgent/unread emails.

        Returns:
            List of urgent EmailMessage objects.
        """
        all_emails = self.get_recent_emails(limit=50)
        return [email for email in all_emails if email.is_urgent]

    def extract_action_items(self, email: EmailMessage) -> List[ActionItem]:
        """
        Extract action items from an email using LLM intelligence.

        Args:
            email: EmailMessage to parse

        Returns:
            List of ActionItem objects.
        """
        if self.action_agent is None:
            # Fallback to empty list if no agent available
            return []

        try:
            # Prepare email data for analysis
            email_context = f"""
Email Subject: {email.subject}
From: {email.sender}
Sent: {email.timestamp.strftime('%Y-%m-%d %I:%M %p')}
Is Urgent: {email.is_urgent}

Email Body:
{email.body}

---
Today's date: {datetime.now().strftime('%Y-%m-%d')}

Please analyze this email and extract all action items. Return as JSON array.
"""

            # Call action intelligence agent
            response = self.action_agent(email_context)

            # Parse response
            if hasattr(response, "messages"):
                result_text = response.messages[0].content
            else:
                result_text = str(response)

            # Extract JSON from response
            action_items = self._parse_action_items_from_response(result_text, email)

            return action_items

        except Exception as e:
            # Fallback to empty list on error
            print(f"Error extracting action items: {e}")
            return []

    def _parse_action_items_from_response(
        self, response_text: str, email: EmailMessage
    ) -> List[ActionItem]:
        """
        Parse action items from LLM response.

        Args:
            response_text: LLM response containing JSON
            email: Original email for fallback data

        Returns:
            List of ActionItem objects
        """
        action_items = []

        try:
            # Try to extract JSON array from response
            # Look for JSON array pattern
            json_match = re.search(r"\[\s*\{.*?\}\s*\]", response_text, re.DOTALL)

            if json_match:
                json_str = json_match.group(0)
                items_data = json.loads(json_str)

                for item_data in items_data:
                    # Parse deadline if present
                    deadline = None
                    if item_data.get("deadline"):
                        try:
                            deadline = datetime.fromisoformat(item_data["deadline"])
                        except (ValueError, TypeError):
                            deadline = None

                    # Create ActionItem
                    action_item = ActionItem(
                        description=item_data.get("description", ""),
                        deadline=deadline,
                        priority=item_data.get("priority", "medium"),
                        assigned_to=item_data.get("assigned_to"),
                        dependencies=item_data.get("dependencies"),
                    )

                    # Only include high confidence items
                    if item_data.get("confidence", 1.0) >= 0.7:
                        action_items.append(action_item)

        except Exception as e:
            print(f"Error parsing action items JSON: {e}")
            # Return empty list rather than crash

        return action_items

    def summarize_email(self, email: EmailMessage) -> str:
        """
        Generate a concise summary of an email.

        Args:
            email: EmailMessage to summarize

        Returns:
            Summary string.
        """
        # Check cache first
        cache_key = getattr(email, "id", None)
        if cache_key is None:
            # Fallback cache key if email has no id
            cache_key = f"{email.sender}:{email.subject}:{email.timestamp.isoformat()}"

        now = time.time()
        cached = _SUMMARY_CACHE.get(cache_key)
        if cached and now - cached[1] < _SUMMARY_CACHE_TTL:
            return cached[0]

        # If LLM not available, use simple summarizer
        if self.bedrock_runtime is None:
            summary = self._simple_summarize(email)
            _SUMMARY_CACHE[cache_key] = (summary, now)
            return summary

        # Prepare prompt for LLM
        try:
            prompt = (
                "Summarize this email concisely in 1-2 sentences. "
                "Focus on key information, action items, and deadlines. "
                "Skip greetings, signatures, and boilerplate.\n\n"
                f"Subject: {email.subject}\n"
                f"From: {email.sender}\n"
                f"Sent: {email.timestamp.strftime('%Y-%m-%d %I:%M %p')}\n\n"
                "Email Body:\n"
                f"{email.body}\n\n"
                "Concise Summary (1-2 sentences):"
            )

            # Invoke Bedrock model
            payload = {
                "prompt": prompt,
                "max_tokens": 120,
                "temperature": 0.3,
                "top_p": 0.9,
            }

            response = self.bedrock_runtime.invoke_model(
                modelId=os.getenv("EMAIL_SUMMARY_MODEL", "eu.amazon.nova-micro-v1:0"),
                body=json.dumps(payload),
            )

            # Parse response body
            result = None
            try:
                body_bytes = response.get("body")
                if hasattr(body_bytes, "read"):
                    result = json.loads(body_bytes.read())
                else:
                    result = json.loads(body_bytes)
            except Exception:
                # Last-resort stringify
                result = {}

            summary = ""
            # Try common keys used by Bedrock responses
            if isinstance(result, dict):
                summary = (
                    result.get("completion")
                    or result.get("content")
                    or result.get("output")
                    or ""
                )

            # Fallback to string conversion of response
            if not summary:
                try:
                    # Some SDKs return the text directly
                    summary = str(response)
                except Exception:
                    summary = ""

            summary = summary.strip()

            # If LLM returned nothing useful, fallback
            if not summary:
                summary = self._simple_summarize(email)

            # Ensure reasonable length and punctuation
            if len(summary) > 300:
                # Truncate to two sentences if possible
                sentences = re.split(r"(?<=[.!?])\s+", summary)
                summary = " ".join(sentences[:2]).strip()

            # Final fallback
            if not summary:
                summary = self._simple_summarize(email)

            # Cache and return
            _SUMMARY_CACHE[cache_key] = (summary, now)
            return summary

        except Exception as e:
            print(f"Error in LLM summarization: {e}")
            summary = self._simple_summarize(email)
            _SUMMARY_CACHE[cache_key] = (summary, now)
            return summary

    def _simple_summarize(self, email: EmailMessage) -> str:
        """
        Simple fallback summarizer that removes boilerplate and picks
        the most informative lines.
        """
        lines = email.body.split("\n")

        # Skip common email boilerplate
        content_lines: List[str] = []
        skip_patterns = [
            "dear",
            "hi",
            "hello",
            "regards",
            "thanks",
            "thank you",
            "sent from",
            "confidential",
            "best,",
            "cheers",
            "kind regards",
        ]

        for line in lines:
            line_stripped = line.strip()
            if len(line_stripped) < 15:
                continue
            low = line_stripped.lower()
            if any(pat in low for pat in skip_patterns):
                continue
            # Exclude lines that look like signatures (multiple words but
            # with email-like tokens) or lines that are mostly dashes
            if re.match(r"[-]{2,}", line_stripped):
                continue
            content_lines.append(line_stripped)

        key_lines = content_lines[:3]
        summary = " ".join(key_lines)

        # Truncate at sentence boundary if possible
        if len(summary) > 200:
            sentence_ends = [".", "!", "?"]
            last_end = -1
            for i, ch in enumerate(summary[:200]):
                if ch in sentence_ends:
                    last_end = i

            if last_end > 100:
                summary = summary[: last_end + 1]
            else:
                summary = summary[:197] + "..."

        return (
            summary
            if summary
            else f"Email from {email.sender} regarding {email.subject}"
        )

    def format_emails_for_display(self, emails: List[EmailMessage]) -> str:
        """Format emails for readable display."""
        if not emails:
            return "No emails found."

        formatted = [f"**{len(emails)} Email(s):**\n"]

        for i, email in enumerate(emails, 1):
            urgency = "🔴 URGENT" if email.is_urgent else "📧"
            formatted.append(f"{i}. {urgency} **{email.subject}**")
            formatted.append(f"   From: {email.sender}")
            formatted.append(
                f"   Time: {email.timestamp.strftime('%Y-%m-%d %I:%M %p')}"
            )

            # Add summary
            summary = self.summarize_email(email)
            formatted.append(f"   Summary: {summary}")

            # Extract action items if urgent
            if email.is_urgent:
                actions = self.extract_action_items(email)
                if actions:
                    formatted.append(f"   **Action Items**: {len(actions)} found")
                    for action in actions[:2]:  # Show first 2
                        formatted.append(f"      - {action.description}")

            formatted.append("")

        return "\n".join(formatted)


def fetch_recent_emails(limit: int = 10) -> dict:
    """
    Tool function to fetch recent emails.
    Compatible with StrandsAgents tool interface.
    """
    try:
        adapter = EmailAdapter()
        emails = adapter.get_recent_emails(limit=limit)

        return {"emails": [email.model_dump(mode="json") for email in emails]}
    except Exception as e:
        return {"error": f"Failed to fetch emails: {str(e)}"}


def fetch_urgent_emails() -> dict:
    """Tool function to fetch urgent emails."""
    try:
        adapter = EmailAdapter()
        emails = adapter.get_urgent_emails()

        return {"emails": [email.model_dump(mode="json") for email in emails]}
    except Exception as e:
        return {"error": f"Failed to fetch urgent emails: {str(e)}"}


def extract_action_items_from_email(email_id: str) -> dict:
    """Tool function to extract action items from a specific email."""
    try:
        adapter = EmailAdapter()
        emails = adapter.get_recent_emails(limit=50)

        # Find the email
        target_email = next((e for e in emails if e.id == email_id), None)
        if not target_email:
            return {"error": f"Email {email_id} not found"}

        action_items = adapter.extract_action_items(target_email)

        return {
            "email": target_email.model_dump(mode="json"),
            "action_items": [item.model_dump(mode="json") for item in action_items],
        }
    except Exception as e:
        return {"error": f"Failed to extract action items: {str(e)}"}
