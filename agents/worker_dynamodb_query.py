"""
DynamoDB Query Builder Agent - Intelligently constructs DynamoDB queries.

This agent:
1. Discovers table schema dynamically using describe_table
2. Parses natural language time expressions
3. Generates optimal KeyConditionExpression
4. Adapts aggregations based on user request
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

import boto3
from strands import Agent, tool
from strands.models import BedrockModel

from agents.utils import extract_agent_response

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Agent-specific model and region constants
DYNAMODB_QUERY_MODEL_ID = "eu.amazon.nova-lite-v1:0"
DYNAMODB_QUERY_REGION = "eu-central-1"


@tool
def describe_dynamodb_table(
    table_name: str, region: str = "eu-central-1"
) -> Dict[str, Any]:
    """
    Retrieve DynamoDB table schema including key structure.

    Args:
        table_name: Name of the DynamoDB table
        region: AWS region

    Returns:
        Table schema including KeySchema, AttributeDefinitions, and sample data structure
    """
    try:
        dynamodb = boto3.client("dynamodb", region_name=region)

        response = dynamodb.describe_table(TableName=table_name)
        table_info = response["Table"]

        return {
            "table_name": table_info["TableName"],
            "key_schema": table_info["KeySchema"],
            "attribute_definitions": table_info["AttributeDefinitions"],
            "item_count": table_info.get("ItemCount", 0),
            "table_size_bytes": table_info.get("TableSizeBytes", 0),
        }
    except Exception as e:
        logger.error(f"Error describing table {table_name}: {str(e)}")
        return {"error": str(e), "table_name": table_name}


def create_dynamodb_query_builder_agent():
    """
    Create an agent that builds intelligent DynamoDB queries.

    Returns:
        Agent configured to build DynamoDB queries
    """
    bedrock_model = BedrockModel(
        model_id=DYNAMODB_QUERY_MODEL_ID,
        region_name=DYNAMODB_QUERY_REGION,
        temperature=0.1,  # Low temperature for precise query construction
        streaming=False,
    )

    agent = Agent(
        model=bedrock_model,
        name="dynamodb_query_builder",
        tools=[describe_dynamodb_table],
        system_prompt="""You are a DynamoDB Query Builder Agent specialized in constructing intelligent database queries.

**Example:** "Get Q3 2025 sales and provide total revenue, regional breakdown, top 5 deals"
- ✅ Correct response: Query data, sum amounts, group by region, sort by amount, return formatted analysis
- ❌ Wrong response: "I can only return raw data" (this is incorrect!)

The "read-only" constraint only means you cannot MODIFY AWS resources.
Analyzing and aggregating the data you READ is your primary job!

### Query Construction Format

**CRITICAL: Always return parameters in DynamoDB JSON format with type descriptors:**

✅ **CORRECT ExpressionAttributeValues format:**
```json
{
  "expression_attribute_values": {
    ":pk_value": {"S": "SALE#2025-Q3"},
    ":amount": {"N": "1000"}
  }
}
```

❌ **INCORRECT format (causes validation errors):**
```json
{
  "expression_attribute_values": {
    ":pk_value": "SALE#2025-Q3"
  }
}
```

**Type Descriptors:**
- String values: `{"S": "value"}`
- Numeric values: `{"N": "123"}`
- Boolean values: `{"BOOL": true}`

### Your Capabilities

### Schema Discovery
- Use describe_dynamodb_table() to learn table structure
- Identify partition key and sort key patterns
- Understand attribute types and naming conventions

### Natural Language Time Parsing
Parse various time expressions to structured values:
- "Q3 2025" → 2025, Q3
- "third quarter of 2025" → 2025, Q3
- "2025 Q3" → 2025, Q3
- "quarter 3 2025" → 2025, Q3
- "Q3" (current context) → 2025, Q3
- "2025-Q3" → 2025, Q3
- "fourth quarter 2024" → 2024, Q4
- "Q4 of 2025" → 2025, Q4

### Query Construction
Based on table schema, construct optimal queries:
- Generate correct KeyConditionExpression
- Build ExpressionAttributeValues
- Add FilterExpression if needed
- Optimize for performance (avoid scans when possible)

### Aggregation Adaptation
Customize aggregations based on user request:
- "top 5 deals" → limit to 5, sort by amount
- "top 10 customers" → limit to 10, group by customer
- "regional breakdown" → group by region
- "monthly trends" → group by month
- If not specified, use sensible defaults for report type

## Query Construction Process

1. **First, describe the table schema** using the tool
2. **Analyze the partition key pattern** from schema and sample data
3. **Parse the user's time expression** into structured format
4. **Construct the partition key value** matching schema pattern
5. **Determine required aggregations** from user request
6. **Return structured query specification** in this format WITH PROPER DynamoDB TYPE DESCRIPTORS:

```json
{
  "table_name": "SalesRecords",
  "region": "eu-central-1",
  "operation": "query",
  "key_condition_expression": "pk = :pk_value",
  "expression_attribute_values": {
    ":pk_value": {"S": "SALE#2025-Q3"}
  },
  "aggregations_needed": [
    "total_revenue",
    "record_count",
    "regional_breakdown",
    "top_5_deals",
    "average_deal_size",
    "sales_rep_performance"
  ],
  "explanation": "Querying SalesRecords for Q3 2025 using partition key 'SALE#2025-Q3'. Using DynamoDB type descriptor 'S' for string value."
}
```

**CRITICAL:** Always include type descriptors in expression_attribute_values:
- For string partition keys: `{":pk_value": {"S": "SALE#2025-Q3"}}`
- For numeric values: `{":amount": {"N": "1000"}}`
- Never use simplified format like `{":pk_value": "SALE#2025-Q3"}` - this will cause validation errors!

## Important Rules

- **Always query schema first** before constructing queries
- **Match the existing key pattern** exactly (e.g., SALE#YYYY-Qn format)
- **Validate time expressions** - reject invalid quarters (Q5, Q0) or years
- **Prefer queries over scans** - use partition key whenever possible
- **Explain your reasoning** - include explanation field
- **Handle ambiguity** - if year not specified, ask or use current year with explanation
- **Adapt aggregations** - if user asks for "top 10", include that in aggregations_needed

Be precise, efficient, and always validate your query construction against the actual schema.""",
    )

    logger.info("✓ DynamoDB Query Builder agent created")
    return agent


if __name__ == "__main__":
    # Test the DynamoDB Query Builder Agent
    print("Testing DynamoDB Query Builder Agent...")
    print("=" * 70)

    # Create agent for testing
    agent = create_dynamodb_query_builder_agent()

    # Test queries
    test_queries = [
        "Build a query for Q3 2025 sales data",
        "Fetch third quarter 2025 sales records with top 10 deals",
        "Get Q4 2024 sales information with regional breakdown",
    ]

    for query in test_queries:
        print(f"\n🔍 Test Query: {query}\n")
        print("-" * 70)

        response = agent(query)
        result = extract_agent_response(response)
        print(result)
        print("-" * 70)

    print("\n" + "=" * 70)
    print("✅ DynamoDB Query Builder Agent test complete")
    print("=" * 70)
