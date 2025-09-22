"""
Document service for file processing and text extraction
"""

import os
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import PyPDF2
import fitz  # PyMuPDF
import docx
from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for document processing"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.vector_service = VectorService()
        self.upload_dir = Path(settings.UPLOAD_DIRECTORY)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def process_document(
        self, 
        file_path: str, 
        filename: str, 
        collection_name: str = "default"
    ) -> Dict[str, Any]:
        """Process uploaded document"""
        try:
            # Extract text content
            content = await self._extract_text(file_path)
            if not content:
                raise ValueError("Could not extract text from document")
            
            # Create document chunks
            chunks = await self._create_chunks(content, filename)
            
            # Generate embeddings and store in vector database
            await self._store_embeddings(chunks, collection_name, filename)
            
            return {
                "status": "success",
                "chunks_created": len(chunks),
                "embeddings_generated": len(chunks),
                "content_length": len(content)
            }
        
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from document based on file type"""
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.pdf':
                return await self._extract_pdf_text(file_path)
            elif file_extension == '.txt':
                return await self._extract_txt_text(file_path)
            elif file_extension == '.docx':
                return await self._extract_docx_text(file_path)
            elif file_extension == '.md':
                return await self._extract_md_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file using PyMuPDF for better accuracy"""
        try:
            # Try PyMuPDF first (better text extraction)
            try:
                doc = fitz.open(file_path)
                text = ""
                
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    text += page.get_text() + "\n"
                
                doc.close()
                return text.strip()
            
            except Exception as e:
                logger.warning(f"PyMuPDF failed, falling back to PyPDF2: {e}")
                
                # Fallback to PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text += page.extract_text() + "\n"
                    
                    return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise
    
    async def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        
        except Exception as e:
            logger.error(f"Error extracting TXT text: {e}")
            raise
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise
    
    async def _extract_md_text(self, file_path: str) -> str:
        """Extract text from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        
        except Exception as e:
            logger.error(f"Error extracting Markdown text: {e}")
            raise
    
    async def _create_chunks(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Create text chunks for embedding"""
        # Simple chunking strategy - split by paragraphs and sentences
        chunks = []
        chunk_size = 1000  # characters
        overlap = 200  # characters
        
        # Split content into sentences
        sentences = self._split_into_sentences(content)
        
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, save current chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append({
                    "id": f"{filename}_{chunk_id}",
                    "content": current_chunk.strip(),
                    "metadata": {
                        "filename": filename,
                        "chunk_id": chunk_id,
                        "chunk_size": len(current_chunk)
                    }
                })
                
                # Start new chunk with overlap
                current_chunk = current_chunk[-overlap:] + " " + sentence
                chunk_id += 1
            else:
                current_chunk += " " + sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "id": f"{filename}_{chunk_id}",
                "content": current_chunk.strip(),
                "metadata": {
                    "filename": filename,
                    "chunk_id": chunk_id,
                    "chunk_size": len(current_chunk)
                }
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _store_embeddings(
        self, 
        chunks: List[Dict[str, Any]], 
        collection_name: str, 
        filename: str
    ) -> bool:
        """Generate embeddings and store in vector database"""
        try:
            # Ensure collection exists
            await self.vector_service.create_collection(collection_name)
            
            # Prepare documents and metadata
            documents = [chunk["content"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            ids = [chunk["id"] for chunk in chunks]
            
            # Store in vector database
            success = await self.vector_service.add_documents(
                collection_name=collection_name,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            if success:
                logger.info(f"Stored {len(chunks)} chunks for {filename} in collection {collection_name}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error storing embeddings for {filename}: {e}")
            return False
    
    async def search_documents(
        self, 
        query: str, 
        collection_name: str = "default", 
        top_k: int = 5, 
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search documents using vector similarity"""
        try:
            results = await self.vector_service.search(
                query=query,
                collection_name=collection_name,
                top_k=top_k,
                threshold=threshold
            )
            
            # Format results for API response
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "document_id": result["id"],
                    "filename": result["metadata"].get("filename", "unknown"),
                    "content": result["content"],
                    "similarity_score": result["similarity_score"],
                    "metadata": result["metadata"]
                })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def get_document_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about documents in collection"""
        try:
            collection_info = await self.vector_service.get_collection_info(collection_name)
            return collection_info
        
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return {}
    
    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from collection"""
        try:
            success = await self.vector_service.delete_documents(
                collection_name=collection_name,
                ids=[document_id]
            )
            
            if success:
                logger.info(f"Deleted document {document_id} from collection {collection_name}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""
    
    def validate_file_type(self, filename: str) -> bool:
        """Validate file type"""
        file_extension = Path(filename).suffix.lower()
        return file_extension in settings.ALLOWED_FILE_TYPES
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size"""
        return file_size <= settings.MAX_FILE_SIZE
