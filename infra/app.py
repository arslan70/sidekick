"""
AWS CDK application entry point for SideKick infrastructure.

Deploys:
- Knowledge Base Stack (S3 buckets for Bedrock KB - KB created manually in console)
- AgentCore Stack (Bedrock Agent with CfnAgent, IAM, ECR)
- App Config Stack (SSM Parameters, Secrets)
- ECS Stack (Chainlit UI on Fargate)
"""

# !/usr/bin/env python3

import os

import aws_cdk as cdk
from stacks.agentcore_stack import AgentCoreStack
from stacks.app_config_stack import AppConfigStack
from stacks.ecs_stack import EcsStack
from stacks.knowledge_base_stack import KnowledgeBaseStack

# Create CDK app
app = cdk.App()

# Define environment for eu-central-1 region
# Uses CDK_DEFAULT_ACCOUNT and CDK_DEFAULT_REGION environment variables
# which are automatically set by CDK CLI from your AWS credentials
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "eu-central-1"),
)

# Load environment variables from .env file if it exists
from pathlib import Path
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
    print(f"✅ Loaded environment variables from {env_file}")

# Stack configuration
stack_config = {
    "project_name": "sidekick",
    "environment": os.getenv("ENVIRONMENT", "dev"),
    # Chainlit authentication
    "chainlit_auth_secret": os.getenv("CHAINLIT_AUTH_SECRET", ""),
    # AWS Bedrock Configuration
    "knowledge_base_id": os.getenv("KNOWLEDGE_BASE_ID", ""),
    # Bedrock Guardrails Configuration (optional)
    "bedrock_guardrail_id": os.getenv("BEDROCK_GUARDRAIL_ID", ""),
    "bedrock_guardrail_version": os.getenv("BEDROCK_GUARDRAIL_VERSION", "1"),
    # Atlassian OAuth Configuration (for real JIRA/Confluence access)
    "atlassian_oauth_client_id": os.getenv("ATLASSIAN_OAUTH_CLIENT_ID", ""),
    "atlassian_oauth_client_secret": os.getenv("ATLASSIAN_OAUTH_CLIENT_SECRET", ""),
    "atlassian_oauth_redirect_uri": os.getenv("ATLASSIAN_OAUTH_REDIRECT_URI", ""),
    "atlassian_cloud_id": os.getenv("ATLASSIAN_CLOUD_ID", ""),
    "atlassian_site_url": os.getenv("ATLASSIAN_SITE_URL", ""),
    "atlassian_demo_user_id": os.getenv("ATLASSIAN_DEMO_USER_ID", "yetanotherarslan@gmail.com"),
    # HTTPS/SSL Configuration (optional)
    "certificate_arn": os.getenv("ACM_CERTIFICATE_ARN", ""),
    "domain_name": os.getenv("DOMAIN_NAME", ""),
}

# Deploy Knowledge Base Stack (S3 buckets only - KB created manually)
kb_stack = KnowledgeBaseStack(
    app,
    f"{stack_config['project_name']}-kb-{stack_config['environment']}",
    env=env,
    description="S3 buckets for Bedrock Knowledge Base (KB created manually in console)",
    config=stack_config,
)

# Deploy App Config Stack (for SSM parameters and secrets)
config_stack = AppConfigStack(
    app,
    f"{stack_config['project_name']}-config-{stack_config['environment']}",
    env=env,
    description="Configuration and secrets for SideKick",
    config=stack_config,
)

# Deploy AgentCore Stack (Bedrock Agent with CfnAgent)
agentcore_stack = AgentCoreStack(
    app,
    f"{stack_config['project_name']}-agentcore-{stack_config['environment']}",
    env=env,
    description="Bedrock Agent deployment for SideKick multi-agent system",
    config=stack_config,
)

# Deploy ECS Stack (Chainlit UI)
# Pass AgentCore outputs to ECS stack
ecs_stack = EcsStack(
    app,
    f"{stack_config['project_name']}-ecs-{stack_config['environment']}",
    env=env,
    description="ECS Fargate deployment for Chainlit UI",
    config=stack_config,
    agent_runtime_id=agentcore_stack.runtime_id,
    agent_runtime_arn=agentcore_stack.runtime_arn,
    create_service=True,  # Enable ECS service deployment
    certificate_arn=stack_config.get("certificate_arn") or None,
    domain_name=stack_config.get("domain_name") or None,
)

# Add dependencies
agentcore_stack.add_dependency(kb_stack)
agentcore_stack.add_dependency(config_stack)
ecs_stack.add_dependency(agentcore_stack)  # ECS needs AgentCore outputs

# Add tags to all stacks
for stack in [kb_stack, config_stack, agentcore_stack, ecs_stack]:
    cdk.Tags.of(stack).add("Project", stack_config["project_name"])
    cdk.Tags.of(stack).add("Environment", stack_config["environment"])
    cdk.Tags.of(stack).add("ManagedBy", "CDK")

# Synthesize CloudFormation templates
app.synth()
