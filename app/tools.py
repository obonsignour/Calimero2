import difflib
import logging
from typing import Any, Dict, List, Optional, Tuple

from .mcp_client import call_tool

logger = logging.getLogger("cast-imaging-agent.tools")

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

    apps = await call_tool(session, applications_tool, {})
    app_list = apps.get("items", apps) if isinstance(apps, dict) else (apps or [])
    if not app_list:
        raise RuntimeError("No applications returned by Imaging MCP.")

    names = [str(a.get("name") or a.get("application") or a.get("id")) for a in app_list]
    guess = (app_hint or "").strip() or (max(question.split(), key=len) if question.split() else "")
    best = difflib.get_close_matches(guess, names, n=1, cutoff=0.4)
    selected_name = best[0] if best else names[0]
    selected = next((a for a in app_list if str(a.get("name") or a.get("id")) == selected_name), app_list[0])
    return selected, applications_tool

def find_tool(available: List[str], base: str) -> Optional[str]:
    t = match_tool_name(available, base)
    if not t:
        logger.info("Tool '%s' not found; continuing without it.", base)
    return t

def normalize_app_id(app: Dict[str, Any]) -> Any:
    return app.get("id") or app.get("applicationId") or app.get("name")
