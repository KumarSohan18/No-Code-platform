"""
Chat endpoints for workflow interaction
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging

from app.core.database import get_db, Workflow, ChatSession, ChatMessage, WorkflowExecution
from app.schemas.chat import (
    ChatMessageCreate, 
    ChatResponse, 
    ChatSessionResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse
)
from app.services.workflow_executor import WorkflowExecutor

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: dict,
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    try:
        workflow_id = request.get("workflow_id")
        if not workflow_id:
            raise HTTPException(status_code=400, detail="workflow_id is required")
        
        # Verify workflow exists
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Create session
        session_id = str(uuid.uuid4())
        chat_session = ChatSession(
            workflow_id=workflow_id,
            session_id=session_id
        )
        
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        
        logger.info(f"Created chat session: {session_id}")
        return chat_session
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get chat session with messages"""
    try:
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return chat_session
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/chat/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: str,
    message: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """Send message and get AI response"""
    logger.info(f"=== CHAT ROUTE CALLED ===")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Message: {message.message}")
    try:
        # Get chat session
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Save user message
        user_message = ChatMessage(
            session_id=chat_session.id,
            message_type="user",
            content=message.message
        )
        
        db.add(user_message)
        db.commit()
        
        # Get workflow
        workflow = db.query(Workflow).filter(
            Workflow.id == chat_session.workflow_id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Execute workflow
        executor = WorkflowExecutor()
        
        # Convert database format to schema format
        from app.schemas.workflow import WorkflowNode, WorkflowEdge
        
        logger.info(f"=== WORKFLOW STRUCTURE DEBUG ===")
        logger.info(f"Raw workflow nodes from DB: {workflow.nodes}")
        logger.info(f"Raw workflow edges from DB: {workflow.edges}")
        
        nodes = [WorkflowNode(**node) for node in workflow.nodes]
        edges = [WorkflowEdge(**edge) for edge in workflow.edges]
        
        logger.info(f"Parsed nodes: {[{'id': n.id, 'type': n.type} for n in nodes]}")
        logger.info(f"Parsed edges: {[{'source': e.source, 'target': e.target} for e in edges]}")
        logger.info(f"=== END WORKFLOW STRUCTURE DEBUG ===")
        
        # Prepare input data
        input_data = {
            "query": message.message,
            "session_id": session_id
        }
        
        # Execute workflow
        logger.info(f"Executing workflow for session {session_id} with input: {input_data}")
        result = await executor.execute_workflow(nodes, edges, input_data)
        logger.info(f"Workflow execution result: {result}")
        
        # Extract AI response
        ai_response = "Sorry, I couldn't process your request."
        if result.get("status") == "completed" and result.get("output"):
            # Find LLM component result first, then output component
            for node_id, output in result["output"].items():
                if isinstance(output, dict):
                    if output.get("type") == "llm_response":
                        ai_response = output.get("response", ai_response)
                        break
                    elif output.get("type") == "output":
                        ai_response = output.get("response", ai_response)
                        break
        else:
            logger.warning(f"Workflow execution failed or no output: {result}")
            ai_response = f"Workflow execution failed: {result.get('error', 'Unknown error')}"
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=chat_session.id,
            message_type="ai",
            content=ai_response,
            meta_data={
                "execution_log": result.get("execution_log"),
                "execution_time": result.get("execution_time"),
                "status": result.get("status")
            }
        )
        
        db.add(ai_message)
        db.commit()
        
        # Log execution
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            session_id=session_id,
            input_data=input_data,
            output_data=result.get("output"),
            execution_log=result.get("execution_log"),
            status=result.get("status", "completed"),
            execution_time=result.get("execution_time")
        )
        
        db.add(execution)
        db.commit()
        
        logger.info(f"Processed message in session {session_id}")
        
        return ChatResponse(
            message=ai_response,
            session_id=session_id,
            execution_log=result.get("execution_log"),
            processing_time=result.get("execution_time")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message in session {session_id}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/chat/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get chat messages for a session"""
    try:
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        return {"messages": messages}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete chat session and all messages"""
    try:
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Delete all messages
        db.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id
        ).delete()
        
        # Delete session
        db.delete(chat_session)
        db.commit()
        
        logger.info(f"Deleted chat session: {session_id}")
        return {"message": "Chat session deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/chat/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow_direct(
    request: WorkflowExecutionRequest,
    db: Session = Depends(get_db)
):
    """Execute workflow directly without chat session"""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == request.workflow_id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Execute workflow
        executor = WorkflowExecutor()
        
        # Convert database format to schema format
        from app.schemas.workflow import WorkflowNode, WorkflowEdge
        
        nodes = [WorkflowNode(**node) for node in workflow.nodes]
        edges = [WorkflowEdge(**edge) for edge in workflow.edges]
        
        # Execute workflow
        result = await executor.execute_workflow(nodes, edges, request.input_data)
        
        # Log execution
        execution = WorkflowExecution(
            workflow_id=request.workflow_id,
            session_id=request.session_id or "direct",
            input_data=request.input_data,
            output_data=result.get("output"),
            execution_log=result.get("execution_log"),
            status=result.get("status", "completed"),
            execution_time=result.get("execution_time")
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        return WorkflowExecutionResponse(
            execution_id=execution.id,
            status=result.get("status", "completed"),
            output_data=result.get("output"),
            execution_log=result.get("execution_log"),
            processing_time=result.get("execution_time"),
            error_message=result.get("error")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {request.workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
