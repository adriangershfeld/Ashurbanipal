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
import aiofiles

from utils.file_loader import FileLoader
from utils.pdf_extractor import PDFExtractor
from utils.docx_extractor import DOCXExtractor
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
        
        # Initialize components once and reuse them
        file_loader = FileLoader(supported_extensions=valid_extensions)
        pdf_extractor = PDFExtractor()
        docx_extractor = DOCXExtractor()
        vector_store = VectorStore()
        chunker = TextChunker()
        embedder = EmbeddingModel()
        
        files_processed = 0
        chunks_created = 0
        
        try:
            # 1. Scan folder for files
            logger.info("Scanning folder for files...")
            files = file_loader.scan_directory(folder_path, recursive=request.recursive)
            logger.info(f"Found {len(files)} files to process")
            
            if not files:
                return IngestResponse(
                    status="completed",
                    files_processed=0,
                    chunks_created=0,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # 2. Process each file with proper error handling and resource cleanup
            for file_info in files:
                try:
                    filepath = file_info['filepath']
                    filename = file_info['filename']
                    logger.info(f"Processing file: {filename}")
                    
                    # Check if file already exists in vector store
                    if vector_store.file_exists(filepath):
                        logger.info(f"File already processed: {filename}")
                        continue
                    
                    # 3. Extract text from file with proper resource management
                    text_content = await _extract_text_from_file(
                        filepath, pdf_extractor, docx_extractor
                    )
                    
                    if not text_content or len(text_content.strip()) < 50:
                        logger.warning(f"No content extracted from {filename}")
                        continue
                    
                    # 4. Chunk the text
                    chunks = chunker.chunk_text(text_content, filepath, {"file_type": Path(filepath).suffix[1:]})
                    logger.info(f"Created {len(chunks)} chunks from {filename}")
                    
                    if not chunks:
                        continue
                    
                    # 5. Generate embeddings in batches to manage memory
                    chunk_texts = [chunk.content for chunk in chunks]
                    embeddings = embedder.batch_embed(chunk_texts)
                    
                    # 6. Store in vector database
                    vector_store.add_chunks(chunks, embeddings)
                    
                    files_processed += 1
                    chunks_created += len(chunks)
                    
                    logger.info(f"Successfully processed {filename}: {len(chunks)} chunks")
                    
                except Exception as file_error:
                    logger.error(f"Error processing file {file_info.get('filename', 'unknown')}: {str(file_error)}")
                    continue
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Folder ingestion completed: {files_processed} files, {chunks_created} chunks in {processing_time:.2f}ms")
            
            return IngestResponse(
                status="completed",
                files_processed=files_processed,
                chunks_created=chunks_created,
                processing_time_ms=processing_time
            )
            
        except Exception as processing_error:
            logger.error(f"Error during file processing: {str(processing_error)}")
            processing_time = (time.time() - start_time) * 1000
            
            return IngestResponse(
                status="partial" if files_processed > 0 else "failed",
                files_processed=files_processed,
                chunks_created=chunks_created,
                processing_time_ms=processing_time
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Folder ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Folder ingestion failed")

async def _extract_text_from_file(filepath: str, pdf_extractor, docx_extractor) -> str:
    """Extract text from file with proper async handling and error management"""
    try:
        file_extension = Path(filepath).suffix[1:].lower()
        text_content = ""
        
        if file_extension == 'pdf':
            # PDF extractor returns a dict, get the text field
            pdf_result = pdf_extractor.extract_text(filepath)
            if isinstance(pdf_result, dict):
                text_content = pdf_result.get('text', '')
            else:
                text_content = str(pdf_result)
        elif file_extension in ['txt', 'md', 'py']:
            # Use async file reading for better performance
            async with aiofiles.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = await f.read()
        elif file_extension == 'docx':
            # DOCX extractor
            docx_result = docx_extractor.extract_text(filepath)
            if isinstance(docx_result, dict):
                text_content = docx_result.get('text', '')
            else:
                text_content = str(docx_result)
        
        return text_content
        
    except Exception as e:
        logger.error(f"Error extracting text from {filepath}: {str(e)}")
        return ""

@router.post("/ingest/file")
async def ingest_single_file(file: UploadFile = File(...)):
    """Ingest a single uploaded file"""
    import tempfile
    import os
    
    try:
        start_time = time.time()
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        if not InputSanitizer.sanitize_filename(file.filename):
            raise HTTPException(status_code=400, detail="Invalid filename")
            
        # Check file size (limit to 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
            
        # Check file extension
        file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        supported_extensions = ['pdf', 'txt', 'md', 'docx']
        if file_extension not in supported_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported: {supported_extensions}")
            
        logger.info(f"Ingesting uploaded file: {file.filename}")
          # Import required modules
        from utils.pdf_extractor import PDFExtractor
        from utils.docx_extractor import DOCXExtractor
        from embeddings.store import VectorStore
        from embeddings.chunker import TextChunker
        from embeddings.embedder import EmbeddingModel
        
        # Initialize components
        pdf_extractor = PDFExtractor()
        docx_extractor = DOCXExtractor()
        vector_store = VectorStore()
        chunker = TextChunker()
        embedder = EmbeddingModel()
        
        # 1. Save uploaded file temporarily
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_filepath = temp_file.name
              # 2. Extract text based on file type
            text_content = ""
            if file_extension == 'pdf':
                pdf_result = pdf_extractor.extract_text(temp_filepath)
                if isinstance(pdf_result, dict):
                    text_content = pdf_result.get('text', '')
                else:
                    text_content = str(pdf_result)
            elif file_extension in ['txt', 'md']:
                with open(temp_filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = f.read()
            elif file_extension == 'docx':
                # DOCX extractor
                docx_result = docx_extractor.extract_text(temp_filepath)
                if isinstance(docx_result, dict):
                    text_content = docx_result.get('text', '')
                else:
                    text_content = str(docx_result)
            
            if not text_content or len(text_content.strip()) < 50:
                raise HTTPException(status_code=400, detail="No readable content found in file")
            
            # 3. Chunk the text
            chunks = chunker.chunk_text(text_content, file.filename, {"file_type": file_extension})
            logger.info(f"Created {len(chunks)} chunks from {file.filename}")
            
            if not chunks:
                raise HTTPException(status_code=400, detail="Failed to create text chunks")
            
            # 4. Generate embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = embedder.batch_embed(chunk_texts)
            
            # 5. Store in vector database
            vector_store.add_chunks(chunks, embeddings)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Successfully processed {file.filename}: {len(chunks)} chunks in {processing_time:.2f}ms")
            
            return {
                "status": "completed", 
                "filename": file.filename,
                "size": file.size,
                "chunks_created": len(chunks),
                "processing_time_ms": processing_time,
                "message": "File successfully ingested"
            }
            
        finally:
            # 6. Clean up temporary file
            if temp_file and os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
    
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
