import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

from ..services.summary_service import fetch_application_summary
from ..services.impact_service import fetch_impact_analysis
from ..summarizers import summarize_with_anthropic, summarize_impact_with_anthropic
from .schemas import QueryRequest, QueryResponse, ImpactRequest, ImpactResponse

# Configure logging to show more details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cast-imaging-agent.api")

# Enable debug logging for our tools module
tools_logger = logging.getLogger("cast-imaging-agent.tools")
tools_logger.setLevel(logging.INFO)

app = FastAPI(
    title="CAST Imaging Agent (Anthropic Sonnet)",
    description="API for application analysis and impact assessment using CAST Imaging and Anthropic AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/", response_class=HTMLResponse)
def root():
    """
    API information and usage guide
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CAST Imaging Agent API</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
            }
            .endpoint {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
                border-left: 4px solid #3498db;
            }
            .method {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                color: white;
            }
            .get { background-color: #28a745; }
            .post { background-color: #007bff; }
            pre {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }
            .links {
                margin: 20px 0;
            }
            .links a {
                display: inline-block;
                padding: 10px 20px;
                margin: 5px 10px 5px 0;
                background: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s;
            }
            .links a:hover {
                background: #2980b9;
            }
            .status {
                display: inline-block;
                padding: 5px 10px;
                background: #28a745;
                color: white;
                border-radius: 15px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 CAST Imaging Agent (Anthropic Sonnet)</h1>
            <p><strong>Version:</strong> 1.0.0 <span class="status">Running</span></p>
            <p>API for application analysis and impact assessment using CAST Imaging and Anthropic AI</p>
            
            <div class="links">
                <a href="/docs">📚 Interactive API Docs</a>
                <a href="/redoc">📖 ReDoc Documentation</a>
                <a href="/healthz">❤️ Health Check</a>
            </div>

            <h2>📋 Available Endpoints</h2>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span> /</h3>
                <p>API information and usage guide (this page)</p>
            </div>

            <div class="endpoint">
                <h3><span class="method get">GET</span> /healthz</h3>
                <p>Health check endpoint - returns server status</p>
            </div>

            <div class="endpoint">
                <h3><span class="method post">POST</span> /query</h3>
                <p>Get application summary based on a question</p>
                <strong>Example Request:</strong>
                <pre>{
  "question": "What does this application do?",
  "application_hint": "optional application name"
}</pre>
            </div>

            <div class="endpoint">
                <h3><span class="method post">POST</span> /impact</h3>
                <p>Analyze impact of changes to objects</p>
                <strong>Example Request:</strong>
                <pre>{
  "question": "What breaks if we change X?",
  "object_hint": "class or method name",
  "application_hint": "optional application name"
}</pre>
            </div>

            <h2>🔧 Quick Start</h2>
            <p>Use the interactive documentation at <a href="/docs">/docs</a> to test the API endpoints directly in your browser.</p>
            
            <h2>📡 Example cURL Commands</h2>
            <strong>Query endpoint:</strong>
            <pre>curl -X POST "http://localhost:8000/query" \\
     -H "Content-Type: application/json" \\
     -d '{"question": "What does this application do?"}'</pre>
            
            <strong>Impact endpoint:</strong>
            <pre>curl -X POST "http://localhost:8000/impact" \\
     -H "Content-Type: application/json" \\
     -d '{"object_hint": "UserService", "question": "What breaks if we change this?"}'</pre>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/healthz", response_class=HTMLResponse)
async def health():
    """
    Health check endpoint that also verifies MCP imaging service connectivity
    """
    # Collect health information
    overall_status = "ok"
    platform_info = {}
    imaging_status = {}
    
    # Show which Imaging MCP URL is being used
    try:
        from ..config import load_mcp_config, resolve_imaging_endpoint, detect_platform_imaging_url
        import platform
        import os
        from pathlib import Path
        
        # Get the resolved URL
        cfg = load_mcp_config()
        base_url, headers = resolve_imaging_endpoint(cfg)
        
        # Show platform detection info
        detected_url = detect_platform_imaging_url()
        override_url = os.getenv("MCP_IMAGING_URL")
        
        platform_info = {
            "system": platform.system(),
            "detected_url": detected_url,
            "override_url": override_url,
            "resolved_url": base_url,
            "env_file_loaded": "✅ .env file found and loaded" if (Path(__file__).parent.parent.parent / '.env').exists() else "❌ No .env file found"
        }
        
    except Exception as e:
        platform_info = {
            "error": f"Failed to resolve platform info: {str(e)}"
        }
    
    try:
        # Test MCP imaging service connectivity
        from ..services.summary_service import test_imaging_connection
        imaging_status = await test_imaging_connection()
    except Exception as e:
        imaging_status = {
            "status": "error",
            "error": str(e)
        }
        overall_status = "degraded"
    
    # Determine status colors and icons
    if overall_status == "ok":
        status_color = "#28a745"
        status_icon = "✅"
        status_text = "Healthy"
    else:
        status_color = "#ffc107"
        status_icon = "⚠️"
        status_text = "Degraded"
    
    # MCP service status
    mcp_status = imaging_status.get("status", "unknown")
    if mcp_status == "connected":
        mcp_color = "#28a745"
        mcp_icon = "🟢"
        mcp_text = "Connected"
    elif mcp_status == "error":
        mcp_color = "#dc3545"
        mcp_icon = "🔴"
        mcp_text = "Connection Failed"
    else:
        mcp_color = "#6c757d"
        mcp_icon = "⚪"
        mcp_text = "Unknown"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CAST Imaging Agent - Health Check</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 30px;
            }}
            .status-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin: 15px 0;
                border-left: 4px solid {status_color};
            }}
            .service-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin: 15px 0;
                border-left: 4px solid {mcp_color};
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 2fr;
                gap: 10px;
                margin: 15px 0;
            }}
            .info-label {{
                font-weight: bold;
                color: #495057;
            }}
            .info-value {{
                font-family: 'Courier New', monospace;
                background: #e9ecef;
                padding: 4px 8px;
                border-radius: 4px;
                word-break: break-all;
            }}
            .status-badge {{
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                color: white;
                font-weight: bold;
                background-color: {status_color};
            }}
            .service-badge {{
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                color: white;
                font-weight: bold;
                background-color: {mcp_color};
            }}
            .back-link {{
                display: inline-block;
                padding: 10px 20px;
                background: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
                transition: background 0.3s;
            }}
            .back-link:hover {{
                background: #2980b9;
            }}
            .error-text {{
                color: #dc3545;
                font-style: italic;
            }}
            .success-text {{
                color: #28a745;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 CAST Imaging Agent - Health Check</h1>
            
            <div class="status-card">
                <h2>{status_icon} Overall Status: <span class="status-badge">{status_text}</span></h2>
                <p>System health and service connectivity status</p>
            </div>

            <div class="service-card">
                <h2>{mcp_icon} Imaging MCP Service: <span class="service-badge">{mcp_text}</span></h2>
                
                <h3>🔧 Platform Detection</h3>
                <div class="info-grid">
                    <div class="info-label">Operating System:</div>
                    <div class="info-value">{platform_info.get('system', 'Unknown')}</div>
                    
                    <div class="info-label">Auto-Detected URL:</div>
                    <div class="info-value">{platform_info.get('detected_url', 'N/A')}</div>
                    
                    <div class="info-label">Environment Override:</div>
                    <div class="info-value">{platform_info.get('override_url') or 'None'}</div>
                    
                    <div class="info-label">Final Resolved URL:</div>
                    <div class="info-value">{platform_info.get('resolved_url', 'N/A')}</div>
                </div>
                
                <h3>📊 Connection Details</h3>
                {"<div class='success-text'>✅ Successfully connected to Imaging MCP service</div>" if mcp_status == "connected" else f"<div class='error-text'>❌ Connection failed: {imaging_status.get('error', 'Unknown error')}</div>"}
                
                {f"<div class='info-grid'><div class='info-label'>Available Tools:</div><div class='info-value'>{imaging_status.get('available_tools', 0)}</div></div>" if mcp_status == "connected" else ""}
            </div>

            <div class="status-card">
                <h3>💡 Troubleshooting Tips</h3>
                <ul>
                    <li><strong>Connection Refused:</strong> Make sure the Imaging MCP server is running on the resolved URL</li>
                    <li><strong>Wrong URL:</strong> Set <code>MCP_IMAGING_URL</code> environment variable to override auto-detection</li>
                    <li><strong>Authentication:</strong> Ensure <code>IMAGING_API_KEY</code> environment variable is set</li>
                    <li><strong>Platform Issues:</strong> Verify the auto-detected URL matches your setup</li>
                </ul>
            </div>

            <a href="/" class="back-link">← Back to API Home</a>
        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    try:
        payload = await fetch_application_summary(req.question, req.application_hint)
        summary = summarize_with_anthropic(payload)
        return QueryResponse(application=payload.get("selected_application", {}), summary=summary)
    except Exception as e:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/impact", response_model=ImpactResponse)
async def impact(req: ImpactRequest):
    try:
        payload = await fetch_impact_analysis(req.question, req.object_hint, req.application_hint)
        summary = summarize_impact_with_anthropic(payload)
        return ImpactResponse(
            application=payload.get("selected_application", {}),
            object=payload.get("object_details", {}),
            summary=summary,
        )
    except Exception as e:
        logger.exception("Impact analysis failed")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=False)
