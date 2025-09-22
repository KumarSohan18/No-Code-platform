#!/usr/bin/env python3
"""
Test script to check if all imports work correctly
"""

try:
    print("Testing imports...")
    
    print("1. Testing core imports...")
    from app.core.config import settings
    print("✓ Config imported successfully")
    
    from app.core.database import init_db, get_db, Base, Workflow, ChatSession, ChatMessage, Document, WorkflowExecution
    print("✓ Database models imported successfully")
    
    print("2. Testing schema imports...")
    from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse
    from app.schemas.chat import ChatMessageCreate, ChatResponse, ChatSessionResponse
    from app.schemas.document import DocumentResponse, DocumentListResponse
    print("✓ Schemas imported successfully")
    
    print("3. Testing service imports...")
    from app.services.workflow_executor import WorkflowExecutor
    from app.services.llm_service import LLMService
    from app.services.vector_service import VectorService
    from app.services.document_service import DocumentService
    print("✓ Services imported successfully")
    
    print("4. Testing route imports...")
    from app.api.routes import workflows, documents, chat, health
    print("✓ Routes imported successfully")
    
    print("\n✅ All imports successful! The backend should work now.")
    
except Exception as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
