"""
Main FastAPI application for the Local AI Research Assistant
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import logging
from pathlib import Path

# Import logging configuration first
from utils.logging_config import setup_logging, get_logger
from utils.middleware import SecurityMiddleware, RequestLoggingMiddleware
from utils.caching import clear_all_caches, get_cache_stats

# Set up logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "logs/ashurbanipal.log")
)

logger = get_logger(__name__)

from api.query import router as query_router
from api.ingest import router as ingest_router
from api.files import router as files_router

app = FastAPI(
    title="Local AI Research Assistant",
    description="Local-first AI assistant for document search and RAG",
    version="0.1.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Add security middleware
app.add_middleware(
    SecurityMiddleware,
    enable_rate_limiting=True,
    max_requests_per_hour=1000,
    max_requests_per_minute=60
)

# Add request logging middleware in development
if os.getenv("ENVIRONMENT") != "production":
    app.add_middleware(
        RequestLoggingMiddleware,
        log_body=False,  # Don't log request bodies for privacy
        max_body_size=1024
    )

# Configure CORS based on environment
allowed_origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative dev port
]

# In production, you might want to be more restrictive
if os.getenv("ENVIRONMENT") == "production":
    allowed_origins = ["http://localhost:5173"]  # Only allow specific origins

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods only
    allow_headers=["Content-Type", "Authorization"],  # Specific headers only
)

# Include API routers with proper error handling
try:
    app.include_router(query_router, prefix="/api", tags=["query"])
    app.include_router(ingest_router, prefix="/api", tags=["ingest"])
    app.include_router(files_router, prefix="/api", tags=["files"])
    logger.info("API routers configured successfully")
except Exception as e:
    logger.error(f"Failed to configure API routers: {str(e)}")
    raise

# Serve static files from frontend build
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
    logger.info("Frontend static files mounted")

@app.get("/health")
async def health_check():
    """Health check endpoint with system information"""
    try:
        from utils.resource_manager import _db_pools
        cache_stats = get_cache_stats()
        
        return {
            "status": "healthy", 
            "message": "Local AI Research Assistant is running",
            "cache_stats": cache_stats,
            "db_pools": len(_db_pools),
            "version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "degraded",
            "message": "Some components may be unavailable",
            "version": "0.1.0"
        }

@app.get("/cache/stats")
async def get_cache_statistics():
    """Get detailed cache statistics (development only)"""
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    return get_cache_stats()

@app.post("/cache/clear")
async def clear_caches():
    """Clear all caches (development only)"""
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        clear_all_caches()
        return {"message": "All caches cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing caches: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear caches")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Starting Ashurbanipal backend...")
    
    # Initialize async components
    try:
        from embeddings.async_store import get_async_vector_store
        vector_store = await get_async_vector_store()
        logger.info("Async vector store initialized")
    except Exception as e:
        logger.error(f"Failed to initialize async vector store: {str(e)}")
    
    logger.info("Ashurbanipal backend started successfully")
    
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down Ashurbanipal backend...")
    
    # Clean up async components
    try:
        from embeddings.async_store import close_async_vector_store
        await close_async_vector_store()
        logger.info("Async vector store closed")
    except Exception as e:
        logger.error(f"Error closing async vector store: {str(e)}")
    
    # Clean up database pools and other resources
    try:
        from utils.resource_manager import cleanup_all_pools
        cleanup_all_pools()
        logger.info("Database pools cleaned up")
    except Exception as e:
        logger.error(f"Error during resource cleanup: {str(e)}")
    
    # Clear caches
    try:
        clear_all_caches()
        logger.info("Caches cleared")
    except Exception as e:
        logger.error(f"Error clearing caches: {str(e)}")
    
    logger.info("Ashurbanipal backend shutdown complete")

if __name__ == "__main__":
    # Development server configuration
    logger.info("Starting development server...")
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
