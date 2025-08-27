import pytest
import httpx
from types import SimpleNamespace

# Test the actual ASGI app exported by your API layer
from app.api.main import app

pytestmark = pytest.mark.asyncio

# --------------------------
# LLM mocking for API tests
# --------------------------

@pytest.fixture(autouse=True)
def patch_llm_summarizers(monkeypatch):
    # Patch LLM summarizers imported in the API module
    import app.api.main as api_main
    monkeypatch.setattr(api_main, "summarize_with_anthropic", lambda payload: "SUMMARY OK")
    monkeypatch.setattr(api_main, "summarize_impact_with_anthropic", lambda payload: "IMPACT OK")
    yield

# --------------------------
# Tests
# --------------------------

async def test_query_route_ok():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={"question": "Summarize the technical details of the Payments app", "application_hint": "Payments"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["application"]["name"] == "Payments"
        assert data["summary"] == "SUMMARY OK"

async def test_impact_route_ok():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/impact",
            json={
                "question": "What breaks if we change X?",
                "application_hint": "Payments",
                "object_hint": "com.acme.payments.OrderService",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["application"]["name"] == "Payments"
        assert data["object"]["id"] == "obj-123"
        assert data["summary"] == "IMPACT OK"
