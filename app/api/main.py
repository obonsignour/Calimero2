import logging
from fastapi import FastAPI, HTTPException
import uvicorn

from ..services.summary_service import fetch_application_summary
from ..services.impact_service import fetch_impact_analysis
from ..summarizers import summarize_with_anthropic, summarize_impact_with_anthropic
from .schemas import QueryRequest, QueryResponse, ImpactRequest, ImpactResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cast-imaging-agent.api")

app = FastAPI(title="CAST Imaging Agent (Anthropic Sonnet)")

@app.get("/healthz")
def health():
    return {"status": "ok"}

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
