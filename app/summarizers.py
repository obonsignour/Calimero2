import json
from typing import Any, Dict, List

import anthropic

from .config import get_anthropic_api_key, get_anthropic_model

def _join_text_blocks(resp) -> str:
    parts: List[str] = []
    for block in getattr(resp, "content", []) or []:
        if getattr(block, "type", "") == "text":
            parts.append(block.text)
    return "\n".join(parts) if parts else "(No content returned from LLM)"

def summarize_with_anthropic(payload: Dict[str, Any]) -> str:
    # Get API key dynamically
    api_key = get_anthropic_api_key()
    
    # Debug: Check if API key is loaded
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set or empty")
    
    # Debug: Log API key status (first few chars only for security)
    import logging
    import os
    logger = logging.getLogger("cast-imaging-agent.summarizers")
    logger.debug(f"ANTHROPIC_API_KEY loaded: {api_key[:10]}..." if api_key else "ANTHROPIC_API_KEY is empty")
    
    # Ensure no conflicting environment variables are set for Anthropic
    # Temporarily clear any auth-related env vars that might confuse the client
    original_env = {}
    conflicting_vars = ['X_API_KEY', 'AUTHORIZATION', 'AUTH_TOKEN']
    for var in conflicting_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    try:
        # Initialize client with explicit parameters
        client = anthropic.Anthropic(
            api_key=api_key,
            # Explicitly set other auth methods to None to avoid conflicts
            auth_token=None
        )
    finally:
        # Restore original environment variables
        for var, value in original_env.items():
            os.environ[var] = value
    system_msg = (
        "You are CAST Imaging Technical Copilot. "
        "Produce an accurate, concise technical summary for the selected application, "
        "grounded ONLY in the provided MCP data. If something is missing, say it's unavailable."
    )

    app_meta = payload.get("selected_application", {})
    stats = payload.get("stats")
    arch = payload.get("architectural_graph")
    qinsights = payload.get("quality_insights")
    packages = payload.get("packages")
    tx = payload.get("transactions")
    dg = payload.get("data_graphs")

    user_prompt = f"""
Question:
{payload.get("question")}

Application (selected):
{json.dumps(app_meta, indent=2)}

Key Data:
- Stats: {json.dumps(stats, indent=2) if stats is not None else "N/A"}
- Architectural Graph: {json.dumps(arch, indent=2) if arch is not None else "N/A"}
- Quality Insights: {json.dumps(qinsights, indent=2) if qinsights is not None else "N/A"}
- Packages / Technologies: {json.dumps(packages, indent=2) if packages is not None else "N/A"}
- Transactions: {json.dumps(tx, indent=2) if tx is not None else "N/A"}
- Data Graphs: {json.dumps(dg, indent=2) if dg is not None else "N/A"}

Instructions:
1) Start with a 2–3 sentence Overview.
2) Sections with bullets: Technologies, Architecture, Data Flows, Dependencies, Key Risks/Hotspots, Next Steps.
3) Reference concrete components where available; be explicit when info is not available.
"""
    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=1200,
        temperature=0.2,
        system=system_msg,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return _join_text_blocks(resp)

def summarize_impact_with_anthropic(payload: Dict[str, Any]) -> str:
    # Get API key dynamically
    api_key = get_anthropic_api_key()
    
    # Debug: Check if API key is loaded
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set or empty")
    
    # Debug: Log API key status (first few chars only for security)
    import logging
    import os
    logger = logging.getLogger("cast-imaging-agent.summarizers")
    logger.debug(f"ANTHROPIC_API_KEY loaded: {api_key[:10]}..." if api_key else "ANTHROPIC_API_KEY is empty")
    
    # Ensure no conflicting environment variables are set for Anthropic
    # Temporarily clear any auth-related env vars that might confuse the client
    original_env = {}
    conflicting_vars = ['X_API_KEY', 'AUTHORIZATION', 'AUTH_TOKEN']
    for var in conflicting_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    try:
        # Initialize client with explicit parameters
        client = anthropic.Anthropic(
            api_key=api_key,
            # Explicitly set other auth methods to None to avoid conflicts
            auth_token=None
        )
    finally:
        # Restore original environment variables
        for var, value in original_env.items():
            os.environ[var] = value
    system_msg = (
        "You are CAST Imaging Technical Copilot. Create an impact analysis report for a code change. "
        "Ground ONLY in provided MCP data. Be conservative: call out potential breakages, tests to run, and approvals."
    )
    app_meta = payload.get("selected_application", {})
    obj = payload.get("object_details")
    txu = payload.get("transactions_using_object")
    dgio = payload.get("data_graphs_involving_object")
    iad = payload.get("inter_applications_dependencies")
    question = payload.get("question")

    user_prompt = f"""
Question:
{question}

Application:
{json.dumps(app_meta, indent=2)}

Object Details:
{json.dumps(obj, indent=2)}

Transactions Using Object:
{json.dumps(txu, indent=2) if txu is not None else "N/A"}

Data Graphs Involving Object:
{json.dumps(dgio, indent=2) if dgio is not None else "N/A"}

Inter-Application Dependencies:
{json.dumps(iad, indent=2) if iad is not None else "N/A"}

Report format:
1) Scope: object(s) and application in scope; assumptions.
2) Direct Impacts: callers/callees, immediate dependencies.
3) Transaction Risks: user-facing transactions affected and why.
4) Data Impacts: tables/files/APIs touched and consistency concerns.
5) Cross-App Impacts: upstream/downstream apps; integration points.
6) Testing Plan: transactions to exercise; edge cases; data checks.
7) Controls/Approvals: security, PII, licensing, rollout/rollback suggestions.
If data is missing, say 'Not available from Imaging data.'
"""
    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=1400,
        temperature=0.2,
        system=system_msg,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return _join_text_blocks(resp)
