"""
Text chunking utilities for breaking documents into manageable pieces
"""
import re
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    source_file: str
    start_pos: int = 0
    end_pos: int = 0

class TextChunker:
    """
    Handles chunking of text documents for embedding and storage
    """
    
    def __init__(self, 
                 chunk_size: int = 500, 
                 chunk_overlap: int = 50,
                 min_chunk_size: int = 100):
        """
        Initialize the text chunker
        
        Args:
            chunk_size: Target size for each chunk (in tokens/characters)
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size for a chunk to be considered valid
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
    def chunk_text(self, text: str, source_file: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """
        Split text into chunks suitable for embedding
        
        Args:
            text: The text to chunk
            source_file: Path to the source file
            metadata: Additional metadata for the chunks
            
        Returns:
            List of TextChunk objects
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            logger.warning(f"Text too short to chunk: {len(text) if text else 0} characters")
            return []
        
        if metadata is None:
            metadata = {}
            
        # Clean the text
        cleaned_text = self._clean_text(text)
        
        # Try sentence-based chunking first
        chunks = self._chunk_by_sentences(cleaned_text, source_file, metadata)
        
        # If chunks are too large, fall back to character-based chunking
        if any(len(chunk.content) > self.chunk_size * 1.5 for chunk in chunks):
            chunks = self._chunk_by_characters(cleaned_text, source_file, metadata)
            
        logger.info(f"Created {len(chunks)} chunks from {source_file}")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for chunking"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove empty lines
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()
    
    def _chunk_by_sentences(self, text: str, source_file: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Chunk text by sentences, respecting chunk size limits"""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_count = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Create chunk from current content
                chunk = self._create_chunk(
                    current_chunk.strip(),
                    source_file,
                    metadata,
                    chunk_count,
                    current_start,
                    current_start + len(current_chunk)
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + " " + sentence
                current_start = current_start + overlap_start
                chunk_count += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk if it has content
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunk = self._create_chunk(
                current_chunk.strip(),
                source_file,
                metadata,
                chunk_count,
                current_start,
                current_start + len(current_chunk)
            )
            chunks.append(chunk)
            
        return chunks
    
    def _chunk_by_characters(self, text: str, source_file: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Fallback chunking by character count"""
        chunks = []
        chunk_count = 0
        
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk_text = text[i:i + self.chunk_size]
            
            if len(chunk_text.strip()) >= self.min_chunk_size:
                chunk = self._create_chunk(
                    chunk_text.strip(),
                    source_file,
                    metadata,
                    chunk_count,
                    i,
                    i + len(chunk_text)
                )
                chunks.append(chunk)
                chunk_count += 1
                
        return chunks
    
    def _create_chunk(self, content: str, source_file: str, metadata: Dict[str, Any], 
                     chunk_num: int, start_pos: int, end_pos: int) -> TextChunk:
        """Create a TextChunk object with proper metadata"""
        chunk_metadata = {
            **metadata,
            "chunk_number": chunk_num,
            "total_length": len(content),
            "word_count": len(content.split())
        }
        
        chunk_id = f"{source_file}_{chunk_num:04d}"
        
        return TextChunk(
            content=content,
            metadata=chunk_metadata,
            chunk_id=chunk_id,
            source_file=source_file,
            start_pos=start_pos,
            end_pos=end_pos
        )
