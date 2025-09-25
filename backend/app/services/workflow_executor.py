"""
Workflow execution engine for processing AI workflows
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.schemas.workflow import WorkflowNode, WorkflowEdge, WorkflowValidation
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

class ComponentType(Enum):
    """Component types"""
    USER_QUERY = "input"
    KNOWLEDGE_BASE = "knowledge"
    LLM_ENGINE = "llm"
    OUTPUT = "output"

@dataclass
class ExecutionContext:
    """Execution context for workflow processing"""
    input_data: Dict[str, Any]
    intermediate_results: Dict[str, Any]
    execution_log: List[Dict[str, Any]]
    start_time: float

class WorkflowExecutor:
    """Workflow execution engine"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.vector_service = VectorService()
        self.document_service = DocumentService()
    
    async def validate_workflow(self, nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> WorkflowValidation:
        """Validate workflow structure and configuration"""
        errors = []
        warnings = []
        execution_order = []
        
        try:
            # Check for required components
            node_types = {node.type for node in nodes}
            required_types = {ComponentType.USER_QUERY.value, ComponentType.LLM_ENGINE.value, ComponentType.OUTPUT.value}
            
            if not required_types.issubset(node_types):
                missing = required_types - node_types
                errors.append(f"Missing required components: {', '.join(missing)}")
            
            # Check for multiple input/output nodes
            input_nodes = [node for node in nodes if node.type == ComponentType.USER_QUERY.value]
            output_nodes = [node for node in nodes if node.type == ComponentType.OUTPUT.value]
            
            if len(input_nodes) > 1:
                errors.append("Only one User Query component is allowed")
            
            if len(output_nodes) > 1:
                errors.append("Only one Output component is allowed")
            
            # Validate connections and determine execution order
            if not errors:
                execution_order = self._determine_execution_order(nodes, edges)
                if not execution_order:
                    errors.append("Invalid workflow connections - cannot determine execution order")
            
            # Validate component configurations
            for node in nodes:
                config_errors = self._validate_node_config(node)
                errors.extend(config_errors)
            
            is_valid = len(errors) == 0
            
        except Exception as e:
            logger.error(f"Error validating workflow: {e}")
            errors.append(f"Validation error: {str(e)}")
            is_valid = False
        
        return WorkflowValidation(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            execution_order=execution_order
        )
    
    def _determine_execution_order(self, nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> List[str]:
        """Determine execution order - FIXED to handle multiple inputs to LLM Engine"""
        logger.info(f"=== DETERMINING EXECUTION ORDER ===")
        logger.info(f"Nodes: {len(nodes)}")
        logger.info(f"Edges: {len(edges)}")
        
        # Create adjacency list
        graph = {node.id: [] for node in nodes}
        for edge in edges:
            if edge.source in graph:
                graph[edge.source].append(edge.target)
                logger.info(f"Added edge: {edge.source} -> {edge.target}")
        
        logger.info(f"Graph structure: {graph}")
        
        # Find input node (no incoming edges)
        input_node = None
        for node in nodes:
            logger.info(f"Node: {node.id}, type: {node.type}")
            if node.type == ComponentType.USER_QUERY.value:
                input_node = node
                break
        
        if not input_node:
            logger.error("No input node found!")
            return []
        
        logger.info(f"Starting BFS from input node: {input_node.id}")
        
        # Use BFS to find ALL reachable nodes in correct order
        from collections import deque
        
        visited = set()
        order = []
        queue = deque([input_node.id])
        
        while queue:
            current_node = queue.popleft()
            
            if current_node in visited:
                logger.info(f"Node {current_node} already visited, skipping")
                continue
                
            visited.add(current_node)
            order.append(current_node)
            logger.info(f"Added node {current_node} to execution order. Current order: {order}")
            
            # Add all neighbors to queue
            for neighbor in graph.get(current_node, []):
                if neighbor not in visited:
                    logger.info(f"Adding neighbor {neighbor} of {current_node} to queue")
                    queue.append(neighbor)
        
        # FIXED: Add any remaining nodes that weren't reached (like LLM Engine with multiple inputs)
        for node in nodes:
            if node.id not in visited:
                logger.info(f"Adding unreached node {node.id} to execution order")
                order.append(node.id)
        
        logger.info(f"Final execution order: {order}")
        logger.info(f"=== END EXECUTION ORDER ===")
        return order
    
    def _validate_node_config(self, node: WorkflowNode) -> List[str]:
        """Validate individual node configuration"""
        errors = []
        
        if node.type == ComponentType.LLM_ENGINE.value:
            if not node.data.model:
                errors.append(f"LLM Engine node {node.id}: Model is required")
        
        elif node.type == ComponentType.KNOWLEDGE_BASE.value:
            if not node.data.collection:
                errors.append(f"Knowledge Base node {node.id}: Collection name is required")
            if node.data.topK is not None and (node.data.topK < 1 or node.data.topK > 50):
                errors.append(f"Knowledge Base node {node.id}: TopK must be between 1 and 50")
        
        return errors
    
    async def execute_workflow(
        self, 
        nodes: List[WorkflowNode], 
        edges: List[WorkflowEdge], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow with given input"""
        start_time = time.time()
        
        # Create execution context
        context = ExecutionContext(
            input_data=input_data,
            intermediate_results={},
            execution_log=[],
            start_time=start_time
        )
        
        try:
            logger.info(f"=== STARTING WORKFLOW EXECUTION ===")
            logger.info(f"Input data: {input_data}")
            logger.info(f"Nodes count: {len(nodes)}")
            logger.info(f"Edges count: {len(edges)}")
            
            # Validate workflow first
            validation = await self.validate_workflow(nodes, edges)
            logger.info(f"Validation result: is_valid={validation.is_valid}, errors={validation.errors}")
            
            if not validation.is_valid:
                raise ValueError(f"Invalid workflow: {', '.join(validation.errors)}")
            
            # Execute components in order
            execution_order = validation.execution_order
            node_map = {node.id: node for node in nodes}
            
            logger.info(f"=== WORKFLOW EXECUTION DEBUG ===")
            logger.info(f"Total nodes: {len(nodes)}")
            logger.info(f"Total edges: {len(edges)}")
            logger.info(f"Node types: {[node.type for node in nodes]}")
            logger.info(f"Node IDs: {[node.id for node in nodes]}")
            logger.info(f"Edges: {[(edge.source, edge.target) for edge in edges]}")
            logger.info(f"Workflow execution order: {execution_order}")
            logger.info(f"Available nodes: {list(node_map.keys())}")
            logger.info(f"=== END DEBUG ===")
            
            for node_id in execution_order:
                node = node_map[node_id]
                logger.info(f"Executing node: {node_id} (type: {node.type})")
                result = await self._execute_component(node, context)
                context.intermediate_results[node_id] = result
                
                # Log execution
                context.execution_log.append({
                    "node_id": node_id,
                    "node_type": node.type,
                    "result": result,
                    "timestamp": time.time() - start_time
                })
                logger.info(f"Completed node: {node_id}")
            
            # Calculate total execution time
            total_time = int((time.time() - start_time) * 1000)
            
            return {
                "output": context.intermediate_results,
                "execution_log": {
                    "steps": context.execution_log,
                    "total_steps": len(context.execution_log),
                    "execution_time": total_time
                },
                "execution_time": total_time,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "error": str(e),
                "execution_log": {
                    "steps": context.execution_log,
                    "total_steps": len(context.execution_log),
                    "error": str(e)
                },
                "execution_time": int((time.time() - start_time) * 1000),
                "status": "failed"
            }
    
    async def _execute_component(self, node: WorkflowNode, context: ExecutionContext) -> Any:
        """Execute individual component"""
        try:
            if node.type == ComponentType.USER_QUERY.value:
                return await self._execute_user_query(node, context)
            elif node.type == ComponentType.KNOWLEDGE_BASE.value:
                return await self._execute_knowledge_base(node, context)
            elif node.type == ComponentType.LLM_ENGINE.value:
                return await self._execute_llm_engine(node, context)
            elif node.type == ComponentType.OUTPUT.value:
                return await self._execute_output(node, context)
            else:
                raise ValueError(f"Unknown component type: {node.type}")
        
        except Exception as e:
            logger.error(f"Error executing component {node.id}: {e}")
            raise
    
    async def _execute_user_query(self, node: WorkflowNode, context: ExecutionContext) -> str:
        """Execute user query component"""
        query = context.input_data.get("query", "")
        if not query:
            raise ValueError("No query provided")
        
        return {
            "query": query,
            "type": "user_query"
        }
    
    async def _execute_knowledge_base(self, node: WorkflowNode, context: ExecutionContext) -> Dict[str, Any]:
        """Execute knowledge base component"""
        # Get query from previous component or input data
        query_data = None
        for result in context.intermediate_results.values():
            if isinstance(result, dict) and result.get("type") == "user_query":
                query_data = result
                break
        
        # If no query from previous component, try to get from input data
        if not query_data and context.input_data.get("query"):
            query_data = {
                "type": "user_query",
                "query": context.input_data["query"]
            }
        
        if not query_data:
            logger.warning("No query found for knowledge base search, skipping search")
            return {
                "type": "knowledge_base",
                "results": [],
                "query": None,
                "status": "skipped"
            }
        
        # Search vector database 
        threshold = 0.3  
        logger.info(f"Searching for query: '{query_data['query']}' in collection: '{node.data.collection or 'default'}' with threshold: {threshold}")
        search_results = await self.vector_service.search(
            query=query_data["query"],
            collection_name=node.data.collection or "default",
            top_k=node.data.topK or 5,
            threshold=threshold 
        )
        logger.info(f"Found {len(search_results)} search results")
        
        return {
            "query": query_data["query"],
            "results": search_results,
            "type": "knowledge_base"
        }
    
    async def _execute_llm_engine(self, node: WorkflowNode, context: ExecutionContext) -> Dict[str, Any]:
        """Execute LLM engine component"""
        # Get query and optional context
        query_data = None
        knowledge_data = None
        
        for result in context.intermediate_results.values():
            if isinstance(result, dict):
                if result.get("type") == "user_query":
                    query_data = result
                elif result.get("type") == "knowledge_base":
                    knowledge_data = result
        
        # If no query from previous component, try to get from input data
        if not query_data and context.input_data.get("query"):
            query_data = {
                "type": "user_query",
                "query": context.input_data["query"]
            }
        
        if not query_data:
            raise ValueError("No query found for LLM processing")
        
        # Prepare context for LLM
        context_text = ""
        if knowledge_data and knowledge_data.get("results"):
            context_text = "\n".join([
                f"Document: {doc.get('filename', 'Unknown')}\nContent: {doc.get('content', '')}"
                for doc in knowledge_data["results"]
            ])
        
        # Check if web search is enabled (from node configuration)
        use_web_search = getattr(node.data, 'use_web_search', False)
        
        # Generate response using LLM - always use GPT-5 nano
        model = "gpt-5-nano-2025-08-07"
        
        # Log model information
        logger.info(f"=== LLM ENGINE EXECUTION ===")
        logger.info(f"Model: {model} (forced to GPT-5 nano)")
        logger.info(f"Web search enabled: {use_web_search}")
        logger.info(f"Node data: {node.data}")
        
        response = await self.llm_service.generate_response(
            query=query_data["query"],
            context=context_text,
            model=model,
            max_tokens=node.data.maxTokens or 1000,
            use_web_search=use_web_search
        )
        
        logger.info(f"LLM response received: {response[:100]}...")
        logger.info(f"=== END LLM ENGINE EXECUTION ===")
        
        return {
            "query": query_data["query"],
            "response": response,
            "context_used": bool(context_text),
            "web_search_used": use_web_search,
            "type": "llm_response"
        }
    
    async def _execute_output(self, node: WorkflowNode, context: ExecutionContext) -> Dict[str, Any]:
        """Execute output component"""
        # Get LLM response
        llm_response = None
        for result in context.intermediate_results.values():
            if isinstance(result, dict) and result.get("type") == "llm_response":
                llm_response = result
                break
        
        if not llm_response:
            raise ValueError("No LLM response found for output")
        
        # Format output based on configuration
        output_format = node.data.format or "text"
        
        if output_format == "json":
            return {
                "response": llm_response["response"],
                "metadata": {
                    "query": llm_response["query"],
                    "context_used": llm_response["context_used"],
                    "format": "json"
                },
                "type": "output"
            }
        else:
            return {
                "response": llm_response["response"],
                "type": "output"
            }
