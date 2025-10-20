# Demo Scenarios Guide - SideKick AI Hackathon Submission

## Overview

This document provides detailed instructions for executing the four pre-configured demo scenarios designed to showcase SideKick AI's capabilities for the AWS AI Agent Global Hackathon.

**Purpose**: Enable smooth, professional demonstrations that highlight multi-agent orchestration, AWS service integration, and real-world business value.

**Target Duration**: 2-3 minutes per scenario

---

## Scenario 1: Proactive Daily Briefing (Multi-Agent Orchestration)

### Business Context
Sarah Chen, an engineering manager, starts her workday and needs a comprehensive overview of her priorities across multiple systems.

### User Prompt
```
"Help me plan my day"
```

### Expected Agent Orchestration
The system will execute **5 agents in parallel**:

1. **Calendar Worker** → Fetches today's meetings
2. **Email Worker** → Extracts urgent action items
3. **JIRA Worker** → Lists assigned tasks and blockers
4. **Incident Worker** → Checks overnight incidents
5. **AWS Worker** → Reviews infrastructure alerts

### Expected Output Structure
```
**Your Day at a Glance (October 19, 2025)**

🚨 **Urgent Actions (Next 2 Hours):**
1. [11:00 AM] Approve Q4 budget (CFO request - deadline today 5 PM)
2. [10:00 AM] Review database connection timeout incident (INC-2025-1847)
3. [09:30 AM] Unblock ENG-123 (OAuth implementation needs security review)

📅 **Today's Meetings:**
- 09:00-10:30: Sprint Planning - Team Phoenix (Conference Room A)
- 14:00-15:00: Architecture Review - Security Enhancements (High Priority)
- 11:00-11:30: 1:1 with CTO - Q4 Planning
- 16:00-17:00: Incident Post-Mortem - INC-001

📧 **Email Action Items:**
- Prepare proposal for TechCorp by Friday, October 6
- Update password (security requirement - deadline Oct 4)
- Review and approve Q4 budget breakdown

📋 **JIRA Tasks:**
- ENG-123: OAuth 2.0 Authentication (In Progress, blocked by security review)
- ENG-124: Database Query Performance (Code Review)
- ENG-125: Automated Sales Report Generation (To Do)
- ENG-126: CI/CD Pipeline Timeout Issues (In Progress)

⚠️ **Critical Incident:**
- INC-2025-1847: Database Connection Timeouts (Investigating)
  - Status: Connection pool exhaustion suspected
  - Impact: 5,000 users affected
  - Action: Review troubleshooting runbook and join war room

**Estimated Time Allocation:**
- Urgent actions: 2 hours
- Meetings: 4 hours
- Development work: 2 hours
- Buffer for incidents: 30 minutes
```

### Key Demonstration Points
- ✅ **Parallel Execution**: All 5 agents run simultaneously
- ✅ **Multi-Source Aggregation**: Data from Calendar, Email, JIRA, Incidents, AWS
- ✅ **Intelligent Prioritization**: Urgent items surfaced first
- ✅ **Time Estimation**: Realistic time allocation
- ✅ **Actionable Insights**: Clear next steps

### Success Criteria
- Response time: <10 seconds
- All 5 agents execute successfully
- Output is coherent and prioritized
- Demonstrates real-world business value

---

## Scenario 2: Incident Resolution (Multi-Source Information Aggregation)

### Business Context
A critical production incident requires rapid information gathering from multiple sources to diagnose and resolve.

### User Prompt
```
"We have a critical incident - database connection timeouts in production. Help me troubleshoot."
```

### Expected Agent Orchestration
The system will execute **4 agents**:

1. **Incident Worker** → Retrieves incident details (INC-2025-1847)
2. **Confluence Worker** → Fetches relevant runbooks (if configured)
3. **Knowledge Base Worker** → Retrieves troubleshooting documentation
4. **AWS Worker** → Checks RDS metrics (read-only)

### Expected Output Structure
```
**Incident Analysis: Database Connection Timeouts**

📋 **Incident Details:**
- ID: INC-2025-1847
- Severity: Critical
- Status: Investigating
- Reported: 2025-10-18 14:23 UTC
- Impact: 5,000 users experiencing 504 Gateway Timeout errors
- Affected Services: API Gateway, Database Connection Pool, User Authentication

**Timeline:**
- 14:23 - Connection timeout errors detected
- 14:25 - Automatic alerts sent
- 14:28 - War room established (#incident-2025-1847)
- 14:35 - Database metrics: connection pool at 98% capacity
- 14:45 - Reviewing code changes from last deployment

🔍 **Troubleshooting Steps (from Knowledge Base):**

**Immediate Actions (First 5 Minutes):**
1. Verify current connection count:
   - Check CloudWatch metrics for DatabaseConnections
   - Normal: 50-150 connections
   - Critical: >250 connections (pool exhaustion)

2. Establish war room:
   - Slack channel: #incident-2025-1847 (already created)
   - Update status page
   - Notify stakeholders

3. Gather initial data:
   - Recent deployments (last 24 hours)
   - Database CPU and memory metrics
   - Application error logs

**Diagnostic Steps:**

Step 1: Check Connection Pool Status
```sql
SELECT COUNT(*) as total_connections, state, application_name
FROM pg_stat_activity
WHERE datname = 'production'
GROUP BY state, application_name
ORDER BY total_connections DESC;
```

Step 2: Investigate Connection Leaks
- Review code changes from last deployment
- Check for missing connection.close() in error handling
- Verify transaction timeout settings

Step 3: Check Database Performance
- CPU utilization: Should be <70%
- Memory: Should have >20% free
- Cache hit ratio: Should be >95%

**Resolution Strategies:**

Option 1: Rollback Recent Deployment (Fastest)
- If issue started after deployment
- Expected resolution: 5-10 minutes

Option 2: Increase Connection Pool (Temporary)
- For legitimate traffic spike
- Warning: Investigate root cause

Option 3: Kill Long-Running Queries
- Only after confirming safe to terminate

📊 **AWS Metrics (Read-Only Check):**
- RDS Instance: prod-db-primary (db.r5.2xlarge)
- Current Connections: 4,850 / 5,000 (97% capacity)
- CPU Utilization: 35.8% (normal)
- Memory: 48.2% (normal)
- Recent Deployment: api-gateway service updated 2 hours ago

**Recommendation:**
Based on timeline correlation, the issue started shortly after the api-gateway deployment. 
Recommend Option 1: Rollback to previous version while investigating connection leak.

**Next Steps:**
1. Rollback api-gateway service to previous task definition
2. Monitor connection count for improvement (should decrease within 5-10 min)
3. Review code changes for missing connection cleanup
4. Schedule post-mortem meeting within 48 hours
```

### Key Demonstration Points
- ✅ **Multi-Source Aggregation**: Incident data + Knowledge Base + AWS metrics
- ✅ **Comprehensive Analysis**: Timeline, diagnostics, resolution strategies
- ✅ **Read-Only Safety**: AWS metrics checked without making changes
- ✅ **Actionable Recommendations**: Clear next steps with rationale
- ✅ **Real-World Value**: 30 minutes of manual research → seconds

### Success Criteria
- Response time: <15 seconds
- Incident details retrieved accurately
- Troubleshooting steps from Knowledge Base
- AWS metrics included (read-only)
- Clear resolution recommendations

---

## Scenario 3: AWS Cost Optimization Analysis (Business Value + Safety)

### Business Context
Engineering leadership needs to identify cost optimization opportunities while maintaining read-only safety.

### User Prompt
```
"Analyze our AWS costs and suggest optimizations"
```

### Expected Agent Orchestration
The system will execute **4 agents**:

1. **AWS Worker** → Lists resources with cost tags (read-only)
2. **DynamoDB Query Builder** → Constructs query for historical cost data
3. **AWS Worker** → Fetches cost data from DynamoDB
4. **Knowledge Base Worker** → Retrieves optimization best practices

### Expected Output Structure
```
**AWS Cost Optimization Analysis**

💰 **Current Monthly Spend:** $4,235.67
**Projected Month-End:** $4,850.00
**Last Month:** $4,120.35 (+2.8% increase)

**Cost Breakdown by Service:**
- EC2: $2,847.50 (67%)
- S3: $892.15 (21%)
- RDS: $496.02 (12%)
- Lambda: $170.50
- Data Transfer: $245.30
- CloudWatch: $85.20
- Other: $499.00

**Cost Breakdown by Environment:**
- Production: $3,850.00 (91%)
- Development: $285.67 (7%)
- Staging: $100.00 (2%)

---

🔧 **High-Impact Optimization Opportunities**

**1. EC2 Right-Sizing (Priority: High)**
**Potential Savings: $670.92/month**

Underutilized Instances:
- i-0abc123def456789 (m5.2xlarge): 15.3% avg CPU
  → Recommendation: Downgrade to m5.large
  → Savings: $140.16/month

- i-0def456ghi789012 (m5.2xlarge): 18.7% avg CPU
  → Recommendation: Downgrade to m5.large
  → Savings: $140.16/month

- i-0ghi789jkl012345 (c5.4xlarge): 25.4% avg CPU
  → Recommendation: Downgrade to c5.xlarge or use Spot Instances
  → Savings: $390.60/month

**2. Reserved Instances (Priority: High)**
**Potential Savings: $576.64/month**

Steady-State Workloads (running 24/7):
- i-0jkl012mno345678 (r5.xlarge): Well-sized, 45% CPU
  → Recommendation: Purchase 1-year Reserved Instance
  → Savings: $80.64/month (35% discount)

- prod-db-primary (db.r5.2xlarge): Production database
  → Recommendation: Purchase 1-year Reserved Instance
  → Savings: $496.00/month (50% discount)

**3. S3 Storage Optimization (Priority: Medium)**
**Potential Savings: $67.45/month**

- acmecorp-prod-data (450 GB): Infrequent access pattern
  → Recommendation: Enable Intelligent-Tiering
  → Savings: $5.18/month

- acmecorp-logs (1,250 GB): Archive access pattern
  → Recommendation: Move to Glacier Instant Retrieval after 90 days
  → Savings: $23.77/month

- acmecorp-backups (3,500 GB): Long-term archive
  → Recommendation: Move objects >365 days to Deep Archive
  → Savings: $38.50/month

**4. Development Resources (Priority: Medium)**
**Potential Savings: $93.02/month**

- i-0mno345pqr678901 (t3.medium): Dev server, 8.5% CPU
  → Recommendation: Stop outside business hours (8 AM - 6 PM)
  → Savings: $18.14/month

- dev-db (db.t3.large): Development database, 12.3% CPU
  → Recommendation: Stop outside business hours or migrate to Aurora Serverless
  → Savings: $74.88/month

---

📊 **Total Optimization Potential**

**Monthly Savings:** $1,472.26
**Annual Savings:** $17,667.12
**Savings Percentage:** 34.8%

**Implementation Effort:** Low to Medium
**Risk Level:** Low (all recommendations tested and proven)

---

⚠️ **Read-Only Safety Enforced**

These are recommendations only. No changes have been made to your infrastructure.

To implement:
1. Review recommendations with infrastructure team
2. Test right-sizing in staging environment first
3. Evaluate Reserved Instance commitment (1-year vs 3-year)
4. Set up cost anomaly alerts for ongoing monitoring

**Next Steps:**
- [ ] Schedule cost optimization review meeting
- [ ] Create Jira tickets for each optimization
- [ ] Test instance downsizing in staging
- [ ] Evaluate Reserved Instance purchase
- [ ] Implement S3 lifecycle policies
- [ ] Set up automated start/stop for dev resources
```

### Key Demonstration Points
- ✅ **Business Value Analysis**: Clear ROI with dollar amounts
- ✅ **Multi-Source Data**: AWS resources + historical costs + best practices
- ✅ **Prioritized Recommendations**: High/Medium/Low priority
- ✅ **Read-Only Safety**: Explicitly states no changes made
- ✅ **Actionable Next Steps**: Clear implementation path

### Safety Demonstration
If user asks: **"Terminate the underutilized instances"**

Expected Response:
```
❌ **Operation Blocked by Read-Only Safety Enforcement**

I cannot terminate EC2 instances. SideKick AI enforces strictly read-only operations 
for all AWS infrastructure commands to prevent accidental changes.

**What I can do:**
- Analyze resource utilization
- Provide optimization recommendations
- Calculate potential savings
- Generate reports

**What I cannot do:**
- Terminate instances
- Modify configurations
- Delete resources
- Change security groups
- Update IAM policies

**To implement changes:**
Please review the recommendations with your team and execute changes through:
- AWS Console
- AWS CLI with appropriate permissions
- Infrastructure as Code (Terraform, CloudFormation, CDK)

This safety feature ensures zero risk of accidental infrastructure changes.
```

### Success Criteria
- Response time: <20 seconds
- Cost data retrieved from DynamoDB
- Optimization recommendations from Knowledge Base
- Clear savings calculations
- Read-only safety explicitly stated
- Safety demonstration blocks destructive operations

---

## Scenario 4: JIRA Story Refinement (AI-Powered Content Generation)

### Business Context
A product manager needs to refine a JIRA task with proper user story structure and acceptance criteria.

### User Prompt
```
"Refine JIRA task ENG-123 with proper acceptance criteria"
```

### Expected Agent Orchestration
The system will execute **3 agents**:

1. **JIRA Worker** → Fetches task details via OAuth
2. **Confluence Worker** → Retrieves user story best practices (if configured)
3. **Knowledge Base Worker** → Gets EARS format examples and authentication patterns

### Expected Output Structure
```
**JIRA Task Refinement: ENG-123**

**Original Task:**
- Key: ENG-123
- Summary: Implement OAuth 2.0 Authentication for Enterprise API
- Status: In Progress
- Description: Add OAuth 2.0 support to replace legacy API key authentication. 
  This is blocking the TechStart Inc deal.
- Blocked by: Need security review from InfoSec team

---

**Refined User Story:**

As an enterprise API consumer,
I want to authenticate using OAuth 2.0 authorization code flow,
So that I can securely access the API without sharing long-lived credentials

---

**Glossary:**
- **Authentication System**: The subsystem responsible for verifying API client identity
- **OAuth 2.0**: Industry-standard protocol for authorization (RFC 6749)
- **Authorization Code Flow**: OAuth grant type for server-side applications
- **Access Token**: Short-lived credential for API access (1-hour expiration)
- **Refresh Token**: Long-lived credential for obtaining new access tokens (90-day expiration)
- **API Client**: Third-party application consuming the Enterprise API

---

**Acceptance Criteria (EARS Format):**

1. **WHEN** an API client initiates OAuth flow, **THE** Authentication System **SHALL** redirect to authorization page within 500 milliseconds

2. **WHEN** a user approves authorization, **THE** Authentication System **SHALL** generate authorization code valid for 10 minutes

3. **WHEN** an API client exchanges authorization code for tokens, **THE** Authentication System **SHALL** return access token and refresh token within 2 seconds

4. **WHEN** an API client presents valid access token, **THE** API Gateway **SHALL** authenticate and process the request

5. **IF** an access token is expired, **THEN THE** API Gateway **SHALL** return HTTP 401 with error code "token_expired"

6. **WHEN** an API client uses refresh token, **THE** Authentication System **SHALL** issue new access token and rotate refresh token

7. **THE** Authentication System **SHALL** support token revocation endpoint per RFC 7009

8. **THE** Authentication System **SHALL** encrypt all tokens using AES-256

9. **WHEN** a token is revoked, **THE** Authentication System **SHALL** invalidate within 30 seconds across all API servers

10. **THE** Authentication System **SHALL** log all token issuance and revocation events with timestamp and client identifier

11. **WHERE** the API client requests specific scopes, **THE** Authentication System **SHALL** validate and include granted scopes in access token

12. **THE** Authentication System **SHALL** support PKCE (Proof Key for Code Exchange) per RFC 7636 for enhanced security

---

**Technical Considerations:**

**Security:**
- Use bcrypt for client secret hashing (cost factor 12)
- Implement rate limiting: 10 token requests per minute per client
- Add CAPTCHA after 3 failed authorization attempts
- Support PKCE for mobile and SPA clients
- Rotate refresh tokens on each use

**Performance:**
- Cache active tokens in Redis (1-hour TTL)
- Use JWT format for stateless token validation
- Implement token introspection endpoint for validation

**Compliance:**
- Follow OAuth 2.0 RFC 6749 specification
- Implement OAuth 2.0 Security Best Practices (RFC 8252)
- Support token revocation (RFC 7009)
- Log all authentication events for audit trail

**Integration:**
- Update API documentation with OAuth flow diagrams
- Provide client libraries (Python, JavaScript, Java)
- Create migration guide from API keys to OAuth
- Maintain backward compatibility with API keys for 6 months

---

**Definition of Done:**

- [ ] All acceptance criteria implemented and tested
- [ ] Unit tests written with >80% coverage
- [ ] Integration tests for complete OAuth flow
- [ ] Security review completed by InfoSec team
- [ ] API documentation updated with OAuth examples
- [ ] Client migration guide published
- [ ] Load testing completed (1000 token requests/second)
- [ ] Deployed to staging environment
- [ ] User acceptance testing with TechStart Inc
- [ ] Production deployment approved

---

**Estimated Effort:** 8 story points (2 weeks)

**Dependencies:**
- InfoSec security review (blocking)
- API documentation team availability
- Redis cluster for token caching

**Related Links:**
- OAuth 2.0 Implementation Guide (Confluence)
- API Security Best Practices (Knowledge Base)
- TechStart Inc Enterprise Deal (Salesforce)
```

### Key Demonstration Points
- ✅ **OAuth Integration**: Real-time JIRA API access
- ✅ **AI-Powered Generation**: Professional user story from minimal input
- ✅ **EARS Format**: Proper acceptance criteria structure
- ✅ **Comprehensive**: Glossary, technical considerations, DoD
- ✅ **Real-World Value**: Hours of manual work → seconds

### Success Criteria
- Response time: <15 seconds
- JIRA task fetched via OAuth
- User story follows proper format
- Acceptance criteria use EARS patterns
- Technical considerations included
- Definition of Done defined

---

## Pre-Demo Checklist

### Data Verification
- [ ] Calendar events updated for October 19, 2025
- [ ] Email data includes urgent Q4 budget request
- [ ] JIRA tasks include ENG-123 with OAuth details
- [ ] Incident INC-2025-1847 is active
- [ ] AWS resources mock data is loaded
- [ ] Knowledge Base documents are uploaded and indexed

### System Verification
- [ ] All agents are deployed and accessible
- [ ] OAuth credentials are configured (if using real JIRA)
- [ ] Knowledge Base retrieval is working
- [ ] DynamoDB sales data is populated
- [ ] Chainlit UI is running and accessible

### Test Execution
- [ ] Test Scenario 1: "Help me plan my day"
- [ ] Test Scenario 2: "Database connection timeouts"
- [ ] Test Scenario 3: "Analyze AWS costs"
- [ ] Test Scenario 4: "Refine JIRA task ENG-123"
- [ ] Test Safety Demo: "Terminate underutilized instances"

### Timing Verification
- [ ] Scenario 1 completes in <10 seconds
- [ ] Scenario 2 completes in <15 seconds
- [ ] Scenario 3 completes in <20 seconds
- [ ] Scenario 4 completes in <15 seconds
- [ ] All scenarios produce coherent, professional output

---

## Troubleshooting

### Issue: Agents Not Responding
**Solution**: Check agent deployment status, verify environment variables

### Issue: Knowledge Base Returns No Results
**Solution**: Verify documents are uploaded and indexed, check retrieval query

### Issue: OAuth Flow Fails
**Solution**: Verify credentials in Secrets Manager, check redirect URI configuration

### Issue: DynamoDB Query Fails
**Solution**: Verify table exists, check IAM permissions, validate query syntax

### Issue: Response Too Slow
**Solution**: Check agent execution logs, optimize prompts, verify AWS service quotas

---

**Document Owner**: Hackathon Demo Team  
**Last Updated**: October 2025  
**Questions?**: Contact demo-team@acmecorp.com
