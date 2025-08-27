import difflib
import logging
from typing import Any, Dict, List, Optional, Tuple

from .mcp_client import call_tool

logger = logging.getLogger("cast-imaging-agent.tools")

def parse_applications_string(apps_str: str) -> List[Dict[str, Any]]:
    """
    Parse the string format returned by the MCP server for applications.
    
    Expected format:
    Available applications:
    Showing items 1-8 of 8 total

    delivery: [dateTime: 2025-06-19T14:51:00, name: Onboarding-202506191451](
    name: Shopizer_115
    ---
    delivery: [dateTime: 2025-05-08T20:12:00, name: Onboarding-202505082012](
    name: CAAS_ADE
    ---
    ...
    """
    applications = []
    
    # Split by the separator "---" to get individual application blocks
    blocks = apps_str.split('---')
    
    for block in blocks:
        block = block.strip()
        if not block or 'Available applications:' in block or 'Showing items' in block:
            continue
            
        # Extract application name from the block
        lines = block.split('\n')
        app_name = None
        delivery_info = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('name:'):
                app_name = line.replace('name:', '').strip()
            elif line.startswith('delivery:'):
                delivery_info = line.replace('delivery:', '').strip()
        
        if app_name:
            app_dict = {
                "id": app_name,  # Use name as ID since no separate ID is provided
                "name": app_name
            }
            if delivery_info:
                app_dict["delivery"] = delivery_info
            applications.append(app_dict)
    
    return applications

def match_tool_name(available_names: List[str], desired_base: str) -> Optional[str]:
    """Find a tool by exact name, suffix, or fuzzy match."""
    if desired_base in available_names:
        return desired_base
    candidates = [n for n in available_names if n.endswith(desired_base)]
    if candidates:
        candidates.sort(key=len)
        return candidates[0]
    close = difflib.get_close_matches(desired_base, available_names, n=1)
    return close[0] if close else None

async def select_application(session, tool_names: List[str], question: str, app_hint: Optional[str]) -> Tuple[Dict[str, Any], str]:
    """ALWAYS call `applications` to enumerate and select the app."""
    applications_tool = match_tool_name(tool_names, "applications")
    if not applications_tool:
        raise RuntimeError("Imaging MCP: 'applications' tool not found.")

    # Debug: Log the input parameters
    logger.info(f"select_application called with question='{question}', app_hint='{app_hint}'")
    logger.info(f"Using applications tool: {applications_tool}")

    apps = await call_tool(session, applications_tool, {})
    
    # Debug: Log the raw response from MCP server
    logger.info(f"Raw MCP response - type: {type(apps)}, value: {apps}")
    
    # Extract the application list from the processed data
    if isinstance(apps, dict):
        app_list = apps.get("items", apps.get("applications", apps.get("data", [])))
    elif isinstance(apps, list):
        app_list = apps
    elif isinstance(apps, str):
        # Parse the string format returned by the MCP server
        app_list = parse_applications_string(apps)
        logger.info(f"Parsed {len(app_list)} applications from string response")
    else:
        # Try to convert to list if it's iterable
        try:
            app_list = list(apps) if apps else []
        except (TypeError, ValueError):
            app_list = [apps] if apps else []
    
    if not app_list:
        raise RuntimeError("No applications returned by Imaging MCP.")

    # Debug: Log the structure of app_list to understand what we're getting
    logger.debug(f"app_list type: {type(app_list)}, length: {len(app_list) if hasattr(app_list, '__len__') else 'unknown'}")
    if app_list and hasattr(app_list, '__getitem__'):
        try:
            logger.debug(f"First item type: {type(app_list[0])}, value: {app_list[0]}")
        except (IndexError, TypeError):
            logger.debug("Could not access first item in app_list")

    # Handle different data structures that might be returned
    processed_apps = []
    names = []
    
    for i, item in enumerate(app_list):
        if isinstance(item, dict):
            # Standard dictionary case
            processed_apps.append(item)
            name = str(item.get("name") or item.get("application") or item.get("id") or f"app_{i}")
            names.append(name)
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            # Handle tuple/list case - assume (id, name) or similar structure
            app_dict = {
                "id": str(item[0]) if len(item) > 0 else f"app_{i}",
                "name": str(item[1]) if len(item) > 1 else f"app_{i}",
            }
            # Add additional fields if available
            if len(item) > 2:
                app_dict["application"] = str(item[2])
            processed_apps.append(app_dict)
            names.append(app_dict["name"])
        elif isinstance(item, str):
            # Handle string case - use as both id and name
            app_dict = {"id": item, "name": item}
            processed_apps.append(app_dict)
            names.append(item)
        else:
            # Fallback for unknown types
            logger.warning(f"Unknown application item type: {type(item)}, value: {item}")
            app_dict = {"id": f"app_{i}", "name": str(item)}
            processed_apps.append(app_dict)
            names.append(str(item))

    if not processed_apps:
        raise RuntimeError("No valid applications could be processed from Imaging MCP response.")

    # Debug: Log processed applications
    logger.info(f"Processed {len(processed_apps)} applications:")
    for i, app in enumerate(processed_apps[:5]):  # Log first 5 apps
        logger.info(f"  App {i}: {app}")
    logger.info(f"Available names: {names[:10]}")  # Log first 10 names

    # Select the best matching application
    guess = (app_hint or "").strip() or (max(question.split(), key=len) if question.split() else "")
    logger.info(f"Matching guess: '{guess}' against available names")
    
    best = difflib.get_close_matches(guess, names, n=1, cutoff=0.4)
    selected_name = best[0] if best else names[0]
    
    logger.info(f"Best match result: {best}, selected_name: '{selected_name}'")
    
    # Find the selected application
    selected = None
    for app in processed_apps:
        if app.get("name") == selected_name or app.get("id") == selected_name:
            selected = app
            break
    
    if not selected:
        selected = processed_apps[0]  # Fallback to first app
        logger.warning(f"No exact match found for '{selected_name}', using fallback: {selected}")
    
    logger.info(f"Final selected application: {selected}")
    
    return selected, applications_tool

def find_tool(available: List[str], base: str) -> Optional[str]:
    t = match_tool_name(available, base)
    if not t:
        logger.info("Tool '%s' not found; continuing without it.", base)
    return t

def normalize_app_id(app: Dict[str, Any]) -> Any:
    return app.get("id") or app.get("applicationId") or app.get("name")
