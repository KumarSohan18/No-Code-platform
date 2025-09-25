"""
LLM service for OpenAI and Gemini integration
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import openai
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM operations"""
    
    def __init__(self):
        # Initialize OpenAI
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not provided")
        
        # Initialize Gemini
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            self.gemini_model = None
            logger.warning("Gemini API key not provided")
    
    async def generate_response(
        self,
        query: str,
        context: Optional[str] = None,
        model: str = "gpt-5-nano-2025-08-07",
        max_tokens: int = 1000,
        use_web_search: bool = False
    ) -> str:
        """Generate response using specified LLM"""
        try:
            # Perform web search if requested
            web_results = []
            if use_web_search:
                web_results = await self.web_search(query, num_results=10)
            
            # Prepare prompt with web search results
            prompt = self._build_prompt(query, context, web_results)
            
            # Log the full prompt for debugging
            logger.info(f"=== FULL PROMPT SENT TO LLM ===")
            logger.info(f"Prompt: {prompt}")
            logger.info(f"=== END PROMPT ===")
            
            # Use GPT-5 nano for all requests
            if self.openai_client:
                return await self._generate_openai_response(
                    prompt, "gpt-5-nano-2025-08-07", max_tokens
                )
            else:
                raise ValueError("OpenAI client not initialized")
        
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise
    
    def _build_prompt(self, query: str, context: Optional[str] = None, web_results: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build prompt for LLM"""
        prompt_parts = []
        
        # Add system instruction
        if web_results:
            prompt_parts.append("You are a helpful AI assistant. Use the provided web search results to answer the user's query accurately and comprehensively. Format your response with proper line breaks, bullet points, and clear structure. If the web search results contain relevant information, use them to provide a detailed response. If the results don't contain enough information, let the user know what you found and suggest they try a different search.")
        else:
            prompt_parts.append("You are a helpful AI assistant. Provide accurate, helpful, and concise responses with proper formatting including line breaks and clear structure.")
        
        # Add context if available
        if context:
            prompt_parts.append(f"Context from knowledge base:\n{context}")
        
        # Add web search results if available
        if web_results:
            web_context = "IMPORTANT: Use the following web search results to answer the user's query. These results contain current, real-time information that should be used to provide an accurate and up-to-date response:\n\n"
            for i, result in enumerate(web_results, 1):
                web_context += f"Result {i}:\nTitle: {result['title']}\nContent: {result['snippet']}\nSource: {result['url']}\n\n"
            prompt_parts.append(web_context)
        
        # Add user query with formatting instructions
        if "news" in query.lower():
            prompt_parts.append(f"User query: {query}\n\nPlease format your response with:\n- Clear headlines\n- Bullet points for each news item\n- Proper line breaks between sections\n- Source attribution when using web search results")
        else:
            prompt_parts.append(f"User query: {query}")
        
        return "\n\n".join(prompt_parts)
    
    async def _generate_openai_response(
        self, 
        prompt: str, 
        model: str, 
        max_tokens: int
    ) -> str:
        """Generate response using OpenAI"""
        try:
            # For newer models that require max_completion_tokens, try both approaches
            if model.startswith("gpt-5") or model.startswith("gpt-4o"):
                try:
                    # First try with max_completion_tokens (newer API)
                    response = await self.openai_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        max_completion_tokens=max_tokens
                    )
                except TypeError:
                    # If max_completion_tokens is not supported, try without any token limit
                    logger.warning(f"max_completion_tokens not supported for {model}, trying without token limit")
                    response = await self.openai_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant."},
                            {"role": "user", "content": prompt}
                        ]
                    )
            else:
                # Use max_tokens for older models
                response = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens
                )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_gemini_response(
        self, 
        prompt: str, 
        max_tokens: int
    ) -> str:
        """Generate response using Gemini"""
        try:
            logger.info("Generating Gemini response")
            
            # Only configure max_output_tokens
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens
            )
            
            # Generate response
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            logger.info("Gemini response generated successfully")
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def generate_embeddings(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Generate embeddings for text"""
        try:
            if not self.openai_client:
                raise ValueError("OpenAI client not initialized")
            
            response = await self.openai_client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def web_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Perform web search using SerpAPI"""
        try:
            if not settings.SERPAPI_API_KEY:
                logger.warning("SerpAPI key not configured, skipping web search")
                return []
            
            import httpx
            
            # Optimize query for better search results
            optimized_query = query
            if "news" in query.lower() and "hindu" in query.lower():
                optimized_query = f"site:thehindu.com {query}"
            elif "news" in query.lower():
                optimized_query = f"{query} latest today"
            
            logger.info(f"Original query: {query}")
            logger.info(f"Optimized query: {optimized_query}")
            
            # SerpAPI endpoint
            url = "https://serpapi.com/search"
            params = {
                "q": optimized_query,
                "api_key": settings.SERPAPI_API_KEY,
                "num": num_results,
                "engine": "google"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # Extract search results
            results = []
            if "organic_results" in data:
                for result in data["organic_results"][:num_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("link", ""),
                        "rank": result.get("position", 0)
                    })
            
            logger.info(f"Found {len(results)} web search results for query: {query}")
            logger.info(f"Web search results: {results}")
            return results
        
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            return []
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-5-nano-2025-08-07",
        max_tokens: int = 1000
    ) -> str:
        """Chat completion for conversation"""
        try:
            if not self.openai_client:
                raise ValueError("OpenAI client not initialized")
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",
                messages=messages,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
