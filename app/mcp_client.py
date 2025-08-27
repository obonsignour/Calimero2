import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from .config import load_mcp_config, resolve_imaging_endpoint

logger = logging.getLogger("cast-imaging-agent.mcp")

@asynccontextmanager
async def imaging_session():
    """
    Async context manager yielding an MCP ClientSession connected to Imaging
    over Streamable HTTP transport (available since MCP 2024-11-05).
    Lazy-imports the SDK so tests can stub this function without installing MCP.
    """
    # Check if we're in test mode (mocked by pytest)
    if hasattr(imaging_session, '_test_implementation'):
        async with imaging_session._test_implementation() as session:
            yield session
        return
    
    # Lazy imports to avoid hard dependency at module import time (helps tests)
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    cfg = load_mcp_config()
    base_url, headers = resolve_imaging_endpoint(cfg)

    # Connect with streamable HTTP client 
    async with streamablehttp_client(base_url, headers=headers) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize the protocol session explicitly
            await session.initialize()
            yield session

async def list_tools(session) -> List[str]:
    tools = await session.list_tools()
    # Normalize to names (SDK returns an object with .tools list)
    return [t.name for t in tools.tools]

async def call_tool(session, tool_name: str, args: Dict[str, Any]):
    result = await session.call_tool(tool_name, args)
    
    # Extract the actual content from CallToolResult
    if hasattr(result, 'content') and result.content:
        # MCP CallToolResult has a content attribute which is a list
        content_list = result.content
        if isinstance(content_list, list) and len(content_list) > 0:
            first_content = content_list[0]
            
            # Handle different content types
            if hasattr(first_content, 'text'):
                # Text content - try to parse as JSON
                import json
                try:
                    return json.loads(first_content.text)
                except (json.JSONDecodeError, AttributeError):
                    return first_content.text
            elif hasattr(first_content, 'data'):
                # Data content
                return first_content.data
            else:
                # Unknown content type, return as-is
                return first_content
        else:
            # Empty or non-list content
            return content_list
    else:
        # No content attribute or empty content, return the result as-is
        return result
