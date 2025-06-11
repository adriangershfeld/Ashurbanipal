"""
Query API for semantic search and RAG functionality
"""
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import logging
import time
import json
import asyncio
import threading
from contextlib import asynccontextmanager

from embeddings.store import VectorStore
from embeddings.embedder import EmbeddingModel
from utils.sanitization import InputSanitizer, check_rate_limit
from utils.resource_manager import ResourceManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize components with proper error handling
try:
    vector_store = VectorStore()
    embedding_model = EmbeddingModel()
    logger.info("Query API components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize query API components: {e}")
    vector_store = None
    embedding_model = None

# Initialize RAG pipeline as singleton with thread safety
_rag_pipeline = None
_rag_pipeline_lock = threading.RLock()

# Configuration constants
STREAMING_WORDS_PER_CHUNK = 5
STREAMING_DELAY_SECONDS = 0.05
MAX_CHAT_HISTORY_ITEMS = 50
CHAT_RATE_LIMIT = 30
SEARCH_RATE_LIMIT = 50
RATE_LIMIT_WINDOW = 3600

def get_rag_pipeline():
    """Get or create RAG pipeline singleton with thread safety"""
    global _rag_pipeline
    with _rag_pipeline_lock:
        if _rag_pipeline is None:
            try:
                from llm.rag_pipeline import RAGPipeline
                _rag_pipeline = RAGPipeline()
                logger.info("RAG pipeline initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RAG pipeline: {e}")
                _rag_pipeline = None
        return _rag_pipeline

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    
    @field_validator('query')
    @classmethod
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        # Sanitize the query for security
        sanitized = InputSanitizer.sanitize_query(v)
        if not sanitized:
            raise ValueError('Query contains invalid characters')
        return sanitized

class SearchResult(BaseModel):
    content: str
    source_file: str
    chunk_id: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    metadata: dict

class QueryResponse(BaseModel):
    results: List[SearchResult]
    total_results: int = Field(..., ge=0)
    query_time_ms: float = Field(..., ge=0.0)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Chat message")
    history: List[dict] = Field(default_factory=list, description="Chat history (max 50 items)")
    use_rag: bool = Field(default=True, description="Whether to use RAG for response")
    
    @field_validator('message')
    @classmethod
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        # Sanitize the message for security
        sanitized = InputSanitizer.sanitize_string(v, max_length=2000)
        if not sanitized:
            raise ValueError('Message contains invalid characters')
        return sanitized
    
    @field_validator('history')
    @classmethod 
    def validate_history(cls, v):
        if len(v) > 50:
            # Keep only the most recent 50 messages
            v = v[-50:]
        
        # Validate each message in history
        for msg in v:
            if not isinstance(msg, dict):
                raise ValueError('History items must be dictionaries')
            if 'role' not in msg or 'content' not in msg:
                raise ValueError('History items must have "role" and "content" fields')
            if msg['role'] not in ['user', 'assistant']:
                raise ValueError('Message role must be "user" or "assistant"')
        
        return v

class ChatResponse(BaseModel):
    response: str
    sources: List[SearchResult] = Field(default_factory=list)
    response_time_ms: float = Field(..., ge=0.0)

@router.post("/search", response_model=QueryResponse)
async def semantic_search(request: QueryRequest, http_request: Request):
    """Perform semantic search across the document corpus"""
    start_time = time.time()
    # Rate limiting
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not check_rate_limit(client_ip, max_requests=SEARCH_RATE_LIMIT, window_seconds=RATE_LIMIT_WINDOW):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    try:
        logger.info(f"Search request from {client_ip}: '{request.query}' (limit: {request.limit}, threshold: {request.similarity_threshold})")
        
        # Check if components are available
        if not vector_store or not embedding_model:
            logger.error("Vector store or embedding model not initialized")
            raise HTTPException(status_code=503, detail="Search service not available")
        
        # Generate embedding for the query
        query_embedding = embedding_model.embed_query(request.query)
        
        # Perform similarity search
        search_results = vector_store.search(
            query_embedding=query_embedding,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # Convert to response format
        results = []
        for chunk_id, similarity_score in search_results:
            # Get chunk details from database
            chunk_data = vector_store.get_chunk_metadata(chunk_id)
            if chunk_data:
                results.append(SearchResult(
                    content=chunk_data.get('content', ''),
                    source_file=chunk_data.get('source_file', ''),
                    chunk_id=chunk_id,
                    similarity_score=similarity_score,
                    metadata=chunk_data.get('metadata', {})
                ))
        
        query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        response = QueryResponse(
            results=results,
            total_results=len(results),
            query_time_ms=query_time
        )
        
        logger.info(f"Search completed in {query_time:.2f}ms, returned {len(results)} results")
        return response
    
    except ValueError as e:
        logger.warning(f"Invalid search request from {client_ip}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Search error for {client_ip}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during search")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_rag(request: ChatRequest, http_request: Request):
    """Chat with RAG-enhanced responses"""
    start_time = time.time()
    # Rate limiting
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not check_rate_limit(f"chat_{client_ip}", max_requests=CHAT_RATE_LIMIT, window_seconds=RATE_LIMIT_WINDOW):
        logger.warning(f"Chat rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    try:
        logger.info(f"Chat request from {client_ip}: '{request.message[:50]}...' (use_rag: {request.use_rag})")
        
        # Get RAG pipeline singleton
        rag = get_rag_pipeline()
        if not rag:
            logger.error("RAG pipeline not available")
            raise HTTPException(status_code=503, detail="Chat service not available")
        
        # Process query through RAG pipeline with error handling
        try:
            rag_response = rag.query(
                user_query=request.message,
                chat_history=request.history,
                use_context=request.use_rag
            )
        except Exception as rag_error:
            logger.error(f"RAG pipeline error: {str(rag_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to process chat request")
        
        # Convert sources to the expected format with validation
        response_sources = []
        sources = getattr(rag_response, 'sources', [])
        for source in sources:
            if isinstance(source, dict):
                response_sources.append(SearchResult(
                    content=source.get('content', ''),
                    source_file=source.get('source_file', ''),
                    chunk_id=source.get('chunk_id', ''),
                    similarity_score=source.get('similarity_score', 0.0),
                    metadata=source.get('metadata', {})
                ))
        
        response = ChatResponse(
            response=getattr(rag_response, 'response', ''),
            sources=response_sources,
            response_time_ms=getattr(rag_response, 'response_time_ms', (time.time() - start_time) * 1000)
        )
        
        logger.info(f"Chat completed in {getattr(rag_response, 'response_time_ms', (time.time() - start_time) * 1000):.2f}ms with {len(response_sources)} sources")
        return response
    
    except ValueError as e:
        logger.warning(f"Invalid chat request from {client_ip}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Chat error for {client_ip}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during chat")

@router.post("/chat/stream")
async def chat_with_rag_stream(request: ChatRequest, http_request: Request):
    """Stream chat with RAG-enhanced responses using Server-Sent Events"""
    client_ip = http_request.client.host if http_request.client else "unknown"
    
    # Rate limiting
    if not check_rate_limit(f"chat_stream_{client_ip}", max_requests=CHAT_RATE_LIMIT, window_seconds=RATE_LIMIT_WINDOW):
        logger.warning(f"Streaming chat rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    async def generate_sse_stream():
        """Generate Server-Sent Events stream with proper error handling"""
        start_time = time.time()
        
        try:
            logger.info(f"Streaming chat request from {client_ip}: '{request.message[:50]}...'")
            
            # Get RAG pipeline singleton
            rag = get_rag_pipeline()
            if not rag:
                error_event = f"event: error\ndata: {json.dumps({'error': 'Chat service not available', 'code': 503})}\n\n"
                yield error_event
                return
            
            # Send initial status
            status_event = f"event: status\ndata: {json.dumps({'message': 'Processing your request...'})}\n\n"
            yield status_event
            
            # Process query through RAG pipeline
            rag_response = rag.query(
                user_query=request.message,
                chat_history=request.history,
                use_context=request.use_rag
            )
            
            # Send sources first if available
            if hasattr(rag_response, 'sources') and rag_response.sources:
                sources_data = {
                    "sources": [
                        {
                            "chunk_id": source.get('chunk_id', ''),
                            "content": source.get('content', '')[:200] + "..." if len(source.get('content', '')) > 200 else source.get('content', ''),
                            "source_file": source.get('source_file', 'Unknown'),
                            "similarity_score": source.get('similarity_score', 0.0)
                        } for source in rag_response.sources
                    ]
                }
                sources_event = f"event: sources\ndata: {json.dumps(sources_data)}\n\n"
                yield sources_event
            
            # Stream response using sentence-based chunking for better readability
            response_text = getattr(rag_response, 'response', '')
            if response_text:
                # Split by sentences for more natural streaming
                import re
                sentences = re.split(r'(?<=[.!?])\s+', response_text)
                
                for sentence in sentences:
                    if sentence.strip():
                        chunk_data = {"content": sentence.strip() + " "}
                        chunk_event = f"event: chunk\ndata: {json.dumps(chunk_data)}\n\n"
                        yield chunk_event
                        
                        # Small delay for better streaming effect
                        await asyncio.sleep(STREAMING_DELAY_SECONDS)
            
            # Send completion with metadata
            completion_data = {
                "response_time_ms": getattr(rag_response, 'response_time_ms', (time.time() - start_time) * 1000),
                "total_length": len(response_text),
                "source_count": len(getattr(rag_response, 'sources', []))
            }
            completion_event = f"event: complete\ndata: {json.dumps(completion_data)}\n\n"
            yield completion_event
            
            logger.info(f"Streaming chat completed in {completion_data['response_time_ms']:.2f}ms")
            
        except asyncio.CancelledError:
            logger.info(f"Streaming chat cancelled by client: {client_ip}")
            # Don't yield anything for cancelled requests
            raise
        except Exception as e:
            logger.error(f"Streaming chat error for {client_ip}: {str(e)}", exc_info=True)
            error_event = f"event: error\ndata: {json.dumps({'error': 'Internal server error during chat', 'code': 500})}\n\n"
            yield error_event
    
    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@router.get("/similar/{chunk_id}")
async def find_similar_chunks(chunk_id: str, limit: int = Query(5, ge=1, le=20)):
    """Find chunks similar to a given chunk"""
    try:
        # TODO: Implement similarity search by chunk ID
        return {"message": "Similar chunk search not implemented yet", "chunk_id": chunk_id}
    
    except Exception as e:
        logger.error(f"Similar chunks error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Similar chunks search failed: {str(e)}")

@router.get("/query/history")
async def get_query_history(limit: int = Query(20, ge=1, le=100)):
    """
    Get recent search queries
    """
    try:
        # TODO: Implement query history
        return {"queries": [], "total": 0}
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

class RAGRequest(BaseModel):
    query: str
    history: List[dict] = []
    use_context: bool = True

@router.post("/rag")
async def rag_query(request: RAGRequest):
    """
    RAG query with chat context (Stage 3 feature)
    """
    try:
        # TODO: Implement RAG with local LLM
        logger.info(f"RAG query: {request.query}")
        
        return {
            "response": f"This is a placeholder RAG response for: {request.query}",
            "sources": [],
            "context_used": request.use_context
        }
        
    except Exception as e:
        logger.error(f"RAG error: {str(e)}")
        raise HTTPException(status_code=500, detail="RAG query failed")
