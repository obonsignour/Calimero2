from typing import Any, Dict, Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    application_hint: Optional[str] = None

class QueryResponse(BaseModel):
    application: Dict[str, Any]
    summary: str

class ImpactRequest(BaseModel):
    question: str = "What breaks if we change X?"
    object_hint: str
    application_hint: Optional[str] = None

class ImpactResponse(BaseModel):
    application: Dict[str, Any]
    object: Dict[str, Any]
    summary: str
