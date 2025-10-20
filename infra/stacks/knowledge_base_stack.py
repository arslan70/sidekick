"""
Knowledge Base Stack - S3 buckets for Bedrock Knowledge Base.

Creates:
- S3 bucket for data source
- S3 bucket for vector storage (if needed)

Note: The Bedrock Knowledge Base itself should be created manually via AWS Console
to use the S3 vector store feature (currently in preview, not yet in CDK).
"""

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class KnowledgeBaseStack(Stack):
    """Stack for S3 buckets needed by Bedrock Knowledge Base."""

    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = config["project_name"]
        environment = config["environment"]

        # Create S3 bucket for knowledge base data source
        self.data_bucket = s3.Bucket(
            self,
            "KBDataBucket",
            bucket_name=f"{project_name}-kb-data-{environment}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,  # Retain data in production
            auto_delete_objects=False,
        )

        # Create S3 bucket for vector store (if using S3 vectors)
        # Note: This may not be needed if Bedrock manages the vector store
        self.vector_bucket = s3.Bucket(
            self,
            "KBVectorBucket",
            bucket_name=f"{project_name}-kb-vectors-{environment}-{self.account}",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
        )

        # DEMO: Add intentionally faulty bucket policy for incident simulation
        # This policy is missing s3:PutObject permission, causing upload failures
        # This simulates a common misconfiguration scenario for demo purposes
        faulty_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid="BedrockKnowledgeBaseAccess",
                    effect=iam.Effect.ALLOW,
                    principals=[
                        iam.ServicePrincipal("bedrock.amazonaws.com"),
                    ],
                    actions=[
                        "s3:GetObject",
                        "s3:ListBucket",
                        # NOTE: s3:PutObject is intentionally missing!
                        # This causes 403 Forbidden errors when Bedrock tries to upload vectors
                    ],
                    resources=[
                        self.vector_bucket.bucket_arn,
                        f"{self.vector_bucket.bucket_arn}/*",
                    ],
                    conditions={
                        "StringEquals": {
                            "aws:SourceAccount": self.account,
                        },
                        "ArnLike": {
                            "aws:SourceArn": f"arn:aws:bedrock:{self.region}:{self.account}:knowledge-base/*",
                        },
                    },
                )
            ]
        )

        # Apply the faulty policy to the vector bucket
        s3.CfnBucketPolicy(
            self,
            "VectorBucketFaultyPolicy",
            bucket=self.vector_bucket.bucket_name,
            policy_document=faulty_policy,
        )

        # Outputs
        CfnOutput(
            self,
            "DataBucketName",
            value=self.data_bucket.bucket_name,
            description="S3 bucket for Knowledge Base data source - use this when creating KB in console",
            export_name=f"{project_name}-kb-data-bucket-{environment}",
        )

        CfnOutput(
            self,
            "DataBucketArn",
            value=self.data_bucket.bucket_arn,
            description="S3 bucket ARN for Knowledge Base data source",
            export_name=f"{project_name}-kb-data-bucket-arn-{environment}",
        )

        CfnOutput(
            self,
            "VectorBucketName",
            value=self.vector_bucket.bucket_name,
            description="S3 bucket for Knowledge Base vector storage (if needed)",
            export_name=f"{project_name}-kb-vector-bucket-{environment}",
        )

        CfnOutput(
            self,
            "VectorBucketArn",
            value=self.vector_bucket.bucket_arn,
            description="S3 bucket ARN for Knowledge Base vector storage",
            export_name=f"{project_name}-kb-vector-bucket-arn-{environment}",
        )
