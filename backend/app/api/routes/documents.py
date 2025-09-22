"""
Document management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging
from pathlib import Path

from app.core.database import get_db, Document
from app.schemas.document import (
    DocumentResponse, 
    DocumentListResponse,
    DocumentProcessResponse,
    DocumentSearchRequest,
    DocumentSearchResponse
)
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("default"),
    db: Session = Depends(get_db)
):
    """Upload and process a document"""
    try:
        logger.info(f"Received upload request for file: {file.filename}, collection: {collection}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate file type
        doc_service = DocumentService()
        if not doc_service.validate_file_type(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed types: {', '.join(doc_service.validate_file_type.__doc__ or [])}"
            )
        
        # Validate file size
        file_content = await file.read()
        if not doc_service.validate_file_size(len(file_content)):
            raise HTTPException(
                status_code=400, 
                detail="File size exceeds maximum allowed size"
            )
        
        # Save file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        logger.info(f"Created upload directory: {upload_dir}")
        
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Create document record
        document = Document(
            filename=file.filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=len(file_content),
            file_type=Path(file.filename).suffix.lower(),
            is_processed=False
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        logger.info(f"Uploaded document: {file.filename}")
        return document
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/documents/{document_id}/process", response_model=DocumentProcessResponse)
async def process_document(
    document_id: int,
    collection: str = "default",
    db: Session = Depends(get_db)
):
    """Process uploaded document for vector search"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.is_processed:
            raise HTTPException(status_code=400, detail="Document already processed")
        
        # Process document
        doc_service = DocumentService()
        result = await doc_service.process_document(
            file_path=document.file_path,
            filename=document.filename,
            collection_name=collection
        )
        
        if result["status"] == "success":
            # Update document record
            document.is_processed = True
            document.meta_data = {
                "collection": collection,
                "chunks_created": result["chunks_created"],
                "embeddings_generated": result["embeddings_generated"]
            }
            db.commit()
        
        return DocumentProcessResponse(
            document_id=document_id,
            status=result["status"],
            chunks_created=result.get("chunks_created", 0),
            embeddings_generated=result.get("embeddings_generated", 0),
            processing_time=0,  # TODO: Add timing
            error_message=result.get("error_message")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    processed_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List all documents"""
    try:
        # Calculate offset
        offset = (page - 1) * size
        
        # Build query
        query = db.query(Document)
        if processed_only:
            query = query.filter(Document.is_processed == True)
        
        # Get documents
        documents = query.offset(offset).limit(size).all()
        total = query.count()
        
        return DocumentListResponse(
            documents=documents,
            total=total,
            page=page,
            size=size
        )
    
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get document by ID"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete document"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from vector database if processed
        if document.is_processed and document.meta_data:
            doc_service = DocumentService()
            collection = document.meta_data.get("collection", "default")
            # TODO: Delete from vector database
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        logger.info(f"Deleted document: {document.filename}")
        return {"message": "Document deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/documents/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    db: Session = Depends(get_db)
):
    """Search documents using vector similarity"""
    try:
        doc_service = DocumentService()
        results = await doc_service.search_documents(
            query=request.query,
            collection_name=request.collection,
            top_k=request.top_k,
            threshold=request.threshold
        )
        
        return DocumentSearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time=0  # TODO: Add timing
        )
    
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/documents/collections")
async def list_collections():
    """List all document collections"""
    try:
        doc_service = DocumentService()
        collections = await doc_service.vector_service.list_collections()
        
        return {"collections": collections}
    
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/documents/collections/{collection_name}")
async def get_collection_info(collection_name: str):
    """Get collection information"""
    try:
        doc_service = DocumentService()
        info = await doc_service.get_document_info(collection_name)
        
        if not info:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        return info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection info for {collection_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
