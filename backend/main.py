"""
GenAI Stack Backend - Main FastAPI Application
A No-Code/Low-Code workflow builder for intelligent AI workflows
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import workflows, documents, chat, health
from app.services.workflow_executor import WorkflowExecutor
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService
from app.services.document_service import DocumentService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting GenAI Stack Backend...")
    await init_db()
    logger.info("Database initialized")
    
    # Initialize services
    app.state.workflow_executor = WorkflowExecutor()
    app.state.llm_service = LLMService()
    app.state.vector_service = VectorService()
    app.state.document_service = DocumentService()
    
    logger.info("Services initialized")
    yield
    
    # Shutdown
    logger.info("Shutting down GenAI Stack Backend...")

# Create FastAPI application
app = FastAPI(
    title="GenAI Stack API",
    description="Backend API for No-Code/Low-Code AI Workflow Builder",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GenAI Stack API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )