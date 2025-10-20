# Atlassian OAuth Integration - Complete Guide

## Overview

This document describes the Atlassian OAuth integration that enables real-time access to Jira and Confluence data in the SideKick AI agent.

## How It Works

### Architecture

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Chainlit UI │         │  AgentCore   │         │  Jira API    │
│   (Local)    │         │    (AWS)     │         │ (Atlassian)  │
└──────┬───────┘         └──────┬───────┘         └──────┬───────┘
       │                        │                        │
       │ 1. User authenticates  │                        │
       │────────────────────────┼───────────────────────>│
       │                        │                        │
       │ 2. Token stored locally│                        │
       │                        │                        │
       │ 3. User query + token  │                        │
       │───────────────────────>│                        │
       │                        │                        │
       │                        │ 4. Query with token    │
       │                        │───────────────────────>│
       │                        │                        │
       │                        │ 5. Real data           │
       │                        │<───────────────────────│
       │                        │                        │
       │ 6. Display real data   │                        │
       │<───────────────────────│                        │
```

### Token Flow

1. **User authenticates** in Chainlit UI via OAuth
2. **Token stored** locally in SimpleTokenManager (in-memory)
3. **User makes query** (e.g., "Show me my Jira tasks")
4. **Chainlit retrieves token** from local storage
5. **Token passed to agent** via request metadata
6. **Agent extracts token** and sets as environment variable
7. **JiraAdapter uses token** via EnvTokenManager
8. **Real Jira API called** with valid token
9. **Real data returned** to user

## Configuration

### Required Environment Variables

```bash
# Atlassian OAuth Credentials
ATLASSIAN_OAUTH_CLIENT_ID=your-client-id
ATLASSIAN_OAUTH_CLIENT_SECRET=your-client-secret
ATLASSIAN_OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback
ATLASSIAN_CLOUD_ID=your-cloud-id
ATLASSIAN_SITE_URL=your-site.atlassian.net
ATLASSIAN_DEMO_USER_ID=your-email@example.com
```

### AgentCore Environment Variables

The following environment variables are automatically passed to the AgentCore runtime (configured in `infra/stacks/agentcore_stack.py`):

- `ATLASSIAN_OAUTH_CLIENT_ID`
- `ATLASSIAN_OAUTH_CLIENT_SECRET`
- `ATLASSIAN_OAUTH_REDIRECT_URI`
- `ATLASSIAN_CLOUD_ID`
- `ATLASSIAN_SITE_URL`
- `ATLASSIAN_DEMO_USER_ID`

## Implementation Details

### Key Components

#### 1. Chainlit UI (`app/app.py`)
- Handles OAuth authentication flow
- Stores tokens in SimpleTokenManager
- Passes tokens to agent via metadata

#### 2. Agent Runtime (`agent_runtime.py`)
- Receives token in request metadata
- Sets token as environment variable
- Makes it available to tools

#### 3. EnvTokenManager (`tools/env_token_manager.py`)
- Retrieves token from environment variable
- Provides token to API clients
- Simple, stateless implementation

#### 4. Jira Adapter (`tools/jira_adapter.py`)
- Checks for token in environment
- Uses EnvTokenManager when available
- Falls back to static data if no token

#### 5. Confluence Adapter (`tools/confluence_adapter.py`)
- Same pattern as Jira adapter
- Supports real-time Confluence access

### Token Manager Priority

The adapters use this priority order for token managers:

1. **EnvTokenManager** - Token from environment variable (passed from UI)
2. **AgentCoreTokenManager** - Token from AgentCore Identity (not configured)
3. **SimpleTokenManager** - In-memory storage (fallback)

## Usage

### Authentication Flow

1. **Start Chainlit UI:**
   ```bash
   python run_app.py
   ```

2. **Authenticate with Atlassian:**
   - Click the OAuth link in the welcome message
   - Authorize the app in Atlassian
   - Complete the OAuth flow

3. **Use real Jira data:**
   ```
   "Show me all my Jira tasks"
   "What are my high priority issues?"
   "Search for issues about authentication"
   ```

### Special Commands

- `/get-token` - Display current access token (for debugging)
- `/check-auth` - Check authentication status

## Troubleshooting

### Issue: Agent returns fake data

**Cause:** Token not being passed or agent hasn't updated

**Solution:**
1. Verify authentication: Use `/check-auth` command
2. Check logs for "Passing Atlassian access token to agent"
3. Wait 2-5 minutes after deployment for AgentCore to update

### Issue: "No valid access token" error

**Cause:** Token expired or invalid

**Solution:**
1. Re-authenticate in Chainlit UI
2. Click the OAuth link again
3. Complete the authorization flow

### Issue: Rate limit errors

**Cause:** Atlassian API rate limits exceeded

**Solution:**
- Wait a few minutes
- Reduce query frequency
- Check Atlassian rate limit documentation

## Monitoring

### Chainlit Logs

Look for:
```
✅ Passing Atlassian access token to agent
✅ OAuth handler initialized successfully
```

### Agent Logs (CloudWatch)

```bash
aws logs tail /aws/bedrock/agentcore/sidekick-agentcore-dev --follow --region eu-central-1
```

Look for:
```
✅ Atlassian access token received and set in environment
✅ Using Environment Token Manager for JIRA
✅ Retrieved access token from environment
JIRA adapter initialized with real API (OAuth credentials detected)
```

## Security Considerations

### Current Implementation (Hackathon Demo)

- ✅ Token passed over HTTPS
- ✅ Token only in memory, not persisted
- ✅ Token scoped to user session
- ⚠️ Token passed on every request
- ⚠️ No automatic token refresh

### Production Recommendations

For production deployment:

1. **Use AgentCore Identity:**
   - Proper token storage service
   - Supports token refresh and revocation
   - Per-user token management

2. **Use AWS Secrets Manager:**
   - Encrypted token storage
   - Automatic rotation
   - Audit logging

3. **Implement token encryption:**
   - Encrypt tokens in transit
   - Use AWS KMS for encryption keys

4. **Add token rotation:**
   - Automatic token refresh
   - Handle token expiration gracefully

## Files Modified

### Core Implementation
- `app/app.py` - Token passing from UI to agent
- `agent_runtime.py` - Token extraction and environment setup
- `tools/env_token_manager.py` - Environment variable token manager
- `tools/jira_adapter.py` - Token manager selection
- `tools/confluence_adapter.py` - Token manager selection

### Infrastructure
- `infra/app.py` - Load OAuth credentials from .env
- `infra/stacks/agentcore_stack.py` - Pass credentials to AgentCore

## Deployment

### Build and Deploy Agent

```bash
# 1. Authenticate with ECR
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 275666109134.dkr.ecr.eu-central-1.amazonaws.com

# 2. Build Docker image
docker build -t sidekick-agent-dev:latest -f Dockerfile.agents .

# 3. Tag for ECR
docker tag sidekick-agent-dev:latest 275666109134.dkr.ecr.eu-central-1.amazonaws.com/sidekick-agent-dev:latest

# 4. Push to ECR
docker push 275666109134.dkr.ecr.eu-central-1.amazonaws.com/sidekick-agent-dev:latest

# 5. Wait 2-5 minutes for AgentCore to pull new image
```

### Deploy Infrastructure Changes

```bash
cd infra
cdk deploy sidekick-agentcore-dev
```

## Testing

### Verify Real Data Access

1. Authenticate with Atlassian in Chainlit UI
2. Ask: "Show me all my Jira tasks"
3. Verify real task keys (e.g., PROJ-123, not DEMO-1)
4. Check assignees and statuses are real

### Verify Token Passing

1. Check Chainlit logs for token passing message
2. Check CloudWatch logs for token receipt
3. Use `/get-token` to verify token is available

## Support

For issues or questions:

1. Check logs (Chainlit terminal and CloudWatch)
2. Verify authentication status with `/check-auth`
3. Re-authenticate if token expired
4. Review this documentation

## Summary

The Atlassian OAuth integration enables real-time access to Jira and Confluence data by:

1. Authenticating users via OAuth in the Chainlit UI
2. Passing tokens from UI to agent via request metadata
3. Using tokens to call real Atlassian APIs
4. Returning real data instead of dummy/fake data

This provides a seamless experience where users can interact with their actual Jira tasks and Confluence pages through natural language queries.

🎉 **Result:** Real Jira and Confluence integration working!
