"""
Pydantic schemas for document-related data
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class DocumentUpload(BaseModel):
    """Document upload schema"""
    filename: str
    collection: Optional[str] = "default"

class DocumentResponse(BaseModel):
    """Document response schema"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    is_processed: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    """Document list response schema"""
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int

class DocumentProcessResponse(BaseModel):
    """Document processing response schema"""
    document_id: int
    status: str
    chunks_created: int
    embeddings_generated: int
    processing_time: int  # in milliseconds
    error_message: Optional[str] = None

class DocumentSearchRequest(BaseModel):
    """Document search request schema"""
    query: str = Field(..., min_length=1, max_length=1000)
    collection: Optional[str] = "default"
    top_k: int = Field(5, ge=1, le=50)
    threshold: float = Field(0.7, ge=0.0, le=1.0)

class DocumentSearchResult(BaseModel):
    """Document search result schema"""
    document_id: int
    filename: str
    content: str
    similarity_score: float
    meta_data: Optional[Dict[str, Any]]

class DocumentSearchResponse(BaseModel):
    """Document search response schema"""
    query: str
    results: List[DocumentSearchResult]
    total_results: int
    search_time: int  # in milliseconds
