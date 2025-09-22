"""
Workflow management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db, Workflow
from app.schemas.workflow import (
    WorkflowCreate, 
    WorkflowUpdate, 
    WorkflowResponse, 
    WorkflowListResponse,
    WorkflowValidation
)
from app.services.workflow_executor import WorkflowExecutor

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db)
):
    """Create a new workflow"""
    try:
        # Only validate if workflow has nodes (allow empty workflows for initial creation)
        if workflow.nodes:
            executor = WorkflowExecutor()
            validation = await executor.validate_workflow(workflow.nodes, workflow.edges)
            
            if not validation.is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid workflow: {', '.join(validation.errors)}"
                )
        
        # Create workflow in database
        db_workflow = Workflow(
            name=workflow.name,
            description=workflow.description,
            nodes=[node.dict() for node in workflow.nodes],
            edges=[edge.dict() for edge in workflow.edges]
        )
        
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        
        logger.info(f"Created workflow: {workflow.name}")
        return db_workflow
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all workflows"""
    try:
        # Calculate offset
        offset = (page - 1) * size
        
        # Get workflows
        workflows = db.query(Workflow).offset(offset).limit(size).all()
        total = db.query(Workflow).count()
        
        return WorkflowListResponse(
            workflows=workflows,
            total=total,
            page=page,
            size=size
        )
    
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    """Get workflow by ID"""
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return workflow
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_update: WorkflowUpdate,
    db: Session = Depends(get_db)
):
    """Update workflow"""
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update fields
        if workflow_update.name is not None:
            workflow.name = workflow_update.name
        if workflow_update.description is not None:
            workflow.description = workflow_update.description
        if workflow_update.nodes is not None:
            workflow.nodes = [node.dict() for node in workflow_update.nodes]
        if workflow_update.edges is not None:
            workflow.edges = [edge.dict() for edge in workflow_update.edges]
        if workflow_update.is_active is not None:
            workflow.is_active = workflow_update.is_active
        
        db.commit()
        db.refresh(workflow)
        
        logger.info(f"Updated workflow: {workflow.name}")
        return workflow
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    """Delete workflow"""
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        db.delete(workflow)
        db.commit()
        
        logger.info(f"Deleted workflow: {workflow.name}")
        return {"message": "Workflow deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/workflows/{workflow_id}/validate", response_model=WorkflowValidation)
async def validate_workflow(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    """Validate workflow structure"""
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Convert database format to schema format
        from app.schemas.workflow import WorkflowNode, WorkflowEdge
        
        nodes = [WorkflowNode(**node) for node in workflow.nodes]
        edges = [WorkflowEdge(**edge) for edge in workflow.edges]
        
        # Validate workflow
        executor = WorkflowExecutor()
        validation = await executor.validate_workflow(nodes, edges)
        
        return validation
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: int,
    input_data: dict,
    db: Session = Depends(get_db)
):
    """Execute workflow with input data"""
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if not workflow.is_active:
            raise HTTPException(status_code=400, detail="Workflow is not active")
        
        # Convert database format to schema format
        from app.schemas.workflow import WorkflowNode, WorkflowEdge
        
        nodes = [WorkflowNode(**node) for node in workflow.nodes]
        edges = [WorkflowEdge(**edge) for edge in workflow.edges]
        
        # Execute workflow
        executor = WorkflowExecutor()
        result = await executor.execute_workflow(nodes, edges, input_data)
        
        # Log execution in database
        from app.core.database import WorkflowExecution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            session_id=input_data.get("session_id", "default"),
            input_data=input_data,
            output_data=result.get("output"),
            execution_log=result.get("execution_log"),
            status=result.get("status", "completed"),
            execution_time=result.get("execution_time")
        )
        
        db.add(execution)
        db.commit()
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
