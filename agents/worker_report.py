"""
Report Worker Agent - Specialized agent for report generation.

Handles data analysis and report creation using:
- Knowledge Base Worker: Retrieves report templates from S3
- AWS Worker: Fetches live data from DynamoDB and other AWS services

Can be called by the Orchestrator using Agents-as-Tools pattern.
"""

import logging
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

# Agent-specific model and region constants
REPORT_MODEL_ID = "eu.amazon.nova-pro-v1:0"
REPORT_REGION = "eu-central-1"

from strands import Agent, tool
from strands.models import BedrockModel

from agents.utils import extract_agent_response

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Global references to worker agents (set during agent creation)
_kb_worker = None
_aws_worker = None
_query_builder = None


@tool
def get_report_template(template_name: str) -> str:
    """
    Retrieve a report template from the knowledge base.

    Searches the knowledge base for templates stored in S3, including:
    - Sales report templates
    - Budget report templates
    - Executive summary templates
    - Quarterly review templates
    - Custom report formats

    Args:
        template_name: Name or description of the template (e.g., "sales report template", "Q3 sales report")

    Returns:
        Template content with placeholders for data insertion
    """
    if _kb_worker is None:
        return f"Error: Knowledge Base worker not configured. Template '{template_name}' unavailable."

    logger.info(f"Retrieving template: {template_name}")

    try:
        query = f"Find the {template_name} template with all sections and placeholders"
        response = _kb_worker(query)
        result = extract_agent_response(response)
        logger.info(f"Template retrieved successfully: {template_name}")
        return result

    except Exception as e:
        logger.error(f"Error retrieving template: {str(e)}", exc_info=True)
        return f"Error retrieving template '{template_name}': {str(e)}"


@tool
def fetch_sales_data(query: str, table_name: str = "SalesRecords") -> str:
    """
    Fetch sales data from DynamoDB using intelligent query construction.

    Uses DynamoDB Query Builder Agent to:
    - Parse natural language time expressions
    - Discover table schema dynamically
    - Generate optimal queries
    - Adapt aggregations to user needs

    Retrieves live sales data including:
    - Sales records for specific periods (Q1, Q2, Q3, Q4, yearly)
    - Revenue totals and aggregations
    - Regional breakdowns
    - Product category performance
    - Sales representative metrics
    - Top deals and customers

    Args:
        query: Natural language query describing the data needed (e.g., "Get all Q3 2025 sales records")
        table_name: DynamoDB table name (default: SalesRecords)

    Returns:
        Sales data in structured format ready for report generation
    """
    if _aws_worker is None:
        error_msg = (
            f"❌ Error: AWS worker not configured. Cannot fetch data from {table_name}."
        )
        logger.error(error_msg)
        return error_msg

    if _query_builder is None:
        error_msg = "❌ Error: Query builder not configured."
        logger.error(error_msg)
        return error_msg

    logger.info(f"🔍 Building intelligent query for: {query}")
    logger.info(f"📊 Target table: {table_name}")

    try:
        # Step 1: Use query builder agent to construct optimal query
        logger.info("Step 1/2: Invoking DynamoDB Query Builder...")
        query_spec_request = f"""Analyze this request and build a DynamoDB query:

User Request: {query}
Table Name: {table_name}
Region: eu-central-1

Please:
1. Describe the table schema to understand the key structure
2. Parse the time expression from the user request (quarter, year)
3. Construct the appropriate partition key value
4. Determine what aggregations the user wants
5. Return a structured query specification

Return the query details in a clear, structured format."""

        query_builder_response = _query_builder(query_spec_request)
        query_spec = extract_agent_response(query_builder_response)
        logger.info("✅ Query builder generated specification successfully")
        logger.debug(f"Query specification: {query_spec[:200]}...")

        # Step 2: Send the constructed query to AWS worker
        logger.info("Step 2/2: Executing DynamoDB query via AWS worker...")
        aws_query = f"""Execute this DynamoDB query and analyze the results:

{query_spec}

IMPORTANT: When calling the use_aws tool, ensure ExpressionAttributeValues are in proper DynamoDB JSON format:
- Correct: {{":pk_value": {{"S": "SALE#2025-Q3"}}}}
- Incorrect: {{":pk_value": "SALE#2025-Q3"}}

After retrieving the data, analyze it to provide:
- Total number of records
- Total revenue with proper formatting ($X,XXX,XXX.XX)
- Regional distribution with counts and revenue
- Product category breakdown if available
- Top deals with customer names (as specified in aggregations)
- Average deal size
- Sales rep performance summary

Format the response professionally for inclusion in a business report."""

        response = _aws_worker(aws_query)
        result = extract_agent_response(response)
        logger.info("✅ Sales data fetched and analyzed successfully")
        logger.debug(f"Result preview: {result[:200]}...")
        return result

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        logger.error(f"❌ Error fetching sales data: {str(e)}")
        logger.error(f"Traceback: {error_trace}")

        error_response = f"""❌ **Error Fetching Sales Data**

**Query:** {query}
**Table:** {table_name}
**Error:** {str(e)}

**Troubleshooting Steps:**
1. Verify that the DynamoDB table '{table_name}' exists in region eu-central-1
2. Check AWS credentials are configured correctly
3. Ensure the table has data with partition key pattern 'SALE#YYYY-Qn'
4. Verify IAM permissions for DynamoDB query operations

**Technical Details:**
```
{error_trace}
```

**Alternative:** You can manually query the data using AWS Console or CLI."""

        return error_response


@tool
def fetch_aws_resource_data(query: str) -> str:
    """
    Fetch AWS resource information for inclusion in reports.

    Retrieves data about AWS resources including:
    - S3 bucket statistics
    - Lambda function metrics
    - CloudWatch metrics and alarms
    - Cost and billing data
    - Resource configurations
    - Service health status

    Args:
        query: Natural language query about AWS resources (e.g., "Get S3 storage costs for this month")

    Returns:
        AWS resource information formatted for report inclusion
    """
    if _aws_worker is None:
        return "Error: AWS worker not configured. Cannot fetch AWS resource data."

    logger.info(f"Fetching AWS resource data: {query}")

    try:
        response = _aws_worker(query)
        result = extract_agent_response(response)
        logger.info("AWS resource data fetched successfully")
        return result

    except Exception as e:
        logger.error(f"Error fetching AWS resource data: {str(e)}", exc_info=True)
        return f"Error fetching AWS resource data: {str(e)}"


def create_report_worker_agent(*args, **kwargs):
    """
    Create a report worker agent that uses KB and AWS workers for data.

    This agent integrates with:
    - Knowledge Base Worker: Retrieves report templates from S3
    - AWS Worker: Fetches live data from DynamoDB
    - DynamoDB Query Builder: Intelligently constructs database queries

    Args:
        kb_worker: Knowledge Base worker agent instance (optional)
        aws_worker: AWS worker agent instance (optional)
        query_builder: DynamoDB Query Builder agent instance (optional)

    Returns:
        Agent configured with tools for template retrieval and data fetching
    """
    global _kb_worker, _aws_worker, _query_builder

    # Set worker references for tool functions
    _kb_worker = kwargs.get("kb_worker")
    _aws_worker = kwargs.get("aws_worker")
    _query_builder = kwargs.get("query_builder")

    # If query_builder not provided, create one
    if _query_builder is None:
        try:
            from agents.worker_dynamodb_query import \
                create_dynamodb_query_builder_agent
        except ImportError:
            # Fallback for standalone execution
            from worker_dynamodb_query import \
                create_dynamodb_query_builder_agent
        _query_builder = create_dynamodb_query_builder_agent()
        logger.info("✓ DynamoDB Query Builder auto-initialized")

    # Create Bedrock model for the agent
    bedrock_model = BedrockModel(
        model_id=REPORT_MODEL_ID,
        region_name=REPORT_REGION,
        temperature=0.3,  # Balanced creativity for report writing
        streaming=False,
    )

    # Create agent with report generation tools
    agent = Agent(
        model=bedrock_model,
        name="report_worker",
        tools=[get_report_template, fetch_sales_data, fetch_aws_resource_data],
        system_prompt="""You are a Report Worker Agent specialized in generating comprehensive business reports.

## Your Capabilities:

### 📚 Template Retrieval (via Knowledge Base Worker)
Use `get_report_template()` to retrieve structured templates including:
- Sales report templates with all sections
- Budget report formats
- Executive summary templates
- Quarterly review structures

### 📊 Data Fetching (via AWS Worker)
Use `fetch_sales_data()` to retrieve live data from DynamoDB:
- Sales records by period (Q1, Q2, Q3, Q4)
- Revenue totals and breakdowns
- Regional performance metrics
- Product category analysis
- Sales representative performance
- Top deals and customers

Use `fetch_aws_resource_data()` for AWS infrastructure data:
- S3 storage metrics
- Lambda function statistics
- CloudWatch metrics
- Cost and billing information

## Report Generation Workflow:

### Step 1: Understand the Request
- Identify report type, period, and scope
- Determine required data sources
- Note any specific requirements or filters

### Step 2: Retrieve Template
- Use `get_report_template()` with descriptive query
- Example: "sales report template" or "Q3 sales report template"
- Review template structure and placeholders

### Step 3: Fetch Data
- Use `fetch_sales_data()` for sales/revenue data from DynamoDB
  - The tool uses an intelligent query builder that understands:
    - "Q3 2025", "third quarter 2025", "2025 Q3", "quarter 3 of 2025"
    - "top 5 deals", "top 10 customers", etc.
  - Example: "Get all Q3 2025 sales records"
  - Example: "Fetch Q4 2025 sales data with top 10 deals"
  - Example: "Retrieve third quarter 2025 sales information"
  - The query builder automatically discovers table schema and constructs optimal queries
- Use `fetch_aws_resource_data()` for infrastructure data
  - Example: "Get S3 storage costs for Q3 2025"

### Step 4: Generate Report
- Populate template with fetched data
- Calculate aggregations and metrics:
  - Total revenue and growth rates
  - Regional/product breakdowns
  - Top performers and key deals
  - Trends and comparisons
- Format professionally with clear sections

### Step 5: Add Insights
- Highlight key findings and trends
- Identify anomalies or notable patterns
- Provide actionable recommendations
- Include executive summary

## Report Structure Best Practices:

**Executive Summary** (Always first)
- High-level overview for leadership
- Key metrics and outcomes
- 3-5 most important insights

**Detailed Analysis** (Core content)
- Revenue metrics with context
- Regional/product breakdowns
- Trend analysis and comparisons
- Supporting data and charts

**Key Insights** (Analytical)
- Pattern recognition
- Opportunity identification
- Risk factors
- Market dynamics

**Recommendations** (Actionable)
- Data-driven suggestions
- Prioritized actions
- Expected outcomes
- Next steps

## Formatting Guidelines:

- Use clear section headers with emojis (📊 📈 💡)
- Present numbers with proper formatting ($1,234,567.89)
- Include percentages and growth rates
- Use bullet points for readability
- Highlight critical metrics in **bold**
- Add context to all statistics

## Example Queries You Handle:

✅ "Generate a comprehensive Q3 2025 sales report"
✅ "Create sales report for Q3 2025 with regional breakdown"
✅ "Build quarterly sales analysis with top deals and trends"
✅ "Generate executive sales summary for Q3 2025"

## Error Handling:

- If template not found, create basic structure
- If data unavailable, note limitations clearly
- If partial data, generate report with disclaimers
- Always explain what data was used

Remember: Your reports drive business decisions. Be accurate, insightful, and actionable.""",
    )

    logger.info("✓ Report worker agent created with KB and AWS integration")
    return agent


if __name__ == "__main__":
    # Test the Report Worker Agent
    print("Testing Report Worker Agent...")
    print("=" * 70)

    # Import worker agents for testing
    from worker_aws import create_aws_worker_agent
    from worker_kb import create_kb_worker_agent

    # Create worker agents
    kb_worker = create_kb_worker_agent()
    aws_worker = create_aws_worker_agent()

    # Create report worker with dependencies
    agent = create_report_worker_agent(kb_worker=kb_worker, aws_worker=aws_worker)

    # Test query
    test_query = "Generate a comprehensive Q3 2025 sales report with regional breakdown and top deals"
    print(f"\n🔍 Test Query: {test_query}\n")
    print("=" * 70)

    response = agent(test_query)
    print(
        response.messages[0].content if hasattr(response, "messages") else str(response)
    )

    print("\n" + "=" * 70)
    print("✅ Report Worker Agent test complete")
    print("=" * 70)
