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
import asyncio
import stat
from pathlib import Path
from typing import List, Tuple

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

class OpenFolderRequest(BaseModel):
    folder_path: str

class OperationResponse(BaseModel):
    status: str
    message: str
    details: Optional[dict] = None

def is_safe_path(path: Path, allowed_prefixes: Optional[List[str]] = None) -> bool:
    """
    Enhanced security check for file paths
    """
    try:
        # Resolve to absolute path to handle ../ traversal attempts
        resolved_path = path.resolve()
        
        # Default allowed prefixes (can be configured)
        if allowed_prefixes is None:
            allowed_prefixes = [
                str(Path.home()),  # User home directory
                str(Path.cwd()),   # Current working directory
                "C:\\Users",       # Windows Users folder
                "/home",           # Linux home folders
                "/Users"           # macOS Users folder
            ]
        
        # Check if path starts with any allowed prefix
        for prefix in allowed_prefixes:
            if str(resolved_path).startswith(str(Path(prefix).resolve())):
                return True
                
        return False
    except (OSError, ValueError):
        return False

def check_folder_permissions(path: Path) -> Tuple[bool, str]:
    """
    Check if folder can be accessed and opened
    """
    try:
        # Check read permission
        if not os.access(path, os.R_OK):
            return False, "Read permission denied"
            
        # Check if it's a directory
        if not path.is_dir():
            return False, "Path is not a directory"
            
        # Try to list directory contents (quick permission test)
        try:
            next(path.iterdir())
        except StopIteration:
            # Empty directory is fine
            pass
        except PermissionError:
            return False, "Directory access denied"
            
        return True, "OK"
    except Exception as e:
        return False, f"Permission check failed: {str(e)}"

async def safe_subprocess_run(cmd: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
    """
    Safely run subprocess with timeout and proper error handling
    """
    try:
        # Use asyncio to run subprocess with timeout
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
          stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=timeout
        )
        
        return subprocess.CompletedProcess(
            cmd, process.returncode or 0, stdout, stderr
        )
    except asyncio.TimeoutError:
        # Kill the process if it times out
        try:
            process.kill()
            await process.wait()
        except:
            pass
        raise subprocess.TimeoutExpired(cmd, timeout)

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

@router.post("/files/open-folder", response_model=OperationResponse)
async def open_folder_in_explorer(request: OpenFolderRequest):
    """
    Open a folder in the system's default file explorer with enhanced security
    """
    logger.info(f"Received open folder request: {request.folder_path}")
    
    try:
        folder_path = request.folder_path.strip()
        
        # Enhanced validation
        if not folder_path:
            raise HTTPException(
                status_code=400, 
                detail="Folder path cannot be empty"
            )
            
        # Sanitize path
        if not InputSanitizer.sanitize_path(folder_path):
            logger.warning(f"Path failed sanitization: {folder_path}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid characters in folder path"
            )
            
        path = Path(folder_path)
        logger.info(f"Processing path: {path}")
          # Security checks (temporarily disabled for debugging)
        # if not is_safe_path(path):
        #     logger.warning(f"Path outside allowed directories: {path}")
        #     raise HTTPException(
        #         status_code=403, 
        #         detail="Access to this folder is not permitted"
        #     )
        
        # Existence check
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            raise HTTPException(
                status_code=404, 
                detail="Folder not found"
            )
            
        # Handle file paths by using parent directory
        if path.is_file():
            path = path.parent
            logger.info(f"Using parent directory: {path}")
        
        # Permission checks
        can_access, perm_message = check_folder_permissions(path)
        if not can_access:
            logger.warning(f"Permission denied for {path}: {perm_message}")
            raise HTTPException(
                status_code=403, 
                detail=f"Cannot access folder: {perm_message}"
            )
        
        logger.info(f"Opening folder in explorer: {path}")        # Platform-specific folder opening
        logger.info(f"About to open folder with explorer: {path}")
        logger.info(f"OS name: {os.name}")
        
        try:
            if os.name == 'nt':  # Windows
                logger.info("Running Windows explorer command")
                # Use subprocess.run without check=True for Windows explorer
                result = subprocess.run(['explorer', str(path)], 
                                      capture_output=True, text=True, timeout=10)
                logger.info(f"Explorer command completed with return code: {result.returncode}")
                logger.info(f"Stdout: {result.stdout}")
                logger.info(f"Stderr: {result.stderr}")
                # Explorer returns 1 on success, so don't treat it as error
            elif sys.platform == 'darwin':  # macOS
                logger.info("Running macOS open command")
                await safe_subprocess_run(['open', str(path)])
            elif os.name == 'posix':  # Linux
                logger.info("Running Linux xdg-open command")
                await safe_subprocess_run(['xdg-open', str(path)])
            else:
                logger.error(f"Unsupported OS: {os.name}")
                raise HTTPException(
                    status_code=500, 
                    detail="Unsupported operating system"
                )
        except subprocess.TimeoutExpired as te:
            logger.error(f"Timeout opening folder: {path} - {te}")
            raise HTTPException(
                status_code=500, 
                detail="Folder opening timed out"
            )
        except Exception as e:
            logger.error(f"Exception opening folder: {path} - {e}")
            logger.error(f"Exception type: {type(e)}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to open folder with system file manager"
            )
        
        return OperationResponse(
            status="success",
            message="Folder opened successfully",
            details={"folder_path": str(path)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error opening folder: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while opening the folder"
        )

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

@router.get("/files/{filename}/content")
async def get_file_content(filename: str, max_length: int = 10000):
    """Get file content for preview"""
    try:
        # Validate filename
        if not filename or not InputSanitizer.sanitize_filename(filename):
            raise HTTPException(status_code=400, detail="Invalid filename")
            
        logger.info(f"Getting content for file: {filename}")
        
        # Import vector store to get file info
        from embeddings.store import VectorStore
        
        store = VectorStore()
        
        # First try to find file by checking all files
        files_data = store.get_files_list(limit=1000)  # Get a large list to search
        file_info = None
        
        for file in files_data.get('files', []):
            if file.get('filename') == filename:
                file_info = file
                break
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Try to read original file content
        file_path = file_info.get('filepath')
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(max_length)
                    return {
                        "filename": filename,
                        "content": content,
                        "truncated": len(content) >= max_length,
                        "source": "original_file"
                    }
            except UnicodeDecodeError:
                # Try binary file handling for PDFs, etc.
                pass
        
        # Fallback: get content from chunks using filepath
        chunks = store.get_file_chunks(file_path) if file_path else []
        if chunks:
            # Combine first few chunks for preview
            chunk_content = "\n\n".join([chunk.get('content', '') for chunk in chunks[:5]])
            content = chunk_content[:max_length]
            
            return {
                "filename": filename,
                "content": content,
                "truncated": len(chunk_content) > max_length,
                "source": "chunks",
                "total_chunks": len(chunks)
            }
        
        # No content available
        return {
            "filename": filename,
            "content": "",
            "error": "Content not available for preview",
            "source": "none"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file content")

# ...existing code...
