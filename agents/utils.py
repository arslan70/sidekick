"""
Utility functions for agent operations.

This module provides common utilities used across multiple agent implementations
to reduce code duplication and improve maintainability.
"""


def extract_agent_response(response) -> str:
    """
    Extract text content from an agent response.

    This utility handles both real Agent responses (which have a messages attribute)
    and MockAgent responses (which return strings directly). This pattern is used
    throughout the codebase to handle responses consistently.

    Args:
        response: The response object from an agent call. Can be either:
            - An Agent response object with a messages attribute
            - A MockAgent response (string)
            - Any other object that can be converted to string

    Returns:
        str: The extracted text content from the response

    Example:
        >>> agent_response = agent("What is the weather?")
        >>> text = extract_agent_response(agent_response)
        >>> print(text)
    """
    if hasattr(response, "messages"):
        return response.messages[0].content
    return str(response)
