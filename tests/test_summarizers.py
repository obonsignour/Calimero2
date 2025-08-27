import types
import pytest

from app import summarizers

class FakeMsgResp:
    def __init__(self, text):
        self.content = [types.SimpleNamespace(type="text", text=text)]

class FakeMessagesAPI:
    def __init__(self, ret_text):
        self._ret_text = ret_text
    def create(self, **kwargs):
        # sanity on required fields
        assert "model" in kwargs and "messages" in kwargs and "system" in kwargs
        return FakeMsgResp(self._ret_text)

class FakeAnthropicClient:
    def __init__(self, api_key=None):  # signature compatibility
        self.messages = FakeMessagesAPI("OK!")

@pytest.fixture(autouse=True)
def patch_anthropic(monkeypatch):
    # Replace anthropic.Anthropic with our fake client
    import app.summarizers as s
    monkeypatch.setattr(s, "anthropic", types.SimpleNamespace(Anthropic=FakeAnthropicClient))
    yield

def test_summarize_with_anthropic_basic():
    payload = {
        "question": "Summarize app",
        "selected_application": {"id": "app1", "name": "Payments"},
        "stats": {"loc": 100},
    }
    out = summarizers.summarize_with_anthropic(payload)
    assert "OK!" in out

def test_summarize_impact_with_anthropic_basic():
    payload = {
        "question": "What breaks?",
        "selected_application": {"id": "app1", "name": "Payments"},
        "object_details": {"id": "obj-1"},
        "transactions_using_object": [],
        "data_graphs_involving_object": [],
        "inter_applications_dependencies": [],
    }
    out = summarizers.summarize_impact_with_anthropic(payload)
    assert "OK!" in out
