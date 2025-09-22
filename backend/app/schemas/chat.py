"""
Pydantic schemas for chat-related data
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatMessageCreate(BaseModel):
    """Create chat message schema"""
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    """Chat message response schema"""
    id: int
    message_type: str
    content: str
    meta_data: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    """Chat session response schema"""
    id: int
    session_id: str
    workflow_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    messages: List[ChatMessageResponse]

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    """Chat response schema"""
    message: str
    session_id: str
    execution_log: Optional[Dict[str, Any]] = None
    processing_time: Optional[int] = None  # in milliseconds

class WorkflowExecutionRequest(BaseModel):
    """Workflow execution request schema"""
    workflow_id: int
    input_data: Dict[str, Any]
    session_id: Optional[str] = None

class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response schema"""
    execution_id: int
    status: str
    output_data: Optional[Dict[str, Any]]
    execution_log: Optional[Dict[str, Any]]
    processing_time: Optional[int]
    error_message: Optional[str]
