import asyncio
import pytest
from types import SimpleNamespace

from app.services.summary_service import fetch_application_summary

pytestmark = pytest.mark.asyncio

# Mock objects are defined in conftest.py

# MCP mocking is now handled globally in conftest.py

async def test_fetch_application_summary_happy_path():
    payload = await fetch_application_summary("Summarize Payments", app_hint="Payments")
    assert payload["selected_application"]["name"] == "Payments"
    assert payload["stats"]["loc"] == 120_000
    assert payload["architectural_graph"]["nodes"][0]["id"] == "svc1"
    assert payload["quality_insights"]["issues"][0]["rule"] == "CyclicDependency"
    assert payload["packages"]["packages"][0]["name"] == "Spring"
    assert payload["transactions"][0]["name"] == "Checkout"
    assert payload["data_graphs"][0]["entity"] == "orders"
