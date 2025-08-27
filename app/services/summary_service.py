import asyncio
from typing import Any, Dict, Optional

from ..mcp_client import imaging_session, list_tools, call_tool
from ..tools import find_tool, select_application, normalize_app_id

async def fetch_application_summary(question: str, app_hint: Optional[str] = None) -> Dict[str, Any]:
    async with imaging_session() as session:
        tool_names = await list_tools(session)
        selected, _ = await select_application(session, tool_names, question, app_hint)
        app_id = normalize_app_id(selected)

        stats_tool     = find_tool(tool_names, "stats")
        arch_tool      = find_tool(tool_names, "architectural_graph")
        qinsights_tool = find_tool(tool_names, "quality_insights")
        packages_tool  = find_tool(tool_names, "packages")

        common_args = {"app_id": app_id}
        tasks = [
            call_tool(session, stats_tool, dict(common_args)) if stats_tool else asyncio.sleep(0, result=None),
            call_tool(session, arch_tool, {**common_args, "granularity": "components"}) if arch_tool else asyncio.sleep(0, result=None),
            call_tool(session, qinsights_tool, dict(common_args)) if qinsights_tool else asyncio.sleep(0, result=None),
            call_tool(session, packages_tool, dict(common_args)) if packages_tool else asyncio.sleep(0, result=None),
        ]
        stats, arch, qinsights, packages = await asyncio.gather(*tasks)

        tx_tool = find_tool(tool_names, "applications_transactions")
        dgraph_tool = find_tool(tool_names, "applications_data_graphs")
        tx = await call_tool(session, tx_tool, {"app_id": app_id, "limit": 50}) if tx_tool else None
        dg = await call_tool(session, dgraph_tool, {"app_id": app_id, "limit": 50}) if dgraph_tool else None

    return {
        "question": question,
        "selected_application": selected,
        "stats": stats,
        "architectural_graph": arch,
        "quality_insights": qinsights,
        "packages": packages,
        "transactions": tx,
        "data_graphs": dg,
        "tool_names": tool_names,
    }
