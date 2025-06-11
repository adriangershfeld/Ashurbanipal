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

# Configuration constants
STREAMING_WORDS_PER_CHUNK = 5
STREAMING_DELAY_SECONDS = 0.05
MAX_CHAT_HISTORY_ITEMS = 50
CHAT_RATE_LIMIT = 30
SEARCH_RATE_LIMIT = 50
RATE_LIMIT_WINDOW = 3600
MAX_VECTOR_STORE_SIZE = 1000000  # Maximum vectors in memory
MAX_RESPONSE_LENGTH = 10000  # Maximum response length for streaming

# Global components - will be initialized at startup
_vector_store = None
_embedding_model = None
_rag_pipeline = None
_initialization_lock = asyncio.Lock()

async def get_vector_store():
    """Get or create vector store singleton with async safety"""
    global _vector_store
    async with _initialization_lock:
        if _vector_store is None:
            try:
                _vector_store = VectorStore()
                # Check vector store size for memory management
                vector_count = getattr(_vector_store, 'vector_count', 0)
                if vector_count > MAX_VECTOR_STORE_SIZE:
                    logger.warning(f"Vector store size ({vector_count}) exceeds recommended limit ({MAX_VECTOR_STORE_SIZE})")
                logger.info(f"Vector store initialized successfully with {vector_count} vectors")
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {e}")
                raise HTTPException(status_code=503, detail="Vector store not available")
        return _vector_store

async def get_embedding_model():
    """Get or create embedding model singleton with async safety"""
    global _embedding_model
    async with _initialization_lock:
        if _embedding_model is None:
            try:
                _embedding_model = EmbeddingModel()
                logger.info("Embedding model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize embedding model: {e}")
                raise HTTPException(status_code=503, detail="Embedding model not available")
        return _embedding_model

async def get_rag_pipeline():
    """Get or create RAG pipeline singleton with async safety"""
    global _rag_pipeline
    async with _initialization_lock:
        if _rag_pipeline is None:
            try:
                from llm.rag_pipeline import RAGPipeline
                _rag_pipeline = RAGPipeline()
                logger.info("RAG pipeline initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RAG pipeline: {e}")
                raise HTTPException(status_code=503, detail="RAG pipeline not available")
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
            raise ValueError('Message cannot be empty or whitespace only')        # Sanitize the message for security
        sanitized = InputSanitizer.sanitize_string(v, max_length=2000)
        if not sanitized:
            raise ValueError('Message contains invalid characters')
        return sanitized
    
    @field_validator('history')
    @classmethod 
    def validate_history(cls, v):
        if len(v) > MAX_CHAT_HISTORY_ITEMS:
            # Keep only the most recent messages
            v = v[-MAX_CHAT_HISTORY_ITEMS:]
        
        # Validate each message in history
        for msg in v:
            if not isinstance(msg, dict):
                raise ValueError('History items must be dictionaries')
            if 'role' not in msg or 'content' not in msg:
                raise ValueError('History items must have "role" and "content" fields')
            if msg['role'] not in ['user', 'assistant']:
                raise ValueError('Message role must be "user" or "assistant"')
            # Limit individual message content length
            if len(str(msg.get('content', ''))) > 5000:
                raise ValueError('Individual history message too long (max 5000 characters)')
        
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
        
        # Get components with proper async handling
        vector_store = await get_vector_store()
        embedding_model = await get_embedding_model()
        
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
        
        # Get RAG pipeline with proper async handling
        rag = await get_rag_pipeline()
        
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
        rag = None
        
        try:
            logger.info(f"Streaming chat request from {client_ip}: '{request.message[:50]}...'")
            
            # Get RAG pipeline with proper async handling
            rag = await get_rag_pipeline()
            
            # Send initial status
            status_event = f"event: status\ndata: {json.dumps({'message': 'Processing your request...'})}\n\n"
            yield status_event
            
            # Process query through RAG pipeline with timeout protection
            try:
                rag_response = rag.query(
                    user_query=request.message,
                    chat_history=request.history,
                    use_context=request.use_rag
                )
            except Exception as rag_error:
                logger.error(f"RAG pipeline error for {client_ip}: {str(rag_error)}", exc_info=True)
                error_event = f"event: error\ndata: {json.dumps({'error': 'Failed to process request', 'code': 500})}\n\n"
                yield error_event
                return
            
            # Send sources first if available
            if hasattr(rag_response, 'sources') and rag_response.sources:
                try:
                    sources_data = {
                        "sources": [
                            {
                                "chunk_id": source.get('chunk_id', ''),
                                "content": (source.get('content', '')[:200] + "..." 
                                          if len(source.get('content', '')) > 200 
                                          else source.get('content', '')),
                                "source_file": source.get('source_file', 'Unknown'),
                                "similarity_score": float(source.get('similarity_score', 0.0))
                            } for source in rag_response.sources[:10]  # Limit sources to prevent overflow
                        ]
                    }
                    sources_event = f"event: sources\ndata: {json.dumps(sources_data)}\n\n"
                    yield sources_event
                except (ValueError, TypeError) as json_error:
                    logger.warning(f"Failed to serialize sources for {client_ip}: {str(json_error)}")
              # Stream response using sentence-based chunking for better readability
            response_text = getattr(rag_response, 'response', '')
            if response_text:
                # Truncate extremely long responses to prevent memory issues
                if len(response_text) > MAX_RESPONSE_LENGTH:
                    response_text = response_text[:MAX_RESPONSE_LENGTH] + "... [Response truncated]"
                    logger.warning(f"Response truncated for {client_ip} due to length: {len(response_text)}")
                
                try:
                    # Split by sentences for more natural streaming
                    import re
                    sentences = re.split(r'(?<=[.!?])\s+', response_text)
                    
                    for i, sentence in enumerate(sentences):
                        if sentence.strip():
                            # Check for cancellation periodically
                            if i % 5 == 0:
                                await asyncio.sleep(0)  # Allow cancellation check
                            
                            chunk_data = {"content": sentence.strip() + " "}
                            try:
                                chunk_event = f"event: chunk\ndata: {json.dumps(chunk_data)}\n\n"
                                yield chunk_event
                            except (ValueError, TypeError) as json_error:
                                logger.warning(f"Failed to serialize chunk for {client_ip}: {str(json_error)}")
                                continue
                            
                            # Small delay for better streaming effect
                            await asyncio.sleep(STREAMING_DELAY_SECONDS)
                except Exception as stream_error:
                    logger.error(f"Streaming error for {client_ip}: {str(stream_error)}")
                    error_event = f"event: error\ndata: {json.dumps({'error': 'Streaming interrupted', 'code': 500})}\n\n"
                    yield error_event
                    return
            
            # Send completion with metadata
            try:
                completion_data = {
                    "response_time_ms": float(getattr(rag_response, 'response_time_ms', (time.time() - start_time) * 1000)),
                    "total_length": len(response_text),
                    "source_count": len(getattr(rag_response, 'sources', []))
                }
                completion_event = f"event: complete\ndata: {json.dumps(completion_data)}\n\n"
                yield completion_event
                
                logger.info(f"Streaming chat completed in {completion_data['response_time_ms']:.2f}ms")
            except (ValueError, TypeError) as completion_error:
                logger.warning(f"Failed to send completion event for {client_ip}: {str(completion_error)}")
            
        except asyncio.CancelledError:
            logger.info(f"Streaming chat cancelled by client: {client_ip}")
            # Clean up resources if needed
            if rag:
                # Add any necessary cleanup for RAG pipeline
                pass
            raise
        except Exception as e:
            logger.error(f"Streaming chat error for {client_ip}: {str(e)}", exc_info=True)
            try:
                error_event = f"event: error\ndata: {json.dumps({'error': 'Internal server error during chat', 'code': 500})}\n\n"
                yield error_event
            except Exception:
                # If we can't even send an error event, just log and exit
                logger.error(f"Failed to send error event for {client_ip}")
        finally:
            # Ensure any resources are cleaned up
            logger.debug(f"Streaming session ended for {client_ip}")

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
        # Validate chunk_id format
        if not chunk_id or len(chunk_id) > 100:
            raise HTTPException(status_code=400, detail="Invalid chunk ID")
        
        # Sanitize chunk_id
        sanitized_chunk_id = InputSanitizer.sanitize_string(chunk_id, max_length=100)
        if not sanitized_chunk_id:
            raise HTTPException(status_code=400, detail="Invalid chunk ID format")
        
        # Get vector store
        vector_store = await get_vector_store()
        
        # Check if chunk exists
        chunk_data = vector_store.get_chunk_metadata(sanitized_chunk_id)
        if not chunk_data:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        # TODO: Implement similarity search by chunk ID
        logger.info(f"Similar chunks requested for: {sanitized_chunk_id}")
        return {
            "message": "Similar chunk search not implemented yet", 
            "chunk_id": sanitized_chunk_id,
            "status": "placeholder"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar chunks error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Similar chunks search failed")

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