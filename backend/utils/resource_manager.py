"""
Database connection pool and resource management utilities
"""
import sqlite3
import threading
import contextlib
import logging
from typing import Generator
from pathlib import Path
import time
import weakref

logger = logging.getLogger(__name__)

class DatabasePool:
    """
    Simple SQLite connection pool with proper resource management
    """
    
    def __init__(self, database_path: str, max_connections: int = 10):
        self.database_path = Path(database_path)
        self.max_connections = max_connections
        self._pool = []
        self._in_use = set()
        self._lock = threading.Lock()
        self._created_connections = 0
        
        # Create database directory if needed
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Track instances for cleanup
        self._instances = weakref.WeakSet()
        
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimal settings"""
        conn = sqlite3.connect(
            str(self.database_path),
            timeout=30.0,  # 30 second timeout
            check_same_thread=False
        )
        
        # Enable foreign keys and optimize performance
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        
        self._created_connections += 1
        logger.debug(f"Created new database connection ({self._created_connections} total)")
        return conn
        
    @contextlib.contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection from the pool using context manager
        
        Usage:
            with pool.get_connection() as conn:
                conn.execute("SELECT * FROM table")
        """
        conn = None
        try:
            with self._lock:
                if self._pool:
                    conn = self._pool.pop()
                elif self._created_connections < self.max_connections:
                    conn = self._create_connection()
                else:
                    # Wait for a connection to become available
                    logger.warning("Connection pool exhausted, waiting for available connection")
                    
            if conn is None:
                # Fallback: create temporary connection
                conn = self._create_connection()
                logger.warning("Created temporary connection due to pool exhaustion")
                
            # Mark connection as in use
            with self._lock:
                self._in_use.add(conn)
                
            yield conn
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            if conn:
                try:
                    # Return connection to pool
                    with self._lock:
                        self._in_use.discard(conn)
                        if len(self._pool) < self.max_connections:
                            self._pool.append(conn)
                        else:
                            conn.close()
                            self._created_connections -= 1
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}")
                    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            # Close pooled connections
            for conn in self._pool:
                try:
                    conn.close()
                except:
                    pass
            self._pool.clear()
            
            # Close in-use connections
            for conn in list(self._in_use):
                try:
                    conn.close()
                except:
                    pass
            self._in_use.clear()
            
            self._created_connections = 0
            logger.info("All database connections closed")
            
    def get_stats(self) -> dict:
        """Get pool statistics"""
        with self._lock:
            return {
                "pool_size": len(self._pool),
                "in_use": len(self._in_use),
                "total_created": self._created_connections,
                "max_connections": self.max_connections
            }

class ResourceManager:
    """
    Context manager for proper resource cleanup
    """
    
    def __init__(self):
        self._resources = []
        self._cleanup_callbacks = []
        
    def add_resource(self, resource, cleanup_method: str = 'close'):
        """Add a resource to be cleaned up"""
        self._resources.append((resource, cleanup_method))
        
    def add_callback(self, callback):
        """Add a cleanup callback function"""
        self._cleanup_callbacks.append(callback)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        
    def cleanup(self):
        """Clean up all managed resources"""
        # Execute cleanup callbacks first
        for callback in reversed(self._cleanup_callbacks):
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback: {str(e)}")
                
        # Clean up resources
        for resource, method_name in reversed(self._resources):
            try:
                if hasattr(resource, method_name):
                    getattr(resource, method_name)()
                elif hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, '__exit__'):
                    resource.__exit__(None, None, None)
            except Exception as e:
                logger.error(f"Error cleaning up resource: {str(e)}")
                
        self._resources.clear()
        self._cleanup_callbacks.clear()

# Global database pools - initialized when needed
_db_pools = {}
_pool_lock = threading.Lock()

def get_database_pool(database_path: str, max_connections: int = 10) -> DatabasePool:
    """Get or create a database pool for the given path"""
    abs_path = str(Path(database_path).absolute())
    
    with _pool_lock:
        if abs_path not in _db_pools:
            _db_pools[abs_path] = DatabasePool(abs_path, max_connections)
            logger.info(f"Created database pool for {abs_path}")
        return _db_pools[abs_path]

def cleanup_all_pools():
    """Cleanup all database pools - should be called on app shutdown"""
    with _pool_lock:
        for pool in _db_pools.values():
            pool.close_all()
        _db_pools.clear()
        logger.info("All database pools cleaned up")

# Context manager for temporary files
@contextlib.contextmanager
def temporary_file_manager(*file_paths):
    """
    Context manager that ensures temporary files are cleaned up
    
    Usage:
        with temporary_file_manager("temp1.txt", "temp2.txt"):
            # work with files
            pass
        # files are automatically cleaned up
    """
    try:
        yield
    finally:
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    logger.debug(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup temporary file {file_path}: {str(e)}")
