"""
Knowledge Base Worker Agent - Specialized agent for RAG using Bedrock Knowledge Bases.

This worker agent uses Amazon Bedrock Knowledge Bases to retrieve relevant
documentation and context. Can be called by the Orchestrator using Agents-as-Tools pattern.

Updated to use strands_tools.retrieve for production knowledge base integration.
"""

import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

# Agent-specific model and region constants
KB_MODEL_ID = "eu.amazon.nova-pro-v1:0"
KB_REGION = "eu-central-1"

from strands import Agent
from strands.models import BedrockModel

# Import the retrieve tool from strands_tools
try:
    from strands_tools import retrieve

    RETRIEVE_AVAILABLE = True
    print("✅ Using strands_tools.retrieve for knowledge base access")
except ImportError:
    RETRIEVE_AVAILABLE = False
    retrieve = None
    print(
        "⚠️ strands-agents-tools not installed. Install with: pip install strands-agents-tools"
    )


def create_kb_worker_agent(*args, **kwargs):
    """
    Create a knowledge base worker agent using agent-specific model and region constants.

    Args:
        knowledge_base_id: Optional Bedrock Knowledge Base ID (can also set via env var KNOWLEDGE_BASE_ID)
        region: Optional AWS region (default: eu-central-1, can also set via env var AWS_REGION)

    Environment Variables:
        KNOWLEDGE_BASE_ID: The Bedrock Knowledge Base ID to query
        AWS_REGION: AWS region where the knowledge base is located (default: eu-central-1)
        MIN_SCORE: Minimum relevance score threshold (default: 0.4)

    Returns:
        Agent configured with retrieve tool for knowledge base access
    """
    if not RETRIEVE_AVAILABLE:
        raise ImportError(
            "strands-agents-tools is required for knowledge base functionality. "
            "Install with: pip install strands-agents-tools"
        )

    # Create Bedrock model for the agent
    bedrock_model = BedrockModel(
        model_id=KB_MODEL_ID,
        region_name=kwargs.get("region", KB_REGION),
        temperature=0.3,
        streaming=False,
    )

    # Create agent with retrieve tool
    agent = Agent(
        model=bedrock_model,
        name="knowledge_base_worker",
        tools=[retrieve],
        system_prompt="""You are a Knowledge Base Worker Agent specialized in organizational knowledge retrieval.

Your role is to help users find relevant information from the company's knowledge base, which includes:
- Budget documents and financial reports
- Templates and guidelines
- Standard operating procedures (SOPs)
- Best practices and reference materials
- Historical context and decisions
- Technical documentation

When searching for information:
1. Use the retrieve tool with clear, specific search queries
2. Present information clearly with proper citations
3. Highlight key information and actionable guidance
4. Always include document sources for reference
5. Summarize complex information concisely
6. If information is not found, suggest related topics to search

For budget-related queries:
- Look for budget reports, actual spend documents, and budget requests
- Compare current requests with historical data
- Highlight key variances and trends
- Provide context on budget categories and justifications

Be precise, thorough, and always cite your sources with document IDs and relevance scores.""",
    )
    return agent


if __name__ == "__main__":
    # Test the KB Worker Agent
    import os

    # Check if we have KB configuration
    kb_id = os.getenv("KNOWLEDGE_BASE_ID")

    if kb_id:
        print(f"✅ Knowledge Base ID configured: {kb_id}")
        print("Creating knowledge base agent...")
    else:
        print("⚠️ No KNOWLEDGE_BASE_ID set. Agent may have limited functionality...")

    agent = create_kb_worker_agent()

    # Test query
    test_query = "Find information about Q4 2025 budget request and compare with Q3 2024 actual spend"
    print(f"\n🔍 Test Query: {test_query}\n")
    response = agent.invoke(test_query)
    print(response.messages[0].content)
