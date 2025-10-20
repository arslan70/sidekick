"""
AgentCore Stack - Amazon Bedrock AgentCore deployment.

Creates:
- ECR repository for agent container images
- IAM role with Bedrock, DynamoDB, S3, Secrets Manager permissions
- Bedrock AgentCore using containerized agent runtime
- Agent Alias for stable production endpoint
- Outputs AgentId and AliasId for ECS stack consumption
"""

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from constructs import Construct


class AgentCoreStack(Stack):
    """Stack for Bedrock AgentCore agent deployment."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = config["project_name"]
        environment = config["environment"]
        # AgentCore runtime name must match pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}
        # Cannot contain hyphens, only underscores
        agent_name = f"{project_name}_agent_{environment}"
        # ECR repository name can have hyphens
        ecr_repo_name = f"{project_name}-agent-{environment}"

        # ===================================================================
        # ECR Repository for Agent Container Images
        # ===================================================================
        # Import existing ECR repository (created in previous deployment)
        self.ecr_repository = ecr.Repository.from_repository_name(
            self,
            "AgentEcrRepository",
            repository_name=ecr_repo_name,
        )

        # ===================================================================
        # IAM Role for Bedrock Agent
        # ===================================================================
        self.agent_role = iam.Role(
            self,
            "BedrockAgentRole",
            role_name=f"{ecr_repo_name}-role",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description=f"IAM role for {agent_name} Bedrock AgentCore Runtime",
        )

        # Bedrock Model Access
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:GetFoundationModel",
                    "bedrock:ListFoundationModels",
                ],
                resources=[
                    # Allow access to foundation models in any region (for cross-region inference)
                    "arn:aws:bedrock:*::foundation-model/*",
                    # Allow access to inference profiles in this account
                    f"arn:aws:bedrock:*:{self.account}:inference-profile/*",
                ],
            )
        )

        # Bedrock Knowledge Base Access
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:knowledge-base/*",
                ],
            )
        )

        # Bedrock Guardrails Access
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:ApplyGuardrail",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:guardrail/*",
                ],
            )
        )

        # DynamoDB Access (Read-only for sales data)
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:GetItem",
                    "dynamodb:DescribeTable",
                    "dynamodb:ListTables",
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/*",
                ],
            )
        )

        # S3 Access (Read-only for documents)
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:ListAllMyBuckets",
                ],
                resources=[
                    "arn:aws:s3:::*",
                ],
            )
        )

        # Secrets Manager Access (for OAuth credentials)
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                ],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{project_name}/{environment}/*",
                ],
            )
        )

        # CloudWatch Logs Access
        # AgentCore creates log groups under /aws/bedrock-agentcore/runtimes/
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                ],
                resources=[
                    # AgentCore runtime logs - log group level
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock-agentcore/runtimes/*",
                    # AgentCore runtime logs - log stream level (required for PutLogEvents)
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*",
                    # Legacy path (if needed)
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock/agent/*",
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock/agent/*:log-stream:*",
                ],
            )
        )

        # AWS X-Ray Access for distributed tracing
        # OpenTelemetry exports traces to X-Ray for full observability
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                ],
                resources=["*"],  # X-Ray requires wildcard resource
            )
        )

        # ECR Access (for pulling agent container images)
        # GetAuthorizationToken requires "*" resource
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                ],
                resources=["*"],
            )
        )
        # Repository-specific ECR permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=[
                    f"arn:aws:ecr:{self.region}:{self.account}:repository/{ecr_repo_name}",
                ],
            )
        )

        # ===================================================================
        # Bedrock AgentCore Runtime - Containerized Agent
        # ===================================================================
        # Note: The container image must be pushed to ECR before deploying
        # Use the get_docker_commands() method to get build/push commands

        self.agent_runtime = agentcore.CfnRuntime(
            self,
            "BedrockAgentCoreRuntime",
            agent_runtime_name=agent_name,
            role_arn=self.agent_role.role_arn,
            description=f"SideKick AI hierarchical multi-agent system for {environment}",
            # Container configuration for AgentCore
            agent_runtime_artifact=agentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration=agentcore.CfnRuntime.ContainerConfigurationProperty(
                    # ECR image URI will be set after first push
                    # Format: {account}.dkr.ecr.{region}.amazonaws.com/{repo}:latest
                    container_uri=f"{self.ecr_repository.repository_uri}:latest",
                )
            ),
            # Network configuration
            network_configuration=agentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC",  # Public network mode for AgentCore
            ),
            # Environment variables for agent configuration
            environment_variables={
                "BYPASS_TOOL_CONSENT": "true",
                "BEDROCK_MODEL_ID": "eu.amazon.nova-pro-v1:0",
                "AWS_REGION": self.region,
                # Bedrock Knowledge Base Configuration
                "KNOWLEDGE_BASE_ID": config.get("knowledge_base_id", ""),
                # Bedrock Guardrails Configuration (optional)
                "BEDROCK_GUARDRAIL_ID": config.get("bedrock_guardrail_id", ""),
                "BEDROCK_GUARDRAIL_VERSION": config.get("bedrock_guardrail_version", "1"),
                # Strands logging configuration
                "STRANDS_LOG_LEVEL": "INFO",
                # OpenTelemetry configuration - disable metrics to prevent connection errors
                # Based on AWS OpenTelemetry Python Distro documentation
                "OTEL_METRICS_EXPORTER": "none",  # Disable metrics export
                "OTEL_TRACES_EXPORTER": "none",  # Disable traces export
                # Logs exporter is handled automatically by AgentCore
                # Force update marker - increment to trigger runtime update
                "DEPLOYMENT_VERSION": "20",
                # Atlassian OAuth Configuration (for real JIRA/Confluence access)
                # Note: These should be stored in AWS Secrets Manager for production
                # For now, they're passed as environment variables for the hackathon demo
                "ATLASSIAN_OAUTH_CLIENT_ID": config.get("atlassian_oauth_client_id", ""),
                "ATLASSIAN_OAUTH_CLIENT_SECRET": config.get("atlassian_oauth_client_secret", ""),
                "ATLASSIAN_OAUTH_REDIRECT_URI": config.get("atlassian_oauth_redirect_uri", ""),
                "ATLASSIAN_CLOUD_ID": config.get("atlassian_cloud_id", ""),
                "ATLASSIAN_SITE_URL": config.get("atlassian_site_url", ""),
                "ATLASSIAN_DEMO_USER_ID": config.get("atlassian_demo_user_id", "yetanotherarslan@gmail.com"),
            },
        )

        # Ensure IAM role and policies are created before the runtime
        self.agent_runtime.node.add_dependency(self.agent_role)

        # ===================================================================
        # Outputs
        # ===================================================================
        CfnOutput(
            self,
            "RuntimeId",
            value=self.agent_runtime.attr_agent_runtime_id,
            description="Bedrock AgentCore Runtime ID",
            export_name=f"{project_name}-runtime-id-{environment}",
        )

        CfnOutput(
            self,
            "RuntimeArn",
            value=self.agent_runtime.attr_agent_runtime_arn,
            description="Bedrock AgentCore Runtime ARN",
            export_name=f"{project_name}-runtime-arn-{environment}",
        )

        CfnOutput(
            self,
            "RuntimeName",
            value=self.agent_runtime.agent_runtime_name,
            description="Bedrock AgentCore Runtime Name",
            export_name=f"{project_name}-runtime-name-{environment}",
        )

        CfnOutput(
            self,
            "EcrRepositoryUri",
            value=self.ecr_repository.repository_uri,
            description="ECR Repository URI for agent container",
            export_name=f"{project_name}-agent-ecr-uri-{environment}",
        )

        CfnOutput(
            self,
            "AgentRoleArn",
            value=self.agent_role.role_arn,
            description="IAM Role ARN for Bedrock AgentCore",
            export_name=f"{project_name}-agent-role-arn-{environment}",
        )

        # Store for use in other stacks
        self.runtime_id = self.agent_runtime.attr_agent_runtime_id
        self.runtime_arn = self.agent_runtime.attr_agent_runtime_arn
        self.runtime_name = self.agent_runtime.agent_runtime_name

    def get_docker_commands(self) -> list:
        """Get Docker build and push commands for agent container."""
        repo_uri = self.ecr_repository.repository_uri
        repo_name = self.ecr_repository.repository_name

        return [
            "# Authenticate Docker with ECR",
            f"aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {self.account}.dkr.ecr.{self.region}.amazonaws.com",
            "",
            "# Build Docker image for agents",
            f"docker build -t {repo_name}:latest .",
            "",
            "# Tag image for ECR",
            f"docker tag {repo_name}:latest {repo_uri}:latest",
            "",
            "# Push image to ECR",
            f"docker push {repo_uri}:latest",
        ]
