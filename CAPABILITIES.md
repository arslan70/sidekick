# SideKick AI - Comprehensive Capabilities Guide

> A complete reference of what this agentic AI application can do for you

## 🎯 Overview

SideKick is a hierarchical multi-agent system that combines specialized AI workers to provide comprehensive enterprise assistance. Each capability leverages Amazon Bedrock's AI models with intelligent routing, real-time data access, and secure integrations.

---

## 📋 Table of Contents

1. [Calendar & Schedule Management](#1-calendar--schedule-management)
2. [Email Intelligence & Action Items](#2-email-intelligence--action-items)
3. [JIRA Project Management](#3-jira-project-management)
4. [Confluence Documentation](#4-confluence-documentation)
5. [Incident Management & Monitoring](#5-incident-management--monitoring)
6. [AWS Infrastructure Monitoring](#6-aws-infrastructure-monitoring)
7. [DynamoDB Query Intelligence](#7-dynamodb-query-intelligence)
8. [Knowledge Base & RAG](#8-knowledge-base--rag)
9. [Report Generation & Analytics](#9-report-generation--analytics)
10. [Multi-Agent Orchestration](#10-multi-agent-orchestration)
11. [Security & Guardrails](#11-security--guardrails)

---

## 1. 📅 Calendar & Schedule Management

### What It Does
Manages your daily schedule, meetings, and time commitments with intelligent conflict detection.

### Capabilities

#### View Today's Schedule
- **Example**: "What meetings do I have today?"
- Retrieves all calendar events for the current day
- Shows meeting times, durations, and attendees
- Identifies virtual vs. physical locations
- Highlights time conflicts and overlaps

#### Get Meeting Details
- **Example**: "Tell me about the Team Standup meeting"
- Fetches comprehensive meeting information
- Shows attendee list and RSVP status
- Displays meeting description and agenda
- Provides location details (Zoom links, room numbers)

#### Set Meeting Agendas
- **Example**: "Add agenda items to the Client Demo meeting"
- Updates meeting descriptions with agenda topics
- Prepares discussion points in advance
- Helps structure productive meetings

#### Smart Conflict Detection
- Automatically identifies double-booked time slots
- Highlights back-to-back meetings without breaks
- Suggests time management improvements

### Technical Details
- **Agent**: Calendar Worker (`worker_calendar.py`)
- **Model**: Amazon Nova Lite v1:0
- **Data Source**: Static demo data (Google Calendar OAuth can be added)
- **Tools**: `get_todays_calendar_events`, `get_event_details`, `set_event_agenda`

---

## 2. 📧 Email Intelligence & Action Items

### What It Does
Analyzes your inbox to extract actionable tasks, prioritize urgent items, and provide intelligent summaries.

### Capabilities

#### Recent Email Overview
- **Example**: "Show me my recent emails"
- Fetches last 10-50 emails from inbox
- Provides sender, subject, and preview
- Timestamps for quick reference
- Helps you stay on top of communications

#### Urgent Email Detection
- **Example**: "What urgent emails do I have?"
- Identifies high-priority messages
- Flags emails from executives or customers
- Detects urgency keywords (ASAP, urgent, critical)
- Prioritizes by sender authority and context

#### Intelligent Action Item Extraction
- **Example**: "Extract action items from email #12345"
- Uses AI to identify explicit and implicit tasks
- Parses natural language deadlines ("by Friday", "EOD", "next week")
- Determines priority from context and sender
- Extracts dependencies and assignees
- Provides confidence scores for each action item

#### Advanced Email Analysis
- **Explicit Actions**: "Please review the report by Friday"
- **Implicit Actions**: "I'd appreciate your feedback" → Provide feedback
- **Questions as Actions**: "Could you update the spreadsheet?" → Update spreadsheet
- **False Positive Filtering**: Ignores past actions, statements of fact, negations

#### Natural Language Date Parsing
- Relative dates: "tomorrow", "next week", "end of month"
- Time expressions: "by EOD", "by 3pm", "first thing tomorrow"
- Absolute dates: "October 15", "10/15", "Oct 15th"

### Technical Details
- **Agents**: Email Worker (`worker_email.py`), Email Action Intelligence (`worker_email_actions.py`)
- **Model**: Amazon Nova Lite v1:0
- **Data Source**: Static demo data with optional Bedrock-powered summarization
- **Tools**: `get_recent_emails`, `get_urgent_emails`, `extract_email_action_items`

---

## 3. 🎫 JIRA Project Management

### What It Does
Provides comprehensive JIRA issue tracking with both read and write capabilities, plus OAuth authentication.

### Capabilities

#### View All Issues
- **Example**: "Show me all JIRA issues"
- Lists issues across all projects
- Displays status, priority, and assignee
- Configurable limit (default 20, max 100)
- Provides total count and metadata

#### My Assigned Tasks
- **Example**: "What are my tasks?" or "Show my issues"
- Automatically fetches issues for authenticated user
- No username needed - uses OAuth identity
- Perfect for daily planning and workload management
- Shows priorities and due dates

#### High-Priority Issues
- **Example**: "What critical JIRA issues do we have?"
- Filters for Critical and High priority items
- Identifies issues nearing due dates
- Highlights blockers and urgent work
- Helps focus on time-sensitive tasks

#### Issue Details
- **Example**: "Get details for PROJ-123"
- Comprehensive issue information
- Full description and comments
- Linked pages and subtasks
- Complete history and timeline

#### Search Issues
- **Example**: "Find JIRA issues about authentication"
- Text search across issue summaries
- Relevance ranking
- Helps locate related work items

#### Filter by Status
- **Example**: "Show issues in Code Review"
- Filter by workflow status
- Common statuses: To Do, In Progress, Code Review, Testing, Done
- Track work in specific stages

#### Update Issues (Write Operations)
- **Example**: "Update PROJ-123 priority to High"
- Modify summary, description, priority
- Add comments to issues
- Change issue status (transition workflows)
- Move issues through workflow (To Do → In Progress → Done)

#### OAuth Authentication
- Secure OAuth 2.0 authentication with Atlassian
- Automatic token refresh
- Token storage via AWS Bedrock AgentCore Identity
- Seamless authentication flow

### Technical Details
- **Agent**: JIRA Worker (`worker_jira.py`)
- **Model**: Amazon Nova Lite v1:0
- **Data Source**: Real Atlassian JIRA API (when OAuth configured) or static demo data
- **Authentication**: OAuth 2.0 with automatic token refresh
- **Tools**: `get_all_jira_issues`, `get_assigned_jira_issues`, `get_high_priority_jira_issues`, `get_jira_issue_details`, `search_jira_issues`, `get_jira_issues_by_status`, `update_jira_issue`, `add_jira_comment`, `transition_jira_issue`

---

## 4. 📚 Confluence Documentation

### What It Does
Accesses and searches Confluence documentation to provide context and reference materials.

### Capabilities

#### Retrieve Specific Pages
- **Example**: "Get Confluence page 12345"
- Fetch pages by ID
- Multiple content formats (storage, view, export_view)
- Shows title, content, space info, and metadata
- Perfect for referencing documentation

#### Search Documentation
- **Example**: "Search Confluence for API documentation"
- Uses CQL (Confluence Query Language)
- Search by text, space, type, or date
- Returns matching pages with excerpts
- Configurable result limit (default 25, max 250)

#### Common CQL Patterns
- Search by text: `text ~ "keyword"`
- Search in space: `space = "PROJ" AND text ~ "keyword"`
- Search by type: `type = page AND text ~ "keyword"`
- Recent pages: `space = "PROJ" order by lastmodified desc`

#### Integration with JIRA
- Link documentation to JIRA issues
- Provide context for issue resolution
- Reference specifications and requirements

### Technical Details
- **Agent**: JIRA Worker (`worker_jira.py`) - includes Confluence tools
- **Model**: Amazon Nova Lite v1:0
- **Data Source**: Real Atlassian Confluence API (when OAuth configured) or static demo data
- **Authentication**: OAuth 2.0 (shared with JIRA)
- **Tools**: `get_confluence_page`, `search_confluence_pages`

---

## 5. 🚨 Incident Management & Monitoring

### What It Does
Monitors system incidents, outages, and issues with severity-based prioritization.

### Capabilities

#### View All Incidents
- **Example**: "Show me all incidents"
- Comprehensive incident list
- Severity levels and status
- Impact assessment
- Configurable limit (default 20, max 100)

#### Open Incidents
- **Example**: "What incidents are currently open?"
- Filters for Open and In Progress status
- Identifies ongoing issues
- Helps prioritize resolution efforts

#### Critical Incidents
- **Example**: "Show critical incidents"
- High-impact incidents only
- Affects multiple users or critical systems
- Requires immediate attention and escalation

#### Incident Details
- **Example**: "Get details for INC-042"
- Complete incident information
- Timeline of events and updates
- Root cause analysis (if available)
- Affected services and user impact
- Resolution steps and status
- Assigned team and escalation path

#### Search Incidents
- **Example**: "Find incidents related to Database"
- Keyword search in titles and descriptions
- Helps identify patterns
- Finds related incidents

#### Email-Linked Incidents
- **Example**: "Show incidents for email #12345"
- Correlates email notifications with incidents
- Helps when urgent emails reference outages

#### Visual Indicators
- 🔴 Critical severity
- 🟠 High severity
- 🟡 Medium severity
- 🟢 Low severity
- 🆕 Open status
- ⚙️ In Progress
- ✅ Resolved

### Technical Details
- **Agent**: Incident Worker (`worker_incident.py`)
- **Model**: Amazon Nova Lite v1:0
- **Data Source**: Static demo data
- **Tools**: `get_all_incidents`, `get_open_incidents`, `get_critical_incidents`, `get_incident_details`, `search_incident`, `get_incidents_for_email`

---

## 6. ☁️ AWS Infrastructure Monitoring

### What It Does
Monitors AWS services and resources with **STRICTLY READ-ONLY** operations for safety.

### Capabilities

#### EC2 Instance Monitoring
- **Example**: "List all running EC2 instances"
- View instance states and configurations
- Check instance types and sizes
- Monitor resource utilization
- Identify stopped or terminated instances

#### S3 Bucket Management
- **Example**: "What S3 buckets do we have?"
- List all S3 buckets
- Check bucket sizes and object counts
- View bucket properties and configurations
- Monitor storage costs

#### Lambda Function Monitoring
- **Example**: "Show me Lambda function configurations"
- List all Lambda functions
- View function configurations
- Check recent invocations
- Monitor execution metrics

#### DynamoDB Operations
- **Example**: "Query DynamoDB table SalesRecords"
- Read-only query and scan operations
- Get item by primary key
- Batch get multiple items
- Describe table schema and metadata

#### CloudWatch Monitoring
- **Example**: "Check CloudWatch alarms that are triggered"
- View active alarms
- Check metrics and thresholds
- Monitor service health

#### Cost & Billing
- **Example**: "What's our estimated AWS cost this month?"
- Estimate current month costs
- Review cost explorer data
- Check budget status and forecasts

#### Security & Compliance
- Review IAM roles and policies (read-only)
- Check security group configurations
- Analyze CloudTrail logs for audit
- View compliance status

#### Networking
- Describe VPCs, subnets, routing tables
- List network interfaces and connections
- Check load balancer status

### Safety Constraints

#### ✅ ALLOWED Operations
- describe_*, get_*, list_* (read operations)
- query, scan, batch_get_item (DynamoDB reads)
- head_*, lookup_*, search_*
- check_*, test_*, validate_*
- analyze_*, monitor_*, estimate_*

#### ❌ FORBIDDEN Operations
- create, delete, put, update, modify
- start, stop, terminate, reboot
- attach, detach, associate, disassociate
- invoke, execute, run, launch
- enable, disable, set, add, remove
- tag_resource, untag_resource
- Any mutative or destructive operations

### Technical Details
- **Agent**: AWS Worker (`worker_aws.py`)
- **Model**: Amazon Nova Lite v1:0
- **Data Source**: Real AWS APIs via boto3
- **Safety**: Strict read-only enforcement with operation validation
- **Tools**: `use_aws` (from strands_tools)

---

## 7. 🔍 DynamoDB Query Intelligence

### What It Does
Intelligently constructs DynamoDB queries by understanding natural language, discovering schemas, and optimizing performance.

### Capabilities

#### Schema Discovery
- **Example**: "Describe the SalesRecords table"
- Automatically discovers table structure
- Identifies partition key and sort key patterns
- Understands attribute types and naming conventions
- Retrieves table metadata (item count, size)

#### Natural Language Time Parsing
- **Example**: "Q3 2025" → 2025, Q3
- Understands various formats:
  - "Q3 2025", "third quarter of 2025", "2025 Q3"
  - "quarter 3 2025", "Q3", "2025-Q3"
  - "fourth quarter 2024", "Q4 of 2025"
- Validates quarters (rejects Q5, Q0)
- Handles year ambiguity intelligently

#### Intelligent Query Construction
- Generates optimal KeyConditionExpression
- Builds proper ExpressionAttributeValues with DynamoDB type descriptors
- Adds FilterExpression when needed
- Prefers queries over scans for performance
- Matches existing key patterns exactly

#### Aggregation Adaptation
- **Example**: "top 5 deals" → limit to 5, sort by amount
- Customizes aggregations based on request:
  - "top 10 customers" → limit to 10, group by customer
  - "regional breakdown" → group by region
  - "monthly trends" → group by month
- Uses sensible defaults when not specified

#### DynamoDB Type Descriptors
- Properly formats values:
  - String: `{"S": "value"}`
  - Number: `{"N": "123"}`
  - Boolean: `{"BOOL": true}`
- Prevents validation errors

### Example Query Specifications

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
    "average_deal_size"
  ]
}
```

### Technical Details
- **Agent**: DynamoDB Query Builder (`worker_dynamodb_query.py`)
- **Model**: Amazon Nova Lite v1:0
- **Tools**: `describe_dynamodb_table`
- **Integration**: Used by Report Worker for intelligent data fetching

---

## 8. 📖 Knowledge Base & RAG

### What It Does
Retrieves relevant information from organizational knowledge bases using Retrieval-Augmented Generation (RAG).

### Capabilities

#### Document Retrieval
- **Example**: "Find budget documents for Q4 2025"
- Searches knowledge base with semantic understanding
- Returns relevant documents with citations
- Provides relevance scores
- Includes source references

#### Template Access
- **Example**: "Get the sales report template"
- Retrieves company templates and guidelines
- Accesses standard operating procedures (SOPs)
- Finds best practices and reference materials

#### Budget Analysis
- **Example**: "Compare Q4 2025 budget request with Q3 2024 actual spend"
- Finds budget reports and actual spend documents
- Compares current requests with historical data
- Highlights key variances and trends
- Provides context on budget categories

#### Knowledge Types
- Budget documents and financial reports
- Templates and guidelines
- Standard operating procedures
- Best practices and reference materials
- Historical context and decisions
- Technical documentation

#### Smart Search Features
- Semantic search (understands meaning, not just keywords)
- Relevance scoring (minimum threshold: 0.4)
- Source citations with document IDs
- Context-aware retrieval

### Technical Details
- **Agent**: Knowledge Base Worker (`worker_kb.py`)
- **Model**: Amazon Nova Lite v1:0
- **RAG Engine**: Amazon Bedrock Knowledge Bases
- **Embeddings**: Amazon Titan Embeddings
- **Storage**: S3 bucket with documents
- **Tools**: `retrieve` (from strands_tools)

---

## 9. 📊 Report Generation & Analytics

### What It Does
Generates comprehensive business reports by combining templates from Knowledge Base with live data from AWS services.

### Capabilities

#### Sales Report Generation
- **Example**: "Generate a comprehensive Q3 2025 sales report"
- Retrieves report template from Knowledge Base
- Fetches live sales data from DynamoDB
- Calculates aggregations and metrics
- Formats professionally with clear sections

#### Report Components
- **Executive Summary**: High-level overview for leadership
- **Detailed Analysis**: Revenue metrics with context
- **Key Insights**: Pattern recognition and opportunities
- **Recommendations**: Data-driven actionable suggestions

#### Data Analysis
- Total revenue with proper formatting ($X,XXX,XXX.XX)
- Regional distribution with counts and revenue
- Product category breakdown
- Top deals with customer names
- Average deal size
- Sales rep performance summary
- Growth rates and trends

#### Template Retrieval
- **Example**: "Get the sales report template"
- Searches Knowledge Base for templates
- Supports various report types:
  - Sales reports
  - Budget reports
  - Executive summaries
  - Quarterly reviews

#### Live Data Fetching
- **Example**: "Fetch Q3 2025 sales data"
- Uses DynamoDB Query Builder for intelligent queries
- Retrieves data from DynamoDB tables
- Supports natural language time expressions
- Adapts aggregations to user needs

#### AWS Resource Data
- **Example**: "Get S3 storage costs for Q3 2025"
- Fetches infrastructure metrics
- Includes cost and billing data
- Monitors resource utilization

#### Professional Formatting
- Clear section headers with emojis (📊 📈 💡)
- Proper number formatting ($1,234,567.89)
- Percentages and growth rates
- Bullet points for readability
- Bold highlights for critical metrics
- Context for all statistics

### Workflow

1. **Understand Request**: Identify report type, period, scope
2. **Retrieve Template**: Get structured template from Knowledge Base
3. **Fetch Data**: Query DynamoDB and AWS services
4. **Generate Report**: Populate template with data
5. **Add Insights**: Highlight trends and provide recommendations

### Technical Details
- **Agent**: Report Worker (`worker_report.py`)
- **Model**: Amazon Nova Pro v1:0 (higher capability for synthesis)
- **Dependencies**: 
  - Knowledge Base Worker (templates)
  - AWS Worker (data)
  - DynamoDB Query Builder (intelligent queries)
- **Tools**: `get_report_template`, `fetch_sales_data`, `fetch_aws_resource_data`

---

## 10. 🤖 Multi-Agent Orchestration

### What It Does
Coordinates multiple specialized agents to handle complex, multi-faceted requests intelligently.

### Capabilities

#### Intelligent Delegation
- **Example**: "Help me plan my day"
- Orchestrator analyzes user intent
- Routes to appropriate worker agents
- Combines results from multiple sources
- Provides unified, coherent response

#### Parallel Tool Execution
- Calls multiple agents simultaneously when appropriate
- Example: Calendar + Email + JIRA for daily planning
- Reduces response time
- Provides comprehensive context

#### Tool Chaining
- Sequences tools logically
- Example: Knowledge Base → Report Generation
- Example: Query Builder → AWS Worker → Report Worker
- Maintains context across agent calls

#### Proactive Intelligence
- Morning greetings → Comprehensive daily briefing
- Incident queries → Include severity, impact, status
- AWS queries → Monitor resources and costs
- Report requests → Find templates and generate insights

#### User-Centric Synthesis
- Identifies conflicts and overlaps
- Extracts and prioritizes action items
- Surfaces critical issues proactively
- Combines results into coherent insights

#### Error Handling
- Graceful degradation when services unavailable
- Continues with available information
- Clear error messages with actionable guidance
- Automatic fallback to demo data when APIs unavailable

### Agent Hierarchy

```
Orchestrator Agent (Nova Pro)
├── Calendar Worker (Nova Lite)
├── Email Worker (Nova Lite)
│   └── Email Action Intelligence (Nova Lite)
├── JIRA Worker (Nova Lite)
├── Incident Worker (Nova Lite)
├── AWS Worker (Nova Lite)
├── Knowledge Base Worker (Nova Lite)
└── Report Worker (Nova Pro)
    ├── Knowledge Base Worker (templates)
    ├── AWS Worker (data)
    └── DynamoDB Query Builder (Nova Lite)
```

### Example Multi-Agent Scenarios

#### Daily Planning
**User**: "Help me plan my day"

**Orchestrator**:
1. Calls Calendar Worker → Today's meetings
2. Calls Email Worker → Urgent emails
3. Calls JIRA Worker → Assigned tasks
4. Calls Incident Worker → Critical incidents
5. Synthesizes into prioritized action plan

#### Report Generation
**User**: "Generate Q3 2025 sales report"

**Orchestrator**:
1. Calls Report Worker
2. Report Worker calls Knowledge Base Worker → Template
3. Report Worker calls Query Builder → Optimal query
4. Report Worker calls AWS Worker → Execute query
5. Report Worker synthesizes data into formatted report

### Technical Details
- **Agent**: Orchestrator (`orchestrator.py`)
- **Model**: Amazon Nova Pro v1:0 (higher reasoning capability)
- **Pattern**: Agents-as-Tools (StrandsAgents 1.10.0+)
- **Workers**: 7 specialized agents
- **Tools**: Each worker wrapped as callable tool

---

## 11. 🛡️ Security & Guardrails

### What It Does
Ensures safe, compliant, and policy-adherent AI interactions using Amazon Bedrock Guardrails.

### Capabilities

#### Content Filtering
- Blocks harmful or inappropriate content
- Prevents policy violations
- Filters sensitive information
- Protects against prompt injection attacks

#### AWS Safety Protocol
- **Strictly enforced read-only AWS operations**
- Validates every AWS operation before execution
- Rejects any mutative or destructive operations
- Explains why operations are forbidden

#### OAuth Security
- Secure token storage via AWS Bedrock AgentCore Identity
- Automatic token refresh
- Encrypted credential management
- No plaintext secrets in code

#### Data Privacy
- PII detection and handling
- Secure credential management
- Audit logging via CloudTrail
- Compliance with data protection regulations

#### Guardrail Configuration
- **Guardrail ID**: `zd4xbra1lval`
- **Version**: 1
- **Trace**: Enabled for debugging
- Applied to Orchestrator Agent

### Safety Features

#### Read-Only AWS Enforcement
```python
FORBIDDEN_OPERATIONS = [
    'create', 'delete', 'put', 'update', 'modify',
    'terminate', 'stop', 'start', 'reboot',
    'invoke', 'execute', 'run', 'launch',
    # ... and many more
]
```

#### Operation Validation
- Every AWS operation checked against whitelist
- Defensive approach: only explicitly safe operations allowed
- Clear error messages when operations rejected

#### Authentication Security
- OAuth 2.0 with PKCE
- Secure token storage in AWS
- Automatic token refresh
- No credentials in environment variables

### Technical Details
- **Guardrail**: Amazon Bedrock Guardrails
- **Token Storage**: AWS Bedrock AgentCore Identity
- **Audit**: CloudWatch Logs, CloudTrail
- **Encryption**: At rest and in transit

---

## 🎨 Usage Examples

### Example 1: Daily Planning
```
User: "Help me plan my day"

SideKick:
📅 Today's Calendar:
- 9:00 AM: Team Standup (30min)
- 2:00 PM: Client Demo (1hr)
- 3:30 PM: Code Review (1hr)

📧 Urgent Emails (2):
- CEO: Q4 Budget Review needed by EOD
- Customer: Production issue escalation

🎫 JIRA Tasks (4):
- PROJ-123: Implement feature X (In Progress)
- PROJ-124: Fix critical bug (High Priority)

🚨 Critical Incidents (1):
- INC-042: Database performance degradation

Recommended Priority:
1. Address INC-042 (critical, affecting customers)
2. Respond to CEO budget email (due today)
3. Continue PROJ-123 (in progress)
4. Prepare for Client Demo at 2pm
```

### Example 2: Sales Report Generation
```
User: "Generate a comprehensive Q3 2025 sales report with regional breakdown"

SideKick:
📊 Q3 2025 Sales Report

Executive Summary:
- Total Revenue: $2,456,789.50
- Total Deals: 127
- Average Deal Size: $19,344.80
- Growth vs Q2: +15.3%

Regional Breakdown:
- North America: $1,234,567.00 (50.2%)
- Europe: $789,012.00 (32.1%)
- Asia Pacific: $433,210.50 (17.7%)

Top 5 Deals:
1. Acme Corp - $125,000
2. TechStart Inc - $98,500
3. Global Systems - $87,300
...

Key Insights:
💡 North America showing strong growth
💡 Enterprise deals up 23% vs last quarter
💡 Average deal size increased 8%

Recommendations:
✅ Increase focus on enterprise segment
✅ Expand European sales team
✅ Replicate NA success strategies in APAC
```

### Example 3: AWS Monitoring
```
User: "What's the status of our AWS infrastructure?"

SideKick:
☁️ AWS Infrastructure Status

EC2 Instances:
- Running: 12 instances
- Stopped: 3 instances
- Total compute cost: ~$450/month

S3 Storage:
- Buckets: 8
- Total size: 2.3 TB
- Storage cost: ~$53/month

Lambda Functions:
- Active functions: 24
- Invocations (24h): 45,230
- Execution cost: ~$12/day

CloudWatch Alarms:
🔴 2 Critical alarms triggered
- High CPU on prod-web-01
- DynamoDB throttling on SalesRecords

Estimated Monthly Cost: $1,847
Budget Status: 73% of monthly budget used
```

---

## 🚀 Getting Started

### Quick Start
```bash
# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.sample .env
# Edit .env with your AWS credentials

# Run
cd app
chainlit run app.py
```

### Try These Commands
- "Help me plan my day"
- "What are my JIRA tasks?"
- "Show me critical incidents"
- "Generate Q3 2025 sales report"
- "What's our AWS cost this month?"
- "Find budget documents in the knowledge base"

---

## 📚 Documentation

- [Architecture Guide](docs/ARCH.md) - System design and patterns
- [Deployment Guide](docs/DEPLOY.md) - AWS deployment instructions
- [Development Guide](docs/RUNBOOK.md) - Local development setup
- [OAuth Setup](docs/atlassian-oauth-setup.md) - Atlassian integration
- [README](README.md) - Project overview

---

## 🎯 Key Differentiators

### 1. Hierarchical Multi-Agent Architecture
- Orchestrator coordinates 7+ specialized workers
- Each agent optimized for specific domain
- Clean separation of concerns
- Scalable and maintainable

### 2. Intelligent Query Construction
- Natural language understanding for database queries
- Automatic schema discovery
- Optimal query generation
- Adaptive aggregations

### 3. Read-Only AWS Safety
- Strictly enforced read-only operations
- Operation validation before execution
- Clear safety constraints
- No risk of accidental modifications

### 4. Secure OAuth Integration
- Real-time JIRA and Confluence access
- Automatic token refresh
- Secure credential storage
- Seamless authentication

### 5. RAG-Powered Knowledge Retrieval
- Semantic search across documents
- Relevance scoring and citations
- Template and guideline access
- Historical context retrieval

### 6. Comprehensive Report Generation
- Multi-source data integration
- Professional formatting
- Executive summaries
- Actionable insights

### 7. Bedrock Guardrails
- Content filtering and safety
- Policy compliance
- PII protection
- Audit logging

---

## 🔮 Future Enhancements

- [ ] Google Calendar OAuth integration
- [ ] Real-time email integration (Gmail, Outlook)
- [ ] Slack integration for notifications
- [ ] Advanced analytics and forecasting
- [ ] Custom report templates
- [ ] Multi-tenancy support
- [ ] Mobile app interface
- [ ] Voice interaction support

---

**Built with** ❤️ **using StrandsAgents, Chainlit, and AWS Bedrock**
