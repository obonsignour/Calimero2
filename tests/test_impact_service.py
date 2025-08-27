import pytest
from types import SimpleNamespace
from app.services.impact_service import fetch_impact_analysis

pytestmark = pytest.mark.asyncio

# Mock objects are defined in conftest.py

# MCP mocking is now handled globally in conftest.py

async def test_fetch_impact_analysis_happy_path():
    payload = await fetch_impact_analysis(
        "What breaks if we change X?",
        object_hint="com.acme.OrderService",
        app_hint="Payments"
    )
    assert payload["selected_application"]["name"] == "Payments"
    assert payload["object_details"]["id"] == "obj-123"
    assert payload["transactions_using_object"][0]["transaction"] == "Checkout"
    assert payload["data_graphs_involving_object"][0]["entity"] == "orders"
    assert payload["inter_applications_dependencies"][0]["to"] == "billing"
