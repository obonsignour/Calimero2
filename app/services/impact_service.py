import asyncio
from typing import Any, Dict, Optional

from ..mcp_client import imaging_session, list_tools, call_tool
from ..tools import find_tool, select_application, normalize_app_id, match_tool_name

async def _resolve_object_details(session, tool_names, app_id: Any, object_hint: str) -> Dict[str, Any]:
    od_tool = match_tool_name(tool_names, "object_details")
    if not od_tool:
        raise RuntimeError("Imaging MCP: 'object_details' tool not found.")

    candidates = [
        {"app_id": app_id, "object_id": object_hint},
        {"app_id": app_id, "name": object_hint},
        {"app_id": app_id, "query": object_hint},
        {"app_id": app_id, "object": object_hint},
    ]
    last_err: Optional[Exception] = None
    for args in candidates:
        try:
            res = await call_tool(session, od_tool, args)
            if res:
                return res
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Unable to resolve object '{object_hint}' via object_details. Last error: {last_err}")

async def fetch_impact_analysis(question: str, object_hint: str, app_hint: Optional[str] = None) -> Dict[str, Any]:
    async with imaging_session() as session:
        tool_names = await list_tools(session)
        selected, _ = await select_application(session, tool_names, question, app_hint)
        app_id = normalize_app_id(selected)

        obj_details = await _resolve_object_details(session, tool_names, app_id, object_hint)

        txu_tool = find_tool(tool_names, "transactions_using_object")
        dgio_tool = find_tool(tool_names, "data_graphs_involving_object") or find_tool(tool_names, "datagraphs_involving_object")
        iad_tool = find_tool(tool_names, "inter_applications_dependencies")

        oid = (
            obj_details.get("id")
            or obj_details.get("objectId")
            or obj_details.get("object_id")
            or object_hint
        )

        calls = []
        if txu_tool:
            calls.append(call_tool(session, txu_tool, {"app_id": app_id, "object_id": oid, "limit": 50}))
        else:
            calls.append(asyncio.sleep(0, result=None))
        if dgio_tool:
            calls.append(call_tool(session, dgio_tool, {"app_id": app_id, "object_id": oid, "limit": 50}))
        else:
            calls.append(asyncio.sleep(0, result=None))
        if iad_tool:
            calls.append(call_tool(session, iad_tool, {"app_id": app_id, "object_id": oid, "limit": 50}))
        else:
            calls.append(asyncio.sleep(0, result=None))

        txu, dgio, iad = await asyncio.gather(*calls)

    return {
        "question": question,
        "selected_application": selected,
        "object_hint": object_hint,
        "object_details": obj_details,
        "transactions_using_object": txu,
        "data_graphs_involving_object": dgio,
        "inter_applications_dependencies": iad,
        "tool_names": tool_names,
    }
