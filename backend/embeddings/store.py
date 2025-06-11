"""
Vector store for embedding storage and similarity search
"""
import logging
import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from dataclasses import asdict
import pickle
import threading
import contextlib

from embeddings.chunker import TextChunk
from utils.resource_manager import get_database_pool, ResourceManager

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector database for storing and searching document embeddings
    Uses connection pooling and proper resource management
    """
    
    def __init__(self, db_path: str = "data/corpus.db", vector_path: str = "data/vectors.pkl"):
        """
        Initialize the vector store
        
        Args:
            db_path: Path to SQLite database for metadata
            vector_path: Path to pickle file for vector storage
        """
        self.db_path = Path(db_path)
        self.vector_path = Path(vector_path)
        
        # Create directories if they don't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get database pool for connection management
        self.db_pool = get_database_pool(str(self.db_path), max_connections=5)
        
        # Thread-safe vector storage
        self.vectors = {}  # chunk_id -> np.ndarray
        self._vector_lock = threading.RLock()
        
        # Initialize storage
        self._init_database()
        self._load_vectors()
    
    def _init_database(self):
        """Initialize the SQLite database schema"""
        try:
            with self.db_pool.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        chunk_id TEXT PRIMARY KEY,
                        source_file TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        start_pos INTEGER,
                        end_pos INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        filepath TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        file_size INTEGER,
                        chunk_count INTEGER DEFAULT 0,
                        last_modified TIMESTAMP,
                        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_source_file 
                    ON chunks(source_file)
                """)
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def _load_vectors(self):
        """Load vectors from pickle file with proper error handling"""
        with self._vector_lock:
            try:
                if self.vector_path.exists():
                    with open(self.vector_path, 'rb') as f:
                        self.vectors = pickle.load(f)
                    logger.info(f"Loaded {len(self.vectors)} vectors from storage")
                else:
                    self.vectors = {}
                    logger.info("No existing vectors found, starting fresh")
                    
            except Exception as e:
                logger.error(f"Failed to load vectors: {str(e)}")
                self.vectors = {}
    
    def _save_vectors(self):
        """Save vectors to pickle file with atomic writes"""
        with self._vector_lock:
            try:
                # Write to temporary file first for atomic operation
                temp_path = self.vector_path.with_suffix('.tmp')
                with open(temp_path, 'wb') as f:
                    pickle.dump(self.vectors, f)
                
                # Atomic rename
                temp_path.replace(self.vector_path)
                logger.debug("Vectors saved to storage")
                
            except Exception as e:
                logger.error(f"Failed to save vectors: {str(e)}")
                # Clean up temp file if it exists
                temp_path = self.vector_path.with_suffix('.tmp')
                if temp_path.exists():
                    temp_path.unlink()
    
    def add_chunks(self, chunks: List[TextChunk], embeddings: List[np.ndarray]):
        """
        Add chunks and their embeddings to the store
        
        Args:
            chunks: List of TextChunk objects
            embeddings: List of corresponding embeddings
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        try:
            with self.db_pool.get_connection() as conn:
                # Add chunks to database
                chunk_data = []
                for chunk in chunks:
                    chunk_data.append((
                        chunk.chunk_id,
                        chunk.source_file,
                        chunk.content,
                        json.dumps(chunk.metadata),
                        chunk.start_pos,
                        chunk.end_pos
                    ))
                
                conn.executemany("""
                    INSERT OR REPLACE INTO chunks 
                    (chunk_id, source_file, content, metadata, start_pos, end_pos)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, chunk_data)
                
                # Update file chunk count
                for chunk in chunks:
                    conn.execute("""
                        INSERT OR REPLACE INTO files (filepath, filename, chunk_count)
                        VALUES (?, ?, 
                            COALESCE((SELECT chunk_count FROM files WHERE filepath = ?), 0) + 1)
                    """, (chunk.source_file, Path(chunk.source_file).name, chunk.source_file))
                
                conn.commit()
            
            # Add vectors to memory storage
            for chunk, embedding in zip(chunks, embeddings):
                self.vectors[chunk.chunk_id] = embedding
            
            # Save vectors to disk
            self._save_vectors()
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            
        except Exception as e:
            logger.error(f"Failed to add chunks: {str(e)}")
            raise
    
    def search(self, query_embedding: np.ndarray, limit: int = 10, 
               similarity_threshold: float = 0.0) -> List[Tuple[str, float]]:
        """
        Search for similar chunks using cosine similarity
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (chunk_id, similarity_score) tuples
        """
        try:
            if not self.vectors:
                logger.warning("No vectors in store for search")
                return []
            
            similarities = []
            
            for chunk_id, embedding in self.vectors.items():
                similarity = self._cosine_similarity(query_embedding, embedding)
                
                if similarity >= similarity_threshold:
                    similarities.append((chunk_id, similarity))
            
            # Sort by similarity (descending) and limit results
            similarities.sort(key=lambda x: x[1], reverse=True)
            results = similarities[:limit]
            
            logger.info(f"Search found {len(results)} results above threshold {similarity_threshold}")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a chunk by its ID
        
        Args:
            chunk_id: The chunk identifier
            
        Returns:
            Dictionary with chunk data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM chunks WHERE chunk_id = ?
                """, (chunk_id,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    result['metadata'] = json.loads(result['metadata']) if result['metadata'] else {}
                    return result
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {str(e)}")
            return None
    
    def get_file_chunks(self, filepath: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM chunks WHERE source_file = ?
                    ORDER BY start_pos
                """, (filepath,))
                
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    result['metadata'] = json.loads(result['metadata']) if result['metadata'] else {}
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get chunks for file {filepath}: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get chunk count
                cursor = conn.execute("SELECT COUNT(*) FROM chunks")
                chunk_count = cursor.fetchone()[0]
                
                # Get file count
                cursor = conn.execute("SELECT COUNT(*) FROM files")
                file_count = cursor.fetchone()[0]
                
                # Get file types
                cursor = conn.execute("""
                    SELECT 
                        SUBSTR(filename, INSTR(filename, '.')) as extension,
                        COUNT(*) as count
                    FROM files 
                    WHERE INSTR(filename, '.') > 0
                    GROUP BY extension
                """)
                file_types = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    "total_chunks": chunk_count,
                    "total_files": file_count,
                    "vector_count": len(self.vectors),
                    "file_types": file_types
                }
                
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {}
    
    def clear(self):
        """Clear all data from the vector store"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM chunks")
                conn.execute("DELETE FROM files")
                conn.commit()
            
            self.vectors.clear()
            self._save_vectors()
            
            logger.info("Vector store cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear vector store: {str(e)}")
            raise
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
