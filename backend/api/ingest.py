"""
Ingestion API for adding documents to the corpus
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated
import logging
import os
import time
from pathlib import Path

from utils.file_loader import FileLoader
from utils.pdf_extractor import PDFExtractor
from utils.sanitization import InputSanitizer
from embeddings.chunker import TextChunker
from embeddings.embedder import EmbeddingModel
from embeddings.store import VectorStore

router = APIRouter()
logger = logging.getLogger(__name__)

class IngestRequest(BaseModel):
    folder_path: str = Field(..., min_length=1, max_length=500, description="Path to folder to ingest")
    file_types: List[str] = Field(default=[".pdf", ".txt", ".md", ".docx"], description="Allowed file extensions")
    recursive: bool = Field(default=True, description="Whether to scan subdirectories")
    
    class Config:
        json_schema_extra = {
            "example": {
                "folder_path": "/path/to/documents",
                "file_types": [".pdf", ".txt", ".md"],
                "recursive": True
            }
        }

class IngestResponse(BaseModel):
    status: str
    files_processed: int
    chunks_created: int
    processing_time_ms: float

@router.post("/ingest/folder", response_model=IngestResponse)
async def ingest_folder(request: IngestRequest):
    """Ingest all documents from a specified folder"""
    try:
        start_time = time.time()
        
        # Validate and sanitize folder path
        folder_path = request.folder_path.strip()
        if not folder_path or not InputSanitizer.sanitize_path(folder_path):
            raise HTTPException(status_code=400, detail="Invalid folder path")
            
        path = Path(folder_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Folder not found")
        if not path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
            
        # Validate file types
        valid_extensions = [ext for ext in request.file_types if InputSanitizer.sanitize_filename(f"test{ext}")]
        if not valid_extensions:
            raise HTTPException(status_code=400, detail="No valid file types provided")
            
        logger.info(f"Starting folder ingestion: {folder_path}")
        logger.info(f"File types: {valid_extensions}, Recursive: {request.recursive}")
        
        # TODO: Implement actual folder ingestion
        # 1. Scan folder for files
        # 2. Extract text from each file
        # 3. Chunk the text
        # 4. Generate embeddings
        # 5. Store in vector database
        
        processing_time = (time.time() - start_time) * 1000
        
        return IngestResponse(
            status="completed",
            files_processed=0,
            chunks_created=0,
            processing_time_ms=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Folder ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Folder ingestion failed")

@router.post("/ingest/file")
async def ingest_single_file(file: UploadFile = File(...)):
    """Ingest a single uploaded file"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        if not InputSanitizer.sanitize_filename(file.filename):
            raise HTTPException(status_code=400, detail="Invalid filename")
            
        # Check file size (limit to 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
            
        logger.info(f"Ingesting uploaded file: {file.filename}")
        
        # TODO: Implement single file ingestion
        # 1. Save uploaded file temporarily
        # 2. Extract text based on file type
        # 3. Chunk and embed
        # 4. Store in database
        # 5. Clean up temporary file
        
        return {
            "status": "completed", 
            "filename": file.filename,
            "size": file.size,
            "message": "File ingestion not fully implemented yet"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail="File ingestion failed")

@router.post("/ingest/url")
async def ingest_from_url(url: str = Form(...)):
    """Ingest content from a URL"""
    try:
        # Validate URL
        if not url or not InputSanitizer.sanitize_url(url):
            raise HTTPException(status_code=400, detail="Invalid URL")
            
        logger.info(f"Ingesting content from URL: {url}")
        
        # TODO: Implement URL content ingestion
        # 1. Fetch content from URL
        # 2. Extract text (handle HTML, PDF, etc.)
        # 3. Chunk and embed
        # 4. Store with URL as source
        
        return {
            "status": "completed", 
            "url": url,
            "message": "URL ingestion not fully implemented yet"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail="URL ingestion failed")

@router.get("/ingest/status")
async def get_ingestion_status():
    """Get current ingestion status and corpus statistics"""
    try:
        logger.info("Getting ingestion status")
        
        # TODO: Implement status checking from database
        return {
            "corpus_size": 0,
            "total_documents": 0,
            "total_chunks": 0,
            "last_updated": None,
            "ingestion_in_progress": False,
            "message": "Status checking not fully implemented yet"
        }
    
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get ingestion status")

@router.delete("/ingest/clear")
async def clear_corpus():
    """Clear the entire document corpus"""
    try:
        logger.warning("Clearing entire corpus - this action is irreversible")
        
        # TODO: Implement corpus clearing
        # 1. Clear vector store
        # 2. Clear database
        # 3. Remove cached files
        
        return {
            "status": "cleared",
            "message": "Corpus clearing not fully implemented yet"
        }
        
    except Exception as e:
        logger.error(f"Corpus clearing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear corpus")
