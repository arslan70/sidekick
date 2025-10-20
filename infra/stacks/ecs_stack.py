"""
ECS Stack - Chainlit UI deployment on AWS Fargate.

Creates:
- ECR repository for Chainlit container images
- VPC with public and private subnets
- Application Load Balancer with HTTPS
- ECS Fargate cluster and service
- IAM roles for ECS tasks
- CloudWatch log groups
- Auto-scaling configuration
"""

import logging

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct

logger = logging.getLogger(__name__)


class EcsStack(Stack):
    """Stack for ECS Fargate deployment of Chainlit UI."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        agent_runtime_id: str = None,
        agent_runtime_arn: str = None,
        create_service: bool = False,  # Flag to control service creation
        certificate_arn: str = None,  # Optional ACM certificate ARN for HTTPS
        domain_name: str = None,  # Optional custom domain name
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = config["project_name"]
        environment = config["environment"]
        service_name = f"{project_name}-ui-{environment}"

        # ECR Repository for Chainlit UI Container
        # Reference existing repository (created outside CDK or in previous deployment)
        self.ecr_repository = ecr.Repository.from_repository_name(
            self, "ChainlitEcrRepository", repository_name=f"{service_name}"
        )

        # VPC with public and private subnets
        self.vpc = ec2.Vpc(
            self,
            "ChainlitVpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # ECS Cluster
        self.cluster = ecs.Cluster(
            self,
            "ChainlitCluster",
            cluster_name=service_name,
            vpc=self.vpc,
            container_insights=True,
        )

        # CloudWatch Log Group
        self.log_group = logs.LogGroup(
            self,
            "ChainlitLogGroup",
            log_group_name=f"/ecs/{service_name}",
            retention=logs.RetentionDays.ONE_WEEK,
        )

        # Task Execution Role (for pulling images, writing logs)
        self.task_execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            role_name=f"{service_name}-task-execution-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                ),
            ],
            inline_policies={
                "SecretsManagerAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:GetSecretValue",
                            ],
                            resources=[
                                f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{project_name}/{environment}/*"
                            ],
                        ),
                    ]
                )
            },
        )

        # Task Role (for application permissions)
        self.task_role = iam.Role(
            self,
            "TaskRole",
            role_name=f"{service_name}-task-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={
                "BedrockAgentCoreAccess": iam.PolicyDocument(
                    statements=[
                        # Bedrock AgentCore Runtime invocation
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock-agentcore:InvokeAgentRuntime",
                                "bedrock-agentcore:InvokeAgentRuntimeWithResponseStream",
                                "bedrock-agentcore:GetAgentRuntime",
                            ],
                            resources=["*"],
                        ),
                        # DynamoDB access
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:Query",
                                "dynamodb:Scan",
                                "dynamodb:GetItem",
                                "dynamodb:DescribeTable",
                            ],
                            resources=[
                                f"arn:aws:dynamodb:{self.region}:{self.account}:table/*"
                            ],
                        ),
                        # S3 read access
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:ListBucket",
                            ],
                            resources=["*"],
                        ),
                        # Secrets Manager access
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:GetSecretValue",
                            ],
                            resources=[
                                f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{project_name}/{environment}/*"
                            ],
                        ),
                        # CloudWatch Logs
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[self.log_group.log_group_arn],
                        ),
                    ]
                )
            },
        )

        # Fargate Task Definition
        self.task_definition = ecs.FargateTaskDefinition(
            self,
            "ChainlitTaskDefinition",
            family=service_name,
            cpu=1024,  # 1 vCPU
            memory_limit_mib=2048,  # 2 GB
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
            execution_role=self.task_execution_role,
            task_role=self.task_role,
        )

        # Container Definition
        container_image = ecs.ContainerImage.from_ecr_repository(
            repository=self.ecr_repository, tag="latest"
        )

        # Build environment variables for container
        container_env = {
            "AWS_REGION": self.region,
            "ENVIRONMENT": environment,
            "SERVICE_NAME": service_name,
            # Chainlit authentication secret name for Secrets Manager
            "CHAINLIT_AUTH_SECRET_NAME": f"{project_name}/{environment}/chainlit-auth",
        }

        # Add AgentCore configuration if provided
        if agent_runtime_arn:
            container_env["AGENTCORE_RUNTIME_ARN"] = agent_runtime_arn
            container_env["USE_AGENTCORE"] = "true"
            logger.info(f"AgentCore integration enabled with ARN: {agent_runtime_arn}")
        else:
            container_env["USE_AGENTCORE"] = "false"
            logger.info(
                "AgentCore integration disabled - using direct orchestrator mode"
            )

        # Add Chainlit authentication secret (required for OAuth)
        # This should be a secure random string for JWT token signing
        if config.get("chainlit_auth_secret"):
            container_env["CHAINLIT_AUTH_SECRET"] = config.get("chainlit_auth_secret")
            logger.info("Chainlit auth secret configured")
        
        # Add Atlassian OAuth configuration
        # These are read from config and should match the values in .env
        if config.get("atlassian_oauth_client_id"):
            container_env["ATLASSIAN_OAUTH_CLIENT_ID"] = config.get("atlassian_oauth_client_id", "")
            container_env["ATLASSIAN_OAUTH_CLIENT_SECRET"] = config.get("atlassian_oauth_client_secret", "")
            
            # Build OAuth redirect URI based on domain/certificate configuration
            # If custom domain is provided, use it; otherwise use ALB DNS name
            # Note: ALB DNS name is not available at synthesis time, so we'll use a placeholder
            # The actual redirect URI should be updated after deployment
            if domain_name:
                oauth_redirect_uri = f"https://{domain_name}/oauth/callback"
            elif certificate_arn:
                # HTTPS is configured but no custom domain - use placeholder
                # User must update this after deployment with actual ALB DNS name
                oauth_redirect_uri = config.get("atlassian_oauth_redirect_uri", "https://REPLACE_WITH_ALB_DNS/oauth/callback")
            else:
                # HTTP only (development)
                oauth_redirect_uri = config.get("atlassian_oauth_redirect_uri", "http://localhost:8000/oauth/callback")
            
            container_env["ATLASSIAN_OAUTH_REDIRECT_URI"] = oauth_redirect_uri
            container_env["ATLASSIAN_CLOUD_ID"] = config.get("atlassian_cloud_id", "")
            container_env["ATLASSIAN_SITE_URL"] = config.get("atlassian_site_url", "")
            logger.info(f"Atlassian OAuth configuration added with redirect URI: {oauth_redirect_uri}")

        # Add authentication configuration (optional)
        # Note: CHAINLIT_AUTH_SECRET should be stored in Secrets Manager for production
        # For now, we'll document that it should be added manually or via environment
        # ADMIN_PASSWORD should also be stored in Secrets Manager
        # Demo credentials are hardcoded in app/auth.py for hackathon judges

        self.container = self.task_definition.add_container(
            "ChainlitContainer",
            image=container_image,
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="chainlit",
                log_group=self.log_group,
            ),
            environment=container_env,
            port_mappings=[
                ecs.PortMapping(
                    container_port=8080,
                    protocol=ecs.Protocol.TCP,
                )
            ],
            health_check=ecs.HealthCheck(
                command=[
                    "CMD-SHELL",
                    "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()\" || exit 1",
                ],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(10),
                retries=3,
                start_period=Duration.seconds(40),
            ),
        )

        # Security Group for ALB
        self.alb_security_group = ec2.SecurityGroup(
            self,
            "AlbSecurityGroup",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True,
        )
        self.alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP traffic",
        )
        self.alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS traffic",
        )

        # Security Group for ECS Tasks
        self.ecs_security_group = ec2.SecurityGroup(
            self,
            "EcsSecurityGroup",
            vpc=self.vpc,
            description="Security group for ECS tasks",
            allow_all_outbound=True,
        )
        self.ecs_security_group.add_ingress_rule(
            peer=self.alb_security_group,
            connection=ec2.Port.tcp(8080),
            description="Allow traffic from ALB",
        )

        # Application Load Balancer
        self.alb = elbv2.ApplicationLoadBalancer(
            self,
            "ChainlitAlb",
            vpc=self.vpc,
            internet_facing=True,
            security_group=self.alb_security_group,
            load_balancer_name=service_name,
        )

        # Target Group
        self.target_group = elbv2.ApplicationTargetGroup(
            self,
            "ChainlitTargetGroup",
            vpc=self.vpc,
            port=8080,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path="/health",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(10),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
            ),
            deregistration_delay=Duration.seconds(30),
        )

        # HTTPS Configuration
        # If certificate ARN is provided, configure HTTPS listener
        # Otherwise, use HTTP only (for development/testing)
        if certificate_arn:
            logger.info(f"Configuring HTTPS with certificate: {certificate_arn}")
            
            # Import existing ACM certificate
            certificate = acm.Certificate.from_certificate_arn(
                self,
                "AlbCertificate",
                certificate_arn=certificate_arn,
            )
            
            # HTTPS Listener (port 443) with certificate
            self.https_listener = self.alb.add_listener(
                "HttpsListener",
                port=443,
                protocol=elbv2.ApplicationProtocol.HTTPS,
                certificates=[certificate],
                default_action=elbv2.ListenerAction.forward(
                    target_groups=[self.target_group]
                ),
            )
            
            # Add security headers to HTTPS responses
            # Note: CDK L2 constructs don't directly support response headers policy
            # This would need to be added via L1 construct or manually in console
            # For now, we'll document this requirement
            logger.info("HTTPS listener configured. Add security headers via console or L1 construct if needed.")
            
            # HTTP Listener (port 80) - redirect to HTTPS
            self.http_listener = self.alb.add_listener(
                "HttpListener",
                port=80,
                protocol=elbv2.ApplicationProtocol.HTTP,
                default_action=elbv2.ListenerAction.redirect(
                    protocol="HTTPS",
                    port="443",
                    permanent=True,  # 301 redirect
                ),
            )
            logger.info("HTTP to HTTPS redirect configured (301 permanent)")
            
        else:
            logger.warning("No certificate ARN provided - using HTTP only (not recommended for production)")
            
            # HTTP Listener (port 80) - forward to target group
            self.http_listener = self.alb.add_listener(
                "HttpListener",
                port=80,
                protocol=elbv2.ApplicationProtocol.HTTP,
                default_action=elbv2.ListenerAction.forward(
                    target_groups=[self.target_group]
                ),
            )
            self.https_listener = None

        # ECS Fargate Service (optional - only create if flag is set)
        if create_service:
            self.service = ecs.FargateService(
                self,
                "ChainlitService",
                cluster=self.cluster,
                task_definition=self.task_definition,
                desired_count=1,  # Single task for POC
                service_name=service_name,
                security_groups=[self.ecs_security_group],
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
                health_check_grace_period=Duration.seconds(60),
                circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            )

            # Attach service to target group
            self.service.attach_to_application_target_group(self.target_group)

            # Auto Scaling (minimal for POC)
            scaling = self.service.auto_scale_task_count(
                min_capacity=1,  # Single task minimum for POC
                max_capacity=2,  # Allow scaling to 2 if needed
            )

            # CPU-based scaling
            scaling.scale_on_cpu_utilization(
                "CpuScaling",
                target_utilization_percent=70,
                scale_in_cooldown=Duration.seconds(60),
                scale_out_cooldown=Duration.seconds(60),
            )

            # Memory-based scaling
            scaling.scale_on_memory_utilization(
                "MemoryScaling",
                target_utilization_percent=80,
                scale_in_cooldown=Duration.seconds(60),
                scale_out_cooldown=Duration.seconds(60),
            )
        else:
            self.service = None

        # Outputs
        CfnOutput(
            self,
            "EcrRepositoryUri",
            value=self.ecr_repository.repository_uri,
            description="ECR Repository URI for Chainlit container",
            export_name=f"{project_name}-chainlit-ecr-uri-{environment}",
        )

        CfnOutput(
            self,
            "LoadBalancerDns",
            value=self.alb.load_balancer_dns_name,
            description="Application Load Balancer DNS name",
            export_name=f"{project_name}-alb-dns-{environment}",
        )
        
        # Output application URL based on HTTPS configuration
        if certificate_arn and domain_name:
            app_url = f"https://{domain_name}"
        elif certificate_arn:
            app_url = f"https://{self.alb.load_balancer_dns_name}"
        else:
            app_url = f"http://{self.alb.load_balancer_dns_name}"
        
        CfnOutput(
            self,
            "ApplicationUrl",
            value=app_url,
            description="Application URL (use this to access the application)",
        )
        
        if certificate_arn:
            CfnOutput(
                self,
                "HttpsEnabled",
                value="true",
                description="HTTPS is enabled with SSL certificate",
            )
            CfnOutput(
                self,
                "CertificateArn",
                value=certificate_arn,
                description="ACM Certificate ARN used for HTTPS",
            )

        if create_service and self.service:
            CfnOutput(
                self,
                "ServiceName",
                value=self.service.service_name,
                description="ECS Service name",
                export_name=f"{project_name}-ecs-service-name-{environment}",
            )

        CfnOutput(
            self,
            "ClusterName",
            value=self.cluster.cluster_name,
            description="ECS Cluster name",
            export_name=f"{project_name}-ecs-cluster-name-{environment}",
        )

        # Output AgentCore configuration for verification
        if agent_runtime_arn:
            CfnOutput(
                self,
                "AgentCoreRuntimeArn",
                value=agent_runtime_arn,
                description="AgentCore Runtime ARN configured for this ECS service",
            )

    def get_docker_commands(self) -> list:
        """Get Docker build and push commands for Chainlit UI."""
        repo_uri = self.ecr_repository.repository_uri
        service_name = self.ecr_repository.repository_name

        return [
            "# Authenticate Docker with ECR",
            f"aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {self.account}.dkr.ecr.{self.region}.amazonaws.com",
            "",
            "# Build Docker image",
            f"docker build -t {service_name}:latest .",
            "",
            "# Tag image for ECR",
            f"docker tag {service_name}:latest {repo_uri}:latest",
            "",
            "# Push image to ECR",
            f"docker push {repo_uri}:latest",
        ]
