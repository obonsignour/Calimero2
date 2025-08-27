import asyncio
from typing import Any, Dict, Optional

from ..mcp_client import imaging_session, list_tools, call_tool
from ..tools import find_tool, select_application, normalize_app_id

async def test_imaging_connection() -> Dict[str, Any]:
    """
    Test connection to the MCP imaging service
    """
    try:
        async with imaging_session() as session:
            tool_names = await list_tools(session)
            return {
                "status": "connected",
                "available_tools": len(tool_names),
                "tools": tool_names[:5]  # Show first 5 tools
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

async def fetch_application_summary(question: str, app_hint: Optional[str] = None) -> Dict[str, Any]:
    try:
        async with imaging_session() as session:
            # Step 1: Get available tools
            try:
                tool_names = await list_tools(session)
                if not tool_names:
                    raise ValueError("No tools available from imaging service")
            except Exception as e:
                raise RuntimeError(f"Failed to list tools from imaging service: {str(e)}") from e

            # Step 2: Select application
            try:
                selected, _ = await select_application(session, tool_names, question, app_hint)
                if not selected:
                    raise ValueError("No application could be selected based on the provided criteria")
                app_id = normalize_app_id(selected)
                if not app_id:
                    raise ValueError(f"Failed to normalize application ID from selected application: {selected}")
            except Exception as e:
                raise RuntimeError(f"Failed to select application: {str(e)}") from e

            # Step 3: Find required tools
            stats_tool     = find_tool(tool_names, "stats")
            arch_tool      = find_tool(tool_names, "architectural_graph")
            qinsights_tool = find_tool(tool_names, "quality_insights")
            packages_tool  = find_tool(tool_names, "packages")

            # Step 4: Execute parallel tool calls with error handling
            common_args = {"app_id": app_id}
            tasks = []
            task_names = []
            
            if stats_tool:
                tasks.append(call_tool(session, stats_tool, dict(common_args)))
                task_names.append("stats")
            else:
                tasks.append(asyncio.sleep(0, result=None))
                task_names.append("stats (not available)")
                
            if arch_tool:
                tasks.append(call_tool(session, arch_tool, {**common_args, "granularity": "components"}))
                task_names.append("architectural_graph")
            else:
                tasks.append(asyncio.sleep(0, result=None))
                task_names.append("architectural_graph (not available)")
                
            if qinsights_tool:
                tasks.append(call_tool(session, qinsights_tool, dict(common_args)))
                task_names.append("quality_insights")
            else:
                tasks.append(asyncio.sleep(0, result=None))
                task_names.append("quality_insights (not available)")
                
            if packages_tool:
                tasks.append(call_tool(session, packages_tool, dict(common_args)))
                task_names.append("packages")
            else:
                tasks.append(asyncio.sleep(0, result=None))
                task_names.append("packages (not available)")

            try:
                stats, arch, qinsights, packages = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for exceptions in parallel tasks
                for i, (result, task_name) in enumerate(zip([stats, arch, qinsights, packages], task_names)):
                    if isinstance(result, Exception):
                        # Log the error but don't fail the entire operation
                        print(f"Warning: Task '{task_name}' failed: {str(result)}")
                        # Replace exception with None
                        if i == 0:
                            stats = None
                        elif i == 1:
                            arch = None
                        elif i == 2:
                            qinsights = None
                        elif i == 3:
                            packages = None
                            
            except Exception as e:
                raise RuntimeError(f"Failed to execute parallel tool calls: {str(e)}") from e

            # Step 5: Execute additional tool calls
            tx_tool = find_tool(tool_names, "applications_transactions")
            dgraph_tool = find_tool(tool_names, "applications_data_graphs")
            
            tx = None
            dg = None
            
            if tx_tool:
                try:
                    tx = await call_tool(session, tx_tool, {"app_id": app_id, "limit": 50})
                except Exception as e:
                    print(f"Warning: Failed to get transactions: {str(e)}")
                    tx = None
                    
            if dgraph_tool:
                try:
                    dg = await call_tool(session, dgraph_tool, {"app_id": app_id, "limit": 50})
                except Exception as e:
                    print(f"Warning: Failed to get data graphs: {str(e)}")
                    dg = None

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
        
    except Exception as e:
        # Re-raise with more context
        error_msg = f"fetch_application_summary failed for question '{question}'"
        if app_hint:
            error_msg += f" with app_hint '{app_hint}'"
        error_msg += f": {str(e)}"
        raise RuntimeError(error_msg) from e
