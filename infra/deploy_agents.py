import logging
import os
import sys
import time

import boto3
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("deploy_agents.log"),
    ],
)

logger = logging.getLogger(__name__)

boto_session = Session()
region = "eu-central-1"
agentcore_runtime = Runtime()
aws_account_id = os.environ.get("AWS_ACCOUNT_ID")
service_name = os.environ.get("SERVICE", "platform-support-bot")

logger.info(f"Starting agent deployment for service: {service_name}")
iam_role_arn = f"arn:aws:iam::{aws_account_id}:role/{service_name}-agent-iam-role"

logger.info(
    f"Configuring AgentCore runtime for {service_name} with IAM role: {iam_role_arn}"
)

response = agentcore_runtime.configure(
    entrypoint="src/orchestrator/agent.py",
    execution_role=f"arn:aws:iam::{aws_account_id}:role/{service_name}-agent-iam-role",
    auto_create_ecr=True,
    requirements_file="src/orchestrator/requirements.txt",
    region=region,
    agent_name=service_name.replace("-", "_"),
)

try:
    logger.info(f"Launching AgentCore runtime for {service_name}")

    launch_result = agentcore_runtime.launch(
        auto_update_on_conflict=True, local_build=True
    )
    status_response = agentcore_runtime.status()
    status = status_response.endpoint["status"]
    end_status = ["READY", "CREATE_FAILED", "DELETE_FAILED", "UPDATE_FAILED"]

    logger.info(f"Monitoring agent deployment status. Initial status: {status}")

    iteration_count = 0
    while status not in end_status:
        time.sleep(10)
        iteration_count += 1
        status_response = agentcore_runtime.status()
        status = status_response.endpoint["status"]

        logger.info(
            f"Agent deployment status update - Status: {status}, Iteration: {iteration_count}"
        )

    logger.info(f"Agent deployment completed for {service_name} with status: {status}")

except Exception as e:
    logger.error(
        f"Failed to launch AgentCore runtime for {service_name}: {str(e)}",
        exc_info=True,
    )
    exit(1)

# Save agent ARN to Systems Manager Parameter Store if deployment was successful
if status == "READY":
    try:
        logger.info(
            f"Agent deployment successful for {service_name}, saving ARN to Parameter Store"
        )

        # Get the agent ARN from the status response
        agent_arn = launch_result.agent_arn

        if agent_arn:
            # Create SSM client
            ssm_client = boto3.client("ssm", region_name=region)

            # Define parameter name
            parameter_name = f"/{service_name}/orchestrator/arn"

            logger.info(f"Storing agent ARN in Parameter Store: {parameter_name}")

            # Put parameter in Parameter Store
            ssm_client.put_parameter(
                Name=parameter_name,
                Value=agent_arn,
                Type="String",
                Overwrite=True,
                Description=f"ARN for {service_name} orchestrator agent",
            )

            logger.info(
                f"Successfully saved agent ARN to Parameter Store: {parameter_name}"
            )
            logger.info(f"Agent ARN: {agent_arn}")
        else:
            logger.warning(
                f"Could not retrieve agent ARN from status response for {service_name}"
            )

    except Exception as e:
        logger.error(
            f"Failed to save agent ARN to Parameter Store for {service_name}: {str(e)}",
            exc_info=True,
        )
else:
    logger.error(
        f"Agent deployment failed for {service_name} with status: {status}. ARN not saved to Parameter Store."
    )
