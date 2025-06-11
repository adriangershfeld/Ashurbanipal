"""
Files API for opening and managing source documents
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import os
import sys
import subprocess
from pathlib import Path

from utils.sanitization import InputSanitizer

router = APIRouter()
logger = logging.getLogger(__name__)

class FileInfo(BaseModel):
    filename: str
    filepath: str
    size: int
    modified_date: str
    file_type: str
    chunks_count: int

class FilesResponse(BaseModel):
    files: List[FileInfo]
    total_files: int

@router.get("/files", response_model=FilesResponse)
async def list_files(limit: int = 50, offset: int = 0):
    """List all files in the corpus"""
    try:
        # Validate parameters
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        logger.info(f"Listing files (limit: {limit}, offset: {offset})")
        
        # Import vector store
        from embeddings.store import VectorStore
        
        # Initialize vector store
        store = VectorStore()
        files_data = store.get_files_list(offset=offset, limit=limit)
        
        # Convert to response format
        files = []
        for file_info in files_data.get('files', []):
            files.append(FileInfo(
                filename=file_info.get('filename', ''),
                filepath=file_info.get('filepath', ''),
                size=file_info.get('size', 0),
                modified_date=file_info.get('modified_date', ''),
                file_type=file_info.get('file_type', ''),
                chunks_count=file_info.get('chunks_count', 0)
            ))
        
        return FilesResponse(
            files=files, 
            total_files=files_data.get('total_files', 0)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File listing error: {str(e)}")
        raise HTTPException(status_code=500, detail="File listing failed")

@router.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """Get detailed information about a specific file"""
    try:
        # Validate file_id
        if not file_id or not InputSanitizer.sanitize_filename(file_id):
            raise HTTPException(status_code=400, detail="Invalid file ID")
            
        logger.info(f"Getting file info for: {file_id}")
        
        # TODO: Implement file info retrieval from database
        return {
            "file_id": file_id,
            "filename": "example.pdf",
            "filepath": "/path/to/example.pdf",
            "size": 0,
            "modified_date": "2024-01-01T00:00:00Z",
            "file_type": "pdf",
            "chunks_count": 0,
            "message": "File info retrieval not fully implemented yet"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File info error: {str(e)}")
        raise HTTPException(status_code=500, detail="File info retrieval failed")

@router.post("/files/open/{file_id}")
async def open_file_by_id(file_id: str):
    """Open a file in the default system application"""
    try:
        # Validate file_id
        if not file_id or not InputSanitizer.sanitize_filename(file_id):
            raise HTTPException(status_code=400, detail="Invalid file ID")
            
        logger.info(f"Opening file by ID: {file_id}")
        
        # TODO: Implement file opening by ID (lookup filepath in database first)
        return {
            "status": "opened", 
            "file_id": file_id,
            "message": "File opening by ID not fully implemented yet"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File opening error: {str(e)}")
        raise HTTPException(status_code=500, detail="File opening failed")

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Remove a file from the corpus"""
    try:
        # Validate file_id
        if not file_id or not InputSanitizer.sanitize_filename(file_id):
            raise HTTPException(status_code=400, detail="Invalid file ID")
            
        # TODO: Implement file deletion from database and vector store
        logger.info(f"Deleting file: {file_id}")
        
        return {
            "status": "deleted", 
            "file_id": file_id,
            "message": "File deletion not fully implemented yet"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail="File deletion failed")

@router.post("/files/open")
async def open_file_by_path(filepath: str):
    """
    Open a source file with the system's default application
    """
    try:
        # Sanitize and validate filepath
        if not filepath or not InputSanitizer.sanitize_path(filepath):
            raise HTTPException(status_code=400, detail="Invalid file path")
            
        file_path = Path(filepath)
        
        # Security check - ensure file exists and is within allowed directories
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
            
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        logger.info(f"Opening file: {filepath}")
        
        # Open file with default system application
        if os.name == 'nt':  # Windows
            os.startfile(str(file_path))
        elif os.name == 'posix':  # macOS and Linux
            if sys.platform == 'darwin':
                subprocess.run(['open', str(file_path)], check=True)
            else:
                subprocess.run(['xdg-open', str(file_path)], check=True)
        else:
            raise HTTPException(status_code=500, detail="Unsupported operating system")
        
        return {"status": "opened", "filepath": filepath}
        
    except HTTPException:
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"File opening subprocess error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to open file with system application")
    except Exception as e:
        logger.error(f"File opening error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to open file")

@router.get("/files/{file_id}/chunks")
async def get_file_chunks(file_id: str):
    """
    Get all chunks for a specific file
    """
    try:
        # Validate file_id
        if not file_id or not InputSanitizer.sanitize_filename(file_id):
            raise HTTPException(status_code=400, detail="Invalid file ID")
            
        logger.info(f"Getting chunks for file ID: {file_id}")
        
        # TODO: Implement chunk retrieval from vector store
        
        return {
            "file_id": file_id,
            "chunks": [],
            "total_chunks": 0,
            "message": "Chunk retrieval not fully implemented yet"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chunk retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chunks")

@router.get("/files/stats")
async def get_corpus_stats():
    """
    Get corpus statistics
    """
    try:
        logger.info("Getting corpus statistics")
        
        # Import vector store
        from embeddings.store import VectorStore
        
        # Initialize vector store
        store = VectorStore()
        stats = store.get_statistics()
        
        return {
            "total_files": stats.get("total_files", 0),
            "total_chunks": stats.get("total_chunks", 0),
            "total_size_mb": stats.get("total_size_mb", 0.0),
            "file_types": stats.get("file_types", {}),
            "last_updated": stats.get("last_updated"),
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"Stats retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")
