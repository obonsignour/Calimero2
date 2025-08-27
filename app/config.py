import os
import json
import platform
from typing import Any, Dict, Tuple
from pathlib import Path

# Load .env file if it exists
def load_env_file():
    """Load environment variables from .env file in the project root"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already in environment (env vars take precedence)
                    if key not in os.environ:
                        os.environ[key] = value

# Load .env file on module import
load_env_file()

# Environment/config
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

def get_anthropic_api_key() -> str:
    """
    Get the Anthropic API key from environment variables.
    This function checks the environment each time it's called,
    ensuring we get the most up-to-date value.
    """
    return os.getenv("ANTHROPIC_API_KEY", "")

def get_anthropic_model() -> str:
    """
    Get the Anthropic model from environment variables.
    """
    return os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

MCP_CONFIG_PATH = os.getenv("MCP_CONFIG_PATH", "config/mcp.json")
MCP_IMAGING_URL_OVERRIDE = os.getenv("MCP_IMAGING_URL", None)
IMAGING_API_KEY = os.getenv("IMAGING_API_KEY", "")

def load_mcp_config() -> Dict[str, Any]:
    with open(MCP_CONFIG_PATH, "r") as f:
        return json.load(f)

def detect_platform_imaging_url() -> str:
    """
    Detect the platform and return the appropriate Imaging MCP server URL.
    
    Returns:
        - Linux/WSL: http://localhost:8282/mcp/
        - Windows: http://172.23.139.190:8282/mcp/
    """
    system = platform.system().lower()
    
    # Check if running on WSL (Windows Subsystem for Linux)
    is_wsl = False
    try:
        # WSL typically has 'microsoft' in the kernel release or version
        with open('/proc/version', 'r') as f:
            version_info = f.read().lower()
            is_wsl = 'microsoft' in version_info or 'wsl' in version_info
    except (FileNotFoundError, PermissionError):
        # /proc/version doesn't exist or can't be read - not Linux/WSL
        pass
    
    if system == 'linux' or is_wsl:
        # Linux or WSL - use localhost
        return "http://localhost:8282/mcp/"
    elif system == 'windows':
        # Native Windows - use specific IP
        return "http://172.23.139.190:8282/mcp/"
    else:
        # Default fallback for other systems (macOS, etc.)
        return "http://localhost:8282/mcp/"

def resolve_imaging_endpoint(cfg: Dict[str, Any]) -> Tuple[str, Dict[str, str]]:
    servers = cfg.get("servers", {})
    imaging = servers.get("imaging")
    if not imaging:
        raise RuntimeError("No 'imaging' server found in MCP config.")
    if imaging.get("type") != "http":
        raise RuntimeError("Expected 'http' type for 'imaging' server in MCP config.")

    headers = dict(imaging.get("headers", {}))

    # Priority order for determining base URL:
    # 1. Environment variable override (highest priority)
    # 2. Smart platform detection
    # 3. Config file URL (fallback)
    
    if MCP_IMAGING_URL_OVERRIDE:
        # Environment variable override takes precedence
        base_url = MCP_IMAGING_URL_OVERRIDE
    else:
        # Use smart platform detection to determine the appropriate URL
        base_url = detect_platform_imaging_url()
        
        # Log the detected platform and URL for debugging
        import logging
        logger = logging.getLogger("cast-imaging-agent.config")
        system = platform.system()
        logger.info(f"Detected platform: {system}, using Imaging MCP URL: {base_url}")

    # Replace ${input:...} placeholders with the IMAGING_API_KEY env var at runtime.
    for k, v in list(headers.items()):
        if isinstance(v, str) and v.startswith("${input:"):
            headers[k] = IMAGING_API_KEY

    if not base_url:
        raise RuntimeError("Imaging MCP base URL missing from config.")
    return base_url, headers
