"""
Amazon Bedrock Knowledge Base retrieval client.

Wraps the Bedrock Knowledge Bases Retrieve API for RAG functionality.
"""

import logging
import os
from typing import List, Optional

import boto3
from botocore.config import Config as BotocoreConfig

from tools.schemas import KnowledgeChunk

logger = logging.getLogger(__name__)


class BedrockKBClient:
    """Client for Amazon Bedrock Knowledge Bases retrieval."""

    def __init__(
        self,
        knowledge_base_id: Optional[str] = None,
        region_name: Optional[str] = None,
        profile_name: Optional[str] = None,
    ):
        """
        Initialize the Bedrock KB client.

        Args:
            knowledge_base_id: KB ID (defaults to KNOWLEDGE_BASE_ID or BEDROCK_KB_ID env var)
            region_name: AWS region (defaults to AWS_REGION env var or eu-central-1)
            profile_name: AWS profile name (optional)
        """
        # Support both KNOWLEDGE_BASE_ID and BEDROCK_KB_ID for backward compatibility
        self.knowledge_base_id = (
            knowledge_base_id
            or os.getenv("KNOWLEDGE_BASE_ID")
            or os.getenv("BEDROCK_KB_ID")
        )

        if not self.knowledge_base_id:
            raise ValueError(
                "Knowledge Base ID is required. Set KNOWLEDGE_BASE_ID environment variable "
                "or pass knowledge_base_id parameter."
            )

        self.region_name = region_name or os.getenv("AWS_REGION", "eu-central-1")
        self.min_score = float(os.getenv("MIN_SCORE", "0.4"))

        # Initialize Bedrock client
        config = BotocoreConfig(
            region_name=self.region_name, user_agent_extra="daily-planner-kb-client"
        )

        session_kwargs = {"region_name": self.region_name, "config": config}
        if profile_name:
            session_kwargs["profile_name"] = profile_name

        session = boto3.Session(**session_kwargs)
        self.bedrock_agent_runtime = session.client("bedrock-agent-runtime")

        logger.info(
            f"Knowledge Base client initialized with Bedrock KB: {self.knowledge_base_id} "
            f"(region: {self.region_name})"
        )

    def retrieve(
        self,
        query: str,
        max_results: int = 5,
        min_score: Optional[float] = None,
        retrieve_filter: Optional[dict] = None,
    ) -> List[KnowledgeChunk]:
        """
        Retrieve relevant knowledge chunks from Bedrock KB.

        Args:
            query: Query text for semantic search
            max_results: Maximum number of results to return
            min_score: Minimum relevance score threshold (defaults to self.min_score)
            retrieve_filter: Optional filter for retrieval results

        Returns:
            List of KnowledgeChunk objects sorted by relevance score.
        """
        if min_score is None:
            min_score = self.min_score

        try:
            # Build retrieval configuration
            retrieval_config = {
                "vectorSearchConfiguration": {"numberOfResults": max_results}
            }

            if retrieve_filter:
                retrieval_config["vectorSearchConfiguration"][
                    "filter"
                ] = retrieve_filter

            # Perform retrieval
            response = self.bedrock_agent_runtime.retrieve(
                retrievalQuery={"text": query},
                knowledgeBaseId=self.knowledge_base_id,
                retrievalConfiguration=retrieval_config,
            )

            # Parse and filter results
            all_results = response.get("retrievalResults", [])
            chunks = []

            for result in all_results:
                score = result.get("score", 0.0)
                if score < min_score:
                    continue

                # Extract content
                content = result.get("content", {})
                text = content.get("text", "")

                # Extract location
                location = result.get("location", {})
                source_id = "Unknown"
                source_uri = None

                if "customDocumentLocation" in location:
                    source_id = location["customDocumentLocation"].get("id", "Unknown")
                elif "s3Location" in location:
                    source_uri = location["s3Location"].get("uri", "")
                    source_id = source_uri.split("/")[-1] if source_uri else "Unknown"

                # Extract metadata
                metadata = result.get("metadata", {})
                if source_uri is None:
                    source_uri = metadata.get("x-amz-bedrock-kb-source-uri")

                chunk = KnowledgeChunk(
                    text=text,
                    source_id=source_id,
                    source_uri=source_uri,
                    score=score,
                    metadata=metadata,
                )
                chunks.append(chunk)

            # Sort by score (highest first)
            chunks.sort(key=lambda x: x.score, reverse=True)

            return chunks

        except Exception as e:
            raise RuntimeError(
                f"Failed to retrieve from Knowledge Base: {str(e)}"
            ) from e

    def format_chunks_for_display(self, chunks: List[KnowledgeChunk]) -> str:
        """
        Format knowledge chunks for readable display.

        Args:
            chunks: List of KnowledgeChunk objects.

        Returns:
            Formatted string representation with citations.
        """
        if not chunks:
            return "No relevant information found."

        formatted = [f"**Retrieved {len(chunks)} relevant document(s):**\n"]

        for i, chunk in enumerate(chunks, 1):
            formatted.append(f"**[{i}] Score: {chunk.score:.3f}**")
            if chunk.source_uri:
                formatted.append(f"Source: {chunk.source_uri}")
            else:
                formatted.append(f"Source ID: {chunk.source_id}")
            formatted.append(f"\n{chunk.text}\n")
            formatted.append("---\n")

        return "\n".join(formatted)


def retrieve_knowledge(
    query: str, max_results: int = 5, min_score: Optional[float] = None
) -> dict:
    """
    Tool function to retrieve knowledge from Bedrock KB.
    Compatible with StrandsAgents tool interface.

    Args:
        query: Query text for semantic search
        max_results: Maximum number of results to return
        min_score: Minimum relevance score threshold

    Returns:
        Dictionary with status, content, and chunks.
    """
    try:
        client = BedrockKBClient()
        chunks = client.retrieve(
            query=query, max_results=max_results, min_score=min_score
        )
        formatted = client.format_chunks_for_display(chunks)

        return {
            "status": "success",
            "content": formatted,
            "chunks": [chunk.model_dump(mode="json") for chunk in chunks],
        }
    except Exception as e:
        return {"status": "error", "content": f"Failed to retrieve knowledge: {str(e)}"}
