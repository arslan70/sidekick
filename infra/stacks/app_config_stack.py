"""
App Config Stack - Configuration and secrets management.

Creates:
- SSM Parameters for non-sensitive config
- Secrets Manager secrets for sensitive data
"""

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class AppConfigStack(Stack):
    """Stack for application configuration and secrets."""

    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = config["project_name"]
        environment = config["environment"]

        # Create SSM parameters for non-sensitive configuration

        # Atlassian MCP URL
        atlassian_mcp_url_param = ssm.StringParameter(
            self,
            "AtlassianMcpUrl",
            parameter_name=f"/{project_name}/{environment}/atlassian/mcp-url",
            string_value="https://your-mcp-server.example.com",  # Placeholder
            description="Atlassian Remote MCP Server URL",
        )

        # Atlassian Site
        atlassian_site_param = ssm.StringParameter(
            self,
            "AtlassianSite",
            parameter_name=f"/{project_name}/{environment}/atlassian/site",
            string_value="your-site.atlassian.net",  # Placeholder
            description="Atlassian site URL",
        )

        # Create Secrets Manager secret for sensitive Atlassian OAuth credentials
        atlassian_secret = secretsmanager.Secret(
            self,
            "AtlassianSecret",
            secret_name=f"{project_name}/{environment}/atlassian-oauth",
            description="Atlassian OAuth credentials for MCP server",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"client_id": "placeholder"}',
                generate_string_key="client_secret",
            ),
        )

        # Create Secrets Manager secret for Chainlit authentication credentials
        # Note: Password is auto-generated on first deployment for security
        # Update the secret value after deployment using AWS CLI:
        # aws secretsmanager update-secret --secret-id "sidekick/dev/chainlit-auth" \
        #   --secret-string '{"demo_username": "demo", "demo_password": "your-password", "admin_username": "admin", "admin_password": ""}' \
        #   --region eu-central-1
        chainlit_auth_secret = secretsmanager.Secret(
            self,
            "ChainlitAuthSecret",
            secret_name=f"{project_name}/{environment}/chainlit-auth",
            description="Chainlit authentication credentials (demo and admin users)",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"demo_username": "demo", "admin_username": "admin"}',
                generate_string_key="demo_password",
            ),
        )

        # Outputs
        CfnOutput(
            self,
            "AtlassianMcpUrlParam",
            value=atlassian_mcp_url_param.parameter_name,
            description="SSM Parameter for Atlassian MCP URL",
        )

        CfnOutput(
            self,
            "AtlassianSiteParam",
            value=atlassian_site_param.parameter_name,
            description="SSM Parameter for Atlassian site",
        )

        CfnOutput(
            self,
            "AtlassianSecretArn",
            value=atlassian_secret.secret_arn,
            description="Secrets Manager ARN for Atlassian OAuth",
            export_name=f"{project_name}-atlassian-secret-{environment}",
        )

        CfnOutput(
            self,
            "ChainlitAuthSecretArn",
            value=chainlit_auth_secret.secret_arn,
            description="Secrets Manager ARN for Chainlit authentication",
            export_name=f"{project_name}-chainlit-auth-secret-{environment}",
        )

        # Store secret ARNs for use in other stacks
        self.atlassian_secret = atlassian_secret
        self.chainlit_auth_secret = chainlit_auth_secret


"""
Production Implementation Note:

After deploying this stack, update the SSM parameters and secrets with actual values:

1. Update Atlassian MCP URL:
   ```bash
   aws ssm put-parameter \
     --name "/daily-planner/dev/atlassian/mcp-url" \
     --value "https://your-actual-mcp-server.com" \
     --overwrite
   ```

2. Update Atlassian OAuth credentials:
   ```bash
   aws secretsmanager update-secret \
     --secret-id "daily-planner/dev/atlassian-oauth" \
     --secret-string '{"client_id":"actual_id","client_secret":"actual_secret"}'
   ```

3. Grant access to these resources in the Agent Runtime IAM role.
"""
