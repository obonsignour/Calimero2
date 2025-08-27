import pytest
from types import SimpleNamespace

class FakeSession:
    async def list_tools(self):
        tools = [
            SimpleNamespace(name="applications"),
            SimpleNamespace(name="stats"),
            SimpleNamespace(name="object_details"),
            SimpleNamespace(name="transactions_using_object"),
            SimpleNamespace(name="data_graphs_involving_object"),
            SimpleNamespace(name="inter_applications_dependencies"),
            SimpleNamespace(name="architectural_graph"),
            SimpleNamespace(name="quality_insights"),
            SimpleNamespace(name="packages"),
            SimpleNamespace(name="applications_transactions"),
            SimpleNamespace(name="applications_data_graphs"),
        ]
        # Return object with .tools attribute to match MCP SDK structure
        return SimpleNamespace(tools=tools)
    
    async def call_tool(self, tool_name, args):
        return fake_call_tool(self, tool_name, args)

def fake_call_tool(session, tool_name, args):
    # Impact service tools
    if tool_name.endswith("applications"):
        return {"items": [{"id": "app1", "name": "Payments"}]}
    if tool_name.endswith("object_details"):
        return {"id": "obj-123", "name": args.get("name") or args.get("object") or args.get("object_id")}
    if tool_name.endswith("transactions_using_object"):
        return [{"transaction": "Checkout", "calls": ["OrderService.place"]}]
    if tool_name.endswith("data_graphs_involving_object"):
        return [{"entity": "orders", "fields": ["order_id", "amount"]}]
    if tool_name.endswith("inter_applications_dependencies"):
        return [{"from": "payments", "to": "billing"}]
    
    # Summary service tools
    if tool_name.endswith("stats"):
        return {"loc": 120_000, "objects": 5400}
    if tool_name.endswith("architectural_graph"):
        return {"nodes": [{"id": "svc1", "type": "service"}], "edges": []}
    if tool_name.endswith("quality_insights"):
        return {"issues": [{"rule": "CyclicDependency", "count": 3}]}
    if tool_name.endswith("packages"):
        return {"packages": [{"name": "Spring", "version": "5.x"}]}
    if tool_name.endswith("applications_transactions"):
        return [{"name": "Checkout", "entry": "/checkout"}]
    if tool_name.endswith("applications_data_graphs"):
        return [{"entity": "orders", "rels": ["order_items"]}]
    
    return None

class MockMCPContext:
    def __init__(self): 
        self.sess = FakeSession()
    async def __aenter__(self): 
        return self.sess
    async def __aexit__(self, exc_type, exc, tb): 
        return False

def fake_imaging_session():
    return MockMCPContext()

@pytest.fixture(autouse=True)
def mock_mcp_client():
    """Mock MCP client globally for all tests"""
    from app import mcp_client
    
    # Set the test implementation hook
    mcp_client.imaging_session._test_implementation = fake_imaging_session
    
    # Mock list_tools
    async def _list_tools(session):
        tools = await session.list_tools()
        return [t.name for t in tools]
    
    original_list_tools = mcp_client.list_tools
    original_call_tool = mcp_client.call_tool
    
    mcp_client.list_tools = _list_tools
    mcp_client.call_tool = fake_call_tool
    
    yield
    
    # Restore originals
    mcp_client.list_tools = original_list_tools
    mcp_client.call_tool = original_call_tool
    
    # Clean up test hook
    if hasattr(mcp_client.imaging_session, '_test_implementation'):
        delattr(mcp_client.imaging_session, '_test_implementation')
