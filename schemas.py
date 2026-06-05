from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    question:   str
    session_id: str = "default"

class Source(BaseModel):
    content:  str
    doc_type: str

class ChatResponse(BaseModel):
    answer:     str
    sources:    List[Source]
    session_id: str
    tools_used: List[str]