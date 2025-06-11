"""
Async vector store implementation with connection pooling and caching
"""
import asyncio
import aiosqlite
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import pickle
import logging
from dataclasses import asdict

from embeddings.chunker import TextChunk
from utils.caching import cache, AsyncMemoryCache
from utils.resource_manager import ResourceManager

logger = logging.getLogger(__name__)

class AsyncVectorStore:
    """
    Async vector database with connection pooling and caching
    """
    
    def __init__(self, 
                 db_path: str = "data/corpus.db", 
                 vector_path: str = "data/vectors.pkl",
                 max_connections: int = 5):
        self.db_path = Path(db_path)
        self.vector_path = Path(vector_path)
        self.max_connections = max_connections
        
        # Create directories
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connection pool
        self._connection_pool: List[aiosqlite.Connection] = []
        self._available_connections = asyncio.Semaphore(max_connections)
        self._pool_lock = asyncio.Lock()
        
        # Caching
        self._cache = AsyncMemoryCache(max_size=1000, default_ttl=1800)  # 30 min TTL
        
        # Vector storage
        self.vectors: Dict[str, np.ndarray] = {}
        self._vector_lock = asyncio.Lock()
        
        # Initialize flag
        self._initialized = False
    
    async def initialize(self):
        """Initialize the async vector store"""
        if self._initialized:
            return
        
        try:
            await self._init_database()
            await self._load_vectors()
            self._initialized = True
            logger.info("AsyncVectorStore initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AsyncVectorStore: {str(e)}")
            raise
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a database connection from the pool"""
        await self._available_connections.acquire()
        
        async with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
            else:
                conn = await aiosqlite.connect(str(self.db_path))
                # Enable WAL mode and optimize
                await conn.execute("PRAGMA journal_mode = WAL")
                await conn.execute("PRAGMA synchronous = NORMAL")
                await conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
                await conn.execute("PRAGMA temp_store = MEMORY")
        
        return conn
    
    async def _return_connection(self, conn: aiosqlite.Connection):
        """Return a connection to the pool"""
        try:
            async with self._pool_lock:
                if len(self._connection_pool) < self.max_connections:
                    self._connection_pool.append(conn)
                else:
                    await conn.close()
        finally:
            self._available_connections.release()
    
    async def _init_database(self):
        """Initialize the database schema"""
        conn = await self._get_connection()
        try:
            await conn.execute("""
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
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    filepath TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_size INTEGER,
                    chunk_count INTEGER DEFAULT 0,
                    last_modified TIMESTAMP,
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_source_file 
                ON chunks(source_file)
            """)
            
            await conn.commit()
            logger.debug("Database schema initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
        finally:
            await self._return_connection(conn)
    
    async def _load_vectors(self):
        """Load vectors from pickle file"""
        async with self._vector_lock:
            try:
                if self.vector_path.exists():
                    # Use asyncio to load file in thread pool
                    loop = asyncio.get_event_loop()
                    self.vectors = await loop.run_in_executor(
                        None, 
                        lambda: pickle.load(open(self.vector_path, 'rb'))
                    )
                    logger.info(f"Loaded {len(self.vectors)} vectors from storage")
                else:
                    self.vectors = {}
                    logger.info("No existing vectors found, starting fresh")
            except Exception as e:
                logger.error(f"Failed to load vectors: {str(e)}")
                self.vectors = {}
    
    async def _save_vectors(self):
        """Save vectors to pickle file atomically"""
        async with self._vector_lock:
            try:
                temp_path = self.vector_path.with_suffix('.tmp')
                
                # Save in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: pickle.dump(self.vectors, open(temp_path, 'wb'))
                )
                
                # Atomic rename
                await loop.run_in_executor(None, lambda: temp_path.replace(self.vector_path))
                logger.debug("Vectors saved to storage")
                
            except Exception as e:
                logger.error(f"Failed to save vectors: {str(e)}")
                # Clean up temp file
                temp_path = self.vector_path.with_suffix('.tmp')
                if temp_path.exists():
                    temp_path.unlink()
    
    @cache(ttl=1800, use_file_cache=False)  # Cache for 30 minutes
    async def search_similar(self, 
                           query_embedding: np.ndarray, 
                           limit: int = 10, 
                           similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar chunks with metadata
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Calculate similarities
            similarities = []
            async with self._vector_lock:
                for chunk_id, vector in self.vectors.items():
                    similarity = np.dot(query_embedding, vector) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(vector)
                    )
                    if similarity >= similarity_threshold:
                        similarities.append((chunk_id, float(similarity)))
            
            # Sort by similarity and limit results
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_similarities = similarities[:limit]
            
            if not top_similarities:
                return []
            
            # Fetch chunk details from database
            chunk_ids = [chunk_id for chunk_id, _ in top_similarities]
            similarity_dict = dict(top_similarities)
            
            conn = await self._get_connection()
            try:
                placeholders = ','.join('?' * len(chunk_ids))
                query = f"""
                    SELECT chunk_id, source_file, content, metadata, start_pos, end_pos
                    FROM chunks 
                    WHERE chunk_id IN ({placeholders})
                """
                
                async with conn.execute(query, chunk_ids) as cursor:
                    results = []
                    async for row in cursor:
                        chunk_id, source_file, content, metadata_json, start_pos, end_pos = row
                        
                        try:
                            metadata = json.loads(metadata_json) if metadata_json else {}
                        except json.JSONDecodeError:
                            metadata = {}
                        
                        results.append({
                            'chunk_id': chunk_id,
                            'source_file': source_file,
                            'content': content,
                            'metadata': metadata,
                            'start_pos': start_pos,
                            'end_pos': end_pos,
                            'similarity_score': similarity_dict[chunk_id]
                        })
                    
                    # Sort results by similarity score
                    results.sort(key=lambda x: x['similarity_score'], reverse=True)
                    return results
                    
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}")
            raise
    
    async def add_chunks(self, chunks: List[TextChunk], embeddings: List[np.ndarray]):
        """
        Add chunks and embeddings to the store
        
        Args:
            chunks: List of text chunks
            embeddings: Corresponding embeddings
        """
        if not self._initialized:
            await self.initialize()
        
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        conn = await self._get_connection()
        try:
            async with conn.executemany(
                """INSERT OR REPLACE INTO chunks 
                   (chunk_id, source_file, content, metadata, start_pos, end_pos)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (
                        chunk.chunk_id,
                        chunk.source_file,
                        chunk.content,
                        json.dumps(chunk.metadata),
                        chunk.start_pos,
                        chunk.end_pos
                    )
                    for chunk in chunks
                ]
            ):
                pass
            
            await conn.commit()
            
            # Add vectors
            async with self._vector_lock:
                for chunk, embedding in zip(chunks, embeddings):
                    self.vectors[chunk.chunk_id] = embedding
            
            # Save vectors asynchronously
            await self._save_vectors()
            
            # Clear related caches
            await self._cache.adelete("chunk_count")
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding chunks: {str(e)}")
            raise
        finally:
            await self._return_connection(conn)
    
    @cache(ttl=300, use_file_cache=False)  # Cache for 5 minutes
    async def get_chunk_count(self) -> int:
        """Get total number of chunks"""
        if not self._initialized:
            await self.initialize()
        
        conn = await self._get_connection()
        try:
            async with conn.execute("SELECT COUNT(*) FROM chunks") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
        finally:
            await self._return_connection(conn)
    
    @cache(ttl=300, use_file_cache=False)  # Cache for 5 minutes
    async def get_file_count(self) -> int:
        """Get total number of files"""
        if not self._initialized:
            await self.initialize()
        
        conn = await self._get_connection()
        try:
            async with conn.execute("SELECT COUNT(*) FROM files") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
        finally:
            await self._return_connection(conn)
    
    async def close(self):
        """Close all connections and cleanup"""
        async with self._pool_lock:
            for conn in self._connection_pool:
                await conn.close()
            self._connection_pool.clear()
        
        # Save vectors one final time
        if self.vectors:
            await self._save_vectors()
        
        logger.info("AsyncVectorStore closed successfully")

# Global async vector store instance
_async_vector_store: Optional[AsyncVectorStore] = None

async def get_async_vector_store() -> AsyncVectorStore:
    """Get or create the global async vector store instance"""
    global _async_vector_store
    if _async_vector_store is None:
        _async_vector_store = AsyncVectorStore()
        await _async_vector_store.initialize()
    return _async_vector_store

async def close_async_vector_store():
    """Close the global async vector store"""
    global _async_vector_store
    if _async_vector_store:
        await _async_vector_store.close()
        _async_vector_store = None
