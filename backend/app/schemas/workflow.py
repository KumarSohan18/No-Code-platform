"""
Pydantic schemas for workflow-related data
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class NodeData(BaseModel):
    """Node data schema"""
    label: str
    placeholder: Optional[str] = None
    model: Optional[str] = None
    collection: Optional[str] = None
    topK: Optional[int] = 5
    threshold: Optional[float] = 0.7
    format: Optional[str] = "text"
    streaming: Optional[bool] = True
    use_web_search: Optional[bool] = False
    webSearchResults: Optional[int] = 10
    

class WorkflowNode(BaseModel):
    """Workflow node schema"""
    id: str
    type: str
    position: Dict[str, float]
    data: NodeData

class WorkflowEdge(BaseModel):
    """Workflow edge schema"""
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

class WorkflowCreate(BaseModel):
    """Create workflow schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []

class WorkflowUpdate(BaseModel):
    """Update workflow schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    is_active: Optional[bool] = None

class WorkflowResponse(BaseModel):
    """Workflow response schema"""
    id: int
    name: str
    description: Optional[str]
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class WorkflowListResponse(BaseModel):
    """Workflow list response schema"""
    workflows: List[WorkflowResponse]
    total: int
    page: int
    size: int

class WorkflowValidation(BaseModel):
    """Workflow validation schema"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    execution_order: List[str]
