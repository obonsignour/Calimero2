import os
import json
from typing import Any, Dict, Tuple

# Environment/config
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

MCP_CONFIG_PATH = os.getenv("MCP_CONFIG_PATH", "config/mcp.json")
MCP_IMAGING_URL_OVERRIDE = os.getenv("MCP_IMAGING_URL", None)
IMAGING_API_KEY = os.getenv("IMAGING_API_KEY", "")

def load_mcp_config() -> Dict[str, Any]:
    with open(MCP_CONFIG_PATH, "r") as f:
        return json.load(f)

def resolve_imaging_endpoint(cfg: Dict[str, Any]) -> Tuple[str, Dict[str, str]]:
    servers = cfg.get("servers", {})
    imaging = servers.get("imaging")
    if not imaging:
        raise RuntimeError("No 'imaging' server found in MCP config.")
    if imaging.get("type") != "http":
        raise RuntimeError("Expected 'http' type for 'imaging' server in MCP config.")

    base_url = imaging.get("url")
    headers = dict(imaging.get("headers", {}))

    # Container/network override, e.g. http://imaging-mcp:8282/mcp/
    if MCP_IMAGING_URL_OVERRIDE:
        base_url = MCP_IMAGING_URL_OVERRIDE

    # Replace ${input:...} placeholders with the IMAGING_API_KEY env var at runtime.
    for k, v in list(headers.items()):
        if isinstance(v, str) and v.startswith("${input:"):
            headers[k] = IMAGING_API_KEY

    if not base_url:
        raise RuntimeError("Imaging MCP base URL missing from config.")
    return base_url, headers
