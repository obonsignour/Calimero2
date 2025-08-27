import pytest
from app.tools import match_tool_name, normalize_app_id

def test_match_tool_name_exact():
    names = ["applications", "stats", "packages"]
    assert match_tool_name(names, "applications") == "applications"

def test_match_tool_name_suffix():
    names = ["bb7_applications", "zz_quality_insights"]
    assert match_tool_name(names, "applications") == "bb7_applications"
    assert match_tool_name(names, "quality_insights") == "zz_quality_insights"

def test_match_tool_name_fuzzy():
    names = ["applics", "statz"]
    # fuzzy will pick closest; behavior is best-effort
    assert match_tool_name(names, "stats") in names

def test_normalize_app_id_prefers_id():
    app = {"id": "A1", "applicationId": "A2", "name": "Payments"}
    assert normalize_app_id(app) == "A1"

def test_normalize_app_id_fallbacks():
    assert normalize_app_id({"applicationId": "X"}) == "X"
    assert normalize_app_id({"name": "Y"}) == "Y"
