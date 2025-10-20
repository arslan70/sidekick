"""
Agent Runtime Stack - Amazon Bedrock AgentCore infrastructure.

Creates:
- Bedrock AgentCore Runtime for agent workloads
- ECR repository for agent container images
- IAM roles with Bedrock and KB permissions
- Network configuration for AgentCore
- SSM parameters for AgentCore ARN storage
"""

from aws_cdk import CfnOutput, Stack, Tags
from aws_cdk import aws_bedrockagentcore as bedrockagentcore
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class AgentRuntimeStack(Stack):
    """Stack for Bedrock AgentCore runtime infrastructure."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        knowledge_base_id: str,
        knowledge_base_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = config["project_name"]
        environment = config["environment"]

        # Create service name for AgentCore
        service_name = f"{project_name}-{environment}"
        orchestrator_arn_parameter_name = (
            f"/{project_name}/{environment}/orchestrator-arn"
        )

        # ECR Repository for Agent Container (equivalent to auto_create_ecr=True)
        self.ecr_repository = ecr.Repository(
            self,
            "AgentEcrRepository",
            repository_name=f"{service_name}-orchestrator",
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(max_image_count=10, description="Keep last 10 images")
            ],
        )

        # IAM Role for Bedrock Agent Core Runtime (equivalent to execution_role)
        self.agent_role = iam.Role(
            self,
            "BedrockAgentRole",
            role_name=f"{service_name}-agent-iam-role",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonBedrockFullAccess"
                ),
            ],
            inline_policies={
                "BedrockAgentCorePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                # CloudWatch Logs
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                # ECR Access
                                "ecr:GetAuthorizationToken",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                # Parameter Store
                                "ssm:GetParameter",
                                "ssm:GetParameters",
                                # Secrets Manager
                                "secretsmanager:GetSecretValue",
                                # Bedrock Knowledge Base access
                                "bedrock-agent-runtime:Retrieve",
                                # Additional permissions for agent operations
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream",
                                "bedrock:ListModels",
                                "bedrock:GetModel",
                            ],
                            resources=["*"],
                        ),
                        # Specific access to knowledge base
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["bedrock-agent-runtime:Retrieve"],
                            resources=[knowledge_base_arn],
                        ),
                        # Scoped access to project resources
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["ssm:GetParameter", "ssm:GetParameters"],
                            resources=[
                                f"arn:aws:ssm:{self.region}:{self.account}:parameter/{project_name}/{environment}/*"
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["secretsmanager:GetSecretValue"],
                            resources=[
                                f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{project_name}/{environment}/*"
                            ],
                        ),
                    ]
                )
            },
        )

        # Bedrock Agent Core Runtime (equivalent to agentcore_runtime.configure() and launch())
        self.agent_runtime = bedrockagentcore.CfnRuntime(
            self,
            "OrchestratorRuntime",
            agent_runtime_name=service_name.replace(
                "-", "_"
            ),  # equivalent to agent_name
            description=f"SideKick Orchestrator Agent Runtime for {service_name}",
            role_arn=self.agent_role.role_arn,  # equivalent to execution_role
            network_configuration=bedrockagentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC"  # equivalent to region configuration
            ),
            agent_runtime_artifact=bedrockagentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration=bedrockagentcore.CfnRuntime.ContainerConfigurationProperty(
                    container_uri=f"{self.account}.dkr.ecr.{self.region}.amazonaws.com/{self.ecr_repository.repository_name}:latest"
                )
            ),
            protocol_configuration="HTTP",  # For agent-to-client communication
            environment_variables={
                "SERVICE": service_name,
                "AWS_REGION": self.region,
                "AWS_ACCOUNT_ID": self.account,
                "ENVIRONMENT": environment,
                "BEDROCK_KB_ID": knowledge_base_id,
                "BEDROCK_MODEL_ID": "us.eu.amazon.nova-pro-v1:0",
                # Add any environment variables equivalent to those in src/orchestrator/requirements.txt context
                "PYTHONPATH": "/app",
                "PYTHONUNBUFFERED": "1",
                "CHAINLIT_HOST": "0.0.0.0",
                "CHAINLIT_PORT": "8000",
            },
            tags={
                "team": "platform-engineering",
                "service": service_name,
                "project": project_name,
                "environment": environment,
                "managed-by": "cdk",
            },
        )

        # Store orchestrator ARN in Parameter Store (equivalent to saving to SSM)
        self.arn_parameter = ssm.StringParameter(
            self,
            "OrchestratorArnParameter",
            parameter_name=orchestrator_arn_parameter_name,
            string_value=self.agent_runtime.attr_agent_runtime_arn,  # equivalent to agent_arn from launch_result
            description=f"ARN for {service_name} orchestrator agent",
        )

        # Add tags to all resources
        Tags.of(self.ecr_repository).add("team", "platform-engineering")
        Tags.of(self.ecr_repository).add("service", service_name)
        Tags.of(self.ecr_repository).add("project", project_name)
        Tags.of(self.ecr_repository).add("environment", environment)

        Tags.of(self.agent_role).add("team", "platform-engineering")
        Tags.of(self.agent_role).add("service", service_name)
        Tags.of(self.agent_role).add("project", project_name)
        Tags.of(self.agent_role).add("environment", environment)

        Tags.of(self.arn_parameter).add("team", "platform-engineering")
        Tags.of(self.arn_parameter).add("service", service_name)
        Tags.of(self.arn_parameter).add("project", project_name)
        Tags.of(self.arn_parameter).add("environment", environment)

        # Outputs
        CfnOutput(
            self,
            "AgentRuntimeArn",
            value=self.agent_runtime.attr_agent_runtime_arn,
            description="Bedrock AgentCore Runtime ARN",
            export_name=f"{project_name}-agent-runtime-arn-{environment}",
        )

        CfnOutput(
            self,
            "AgentRuntimeId",
            value=self.agent_runtime.attr_agent_runtime_id,
            description="Bedrock AgentCore Runtime ID",
            export_name=f"{project_name}-agent-runtime-id-{environment}",
        )

        CfnOutput(
            self,
            "EcrRepositoryUri",
            value=self.ecr_repository.repository_uri,
            description="ECR Repository URI for agent container",
            export_name=f"{project_name}-ecr-repository-uri-{environment}",
        )

        CfnOutput(
            self,
            "AgentRoleArn",
            value=self.agent_role.role_arn,
            description="IAM Role ARN for AgentCore runtime",
            export_name=f"{project_name}-agent-role-arn-{environment}",
        )

        # Store for use in other stacks
        self.agent_runtime_arn = self.agent_runtime.attr_agent_runtime_arn
        self.agent_runtime_id = self.agent_runtime.attr_agent_runtime_id
        self.container_uri = f"{self.ecr_repository.repository_uri}:latest"

    def get_container_uri(self) -> str:
        """Get the container URI for Docker operations."""
        return f"{self.ecr_repository.repository_uri}:latest"

    def get_docker_commands(self) -> list:
        """Get Docker build and push commands (equivalent to the deploy_agents.py build process)."""
        repo_uri = self.ecr_repository.repository_uri

        return [
            f"aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {repo_uri}",
            f"docker build -t {self.agent_runtime.agent_runtime_name} -f Dockerfile .",
            f"docker tag {self.agent_runtime.agent_runtime_name}:latest {repo_uri}:latest",
            f"docker push {repo_uri}:latest",
        ]
