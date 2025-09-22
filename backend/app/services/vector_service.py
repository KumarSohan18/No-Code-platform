"""
Vector service for ChromaDB integration
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorService:
    """Service for vector database operations"""
    
    def __init__(self):
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Initialize OpenAI embedding function
            if settings.OPENAI_API_KEY:
                self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=settings.OPENAI_API_KEY,
                    model_name=settings.OPENAI_EMBEDDING_MODEL
                )
                logger.info(f"OpenAI embedding function initialized with model: {settings.OPENAI_EMBEDDING_MODEL}")
            else:
                self.embedding_function = None
                logger.warning("OpenAI API key not provided, using default embedding function")
            
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            self.client = None
            self.embedding_function = None
    
    async def create_collection(self, collection_name: str) -> bool:
        """Create a new collection"""
        try:
            if not self.client:
                raise ValueError("ChromaDB client not initialized")
            
            # Check if collection already exists
            try:
                self.client.get_collection(collection_name)
                logger.info(f"Collection {collection_name} already exists")
                return True
            except:
                pass
            
            # Create new collection with OpenAI embedding function
            self.client.create_collection(
                name=collection_name,
                metadata={"description": f"Collection for {collection_name}"},
                embedding_function=self.embedding_function
            )
            logger.info(f"Collection {collection_name} created successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            return False
    
    async def add_documents(
        self, 
        collection_name: str, 
        documents: List[str], 
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """Add documents to collection"""
        try:
            if not self.client:
                raise ValueError("ChromaDB client not initialized")
            
            # Get or create collection
            try:
                collection = self.client.get_collection(collection_name, embedding_function=self.embedding_function)
            except:
                await self.create_collection(collection_name)
                collection = self.client.get_collection(collection_name, embedding_function=self.embedding_function)
            
            # Generate IDs if not provided
            if not ids:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Add documents
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding documents to collection {collection_name}: {e}")
            return False
    
    async def search(
        self,
        query: str,
        collection_name: str = "default",
        top_k: int = 5,
        threshold: float = 0.7,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search documents in collection"""
        try:
            if not self.client:
                raise ValueError("ChromaDB client not initialized")
            
            # Get collection
            try:
                collection = self.client.get_collection(collection_name, embedding_function=self.embedding_function)
            except:
                logger.warning(f"Collection {collection_name} not found")
                return []
            
            # Perform search
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where
            )
            
            logger.info(f"Raw search results: {len(results.get('documents', [[]])[0]) if results.get('documents') else 0} documents found")
            if results.get('distances'):
                logger.info(f"Distance scores: {results['distances'][0]}")
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    logger.info(f"Document {i}: similarity={similarity:.3f}, threshold={threshold}, passed={similarity >= threshold}")
                    
                    if similarity >= threshold:
                        formatted_results.append({
                            'id': results['ids'][0][i],
                            'content': doc,
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                            'similarity_score': similarity,
                            'distance': distance
                        })
            
            logger.info(f"Found {len(formatted_results)} results for query in collection {collection_name}")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {e}")
            return []
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information"""
        try:
            if not self.client:
                raise ValueError("ChromaDB client not initialized")
            
            collection = self.client.get_collection(collection_name)
            count = collection.count()
            
            return {
                'name': collection_name,
                'document_count': count,
                'metadata': collection.metadata
            }
        
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            return {}
    
    async def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            if not self.client:
                raise ValueError("ChromaDB client not initialized")
            
            collections = self.client.list_collections()
            return [col.name for col in collections]
        
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            if not self.client:
                raise ValueError("ChromaDB client not initialized")
            
            self.client.delete_collection(collection_name)
            logger.info(f"Collection {collection_name} deleted successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
    
    async def delete_documents(self, collection_name: str, ids: List[str]) -> bool:
        """Delete specific documents from collection"""
        try:
            if not self.client:
                raise ValueError("ChromaDB client not initialized")
            
            collection = self.client.get_collection(collection_name)
            collection.delete(ids=ids)
            
            logger.info(f"Deleted {len(ids)} documents from collection {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting documents from collection {collection_name}: {e}")
            return False
    
    async def update_document(
        self, 
        collection_name: str, 
        document_id: str, 
        document: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Update a document in collection"""
        try:
            if not self.client:
                raise ValueError("ChromaDB client not initialized")
            
            collection = self.client.get_collection(collection_name)
            collection.update(
                ids=[document_id],
                documents=[document],
                metadatas=[metadata]
            )
            
            logger.info(f"Updated document {document_id} in collection {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating document {document_id} in collection {collection_name}: {e}")
            return False
