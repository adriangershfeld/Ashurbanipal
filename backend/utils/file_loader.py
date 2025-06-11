"""
File loading utilities for scanning and discovering documents
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Generator
import mimetypes
from datetime import datetime
import fnmatch

# Import configuration
try:
    from config import SUPPORTED_EXTENSIONS, EXCLUDE_PATTERNS, EXCLUDE_DIRECTORIES
except ImportError:
    # Fallback if config not available
    SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx', '.doc', '.rtf']
    EXCLUDE_PATTERNS = ['*.py', '*.js', '*.ts', '*.json', '*.log', '__pycache__']
    EXCLUDE_DIRECTORIES = ['__pycache__', 'node_modules', '.git', '.vscode']

logger = logging.getLogger(__name__)

class FileLoader:
    """
    Handles discovery and loading of files from the file system
    """
    
    def __init__(self, supported_extensions: List[str] | None = None):
        """
        Initialize the file loader
        
        Args:
            supported_extensions: List of file extensions to process (e.g., ['.pdf', '.txt'])
        """
        if supported_extensions is None:
            supported_extensions = list(SUPPORTED_EXTENSIONS)
        
        self.supported_extensions = [ext.lower() for ext in supported_extensions]
        self.exclude_patterns = list(EXCLUDE_PATTERNS)
        self.exclude_directories = list(EXCLUDE_DIRECTORIES)
        logger.info(f"FileLoader initialized with extensions: {self.supported_extensions}")
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on patterns"""
        filename = file_path.name
        
        # Check against exclude patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return True
        
        return False
    
    def _should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if a directory should be excluded"""
        dirname = dir_path.name.lower()
        
        for exclude_dir in self.exclude_directories:
            if exclude_dir.lower() in dirname:
                return True
        
        return False
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Scan a directory for supported files
        
        Args:
            directory_path: Path to the directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of file information dictionaries
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        files = []
        
        try:
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in directory.glob(pattern):
                # Skip if any parent directory should be excluded
                if any(self._should_exclude_directory(parent) for parent in file_path.parents):
                    continue
                    
                if file_path.is_file() and self._is_supported_file(file_path) and not self._should_exclude_file(file_path):
                    file_info = self._get_file_info(file_path)
                    files.append(file_info)
            
            logger.info(f"Found {len(files)} supported files in {directory_path}")
            return files
            
        except Exception as e:
            logger.error(f"Error scanning directory {directory_path}: {str(e)}")
            raise
    
    def scan_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process a list of specific file paths
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of file information dictionaries for valid files
        """
        files = []
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                
                if path.exists() and path.is_file() and self._is_supported_file(path):
                    file_info = self._get_file_info(path)
                    files.append(file_info)
                else:
                    logger.warning(f"Skipping invalid or unsupported file: {file_path}")
                    
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                continue
        
        logger.info(f"Processed {len(files)} valid files from {len(file_paths)} provided paths")
        return files
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if a file has a supported extension"""
        return file_path.suffix.lower() in self.supported_extensions
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata information from a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            stat = file_path.stat()
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            file_info = {
                'filepath': str(file_path.absolute()),
                'filename': file_path.name,
                'extension': file_path.suffix.lower(),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'mime_type': mime_type,
                'parent_directory': str(file_path.parent),
                'is_readable': os.access(file_path, os.R_OK)
            }
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            # Return minimal info on error
            return {
                'filepath': str(file_path.absolute()),
                'filename': file_path.name,
                'extension': file_path.suffix.lower(),
                'size_bytes': 0,
                'size_mb': 0,
                'error': str(e)
            }
    
    def filter_by_size(self, files: List[Dict[str, Any]], 
                      min_size_mb: float = 0.001, 
                      max_size_mb: float = 100) -> List[Dict[str, Any]]:
        """
        Filter files by size constraints
        
        Args:
            files: List of file information dictionaries
            min_size_mb: Minimum file size in MB
            max_size_mb: Maximum file size in MB
            
        Returns:
            Filtered list of files
        """
        filtered = []
        
        for file_info in files:
            size_mb = file_info.get('size_mb', 0)
            
            if min_size_mb <= size_mb <= max_size_mb:
                filtered.append(file_info)
            else:
                logger.debug(f"Filtered out {file_info['filename']} (size: {size_mb}MB)")
        
        logger.info(f"Size filter: {len(filtered)}/{len(files)} files passed")
        return filtered
    
    def filter_by_extension(self, files: List[Dict[str, Any]], 
                           extensions: List[str]) -> List[Dict[str, Any]]:
        """
        Filter files by specific extensions
        
        Args:
            files: List of file information dictionaries
            extensions: List of extensions to keep (e.g., ['.pdf', '.txt'])
            
        Returns:
            Filtered list of files
        """
        extensions_lower = [ext.lower() for ext in extensions]
        filtered = []
        
        for file_info in files:
            if file_info.get('extension', '').lower() in extensions_lower:
                filtered.append(file_info)
        
        logger.info(f"Extension filter: {len(filtered)}/{len(files)} files passed")
        return filtered
    
    def get_summary(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of the file collection
        
        Args:
            files: List of file information dictionaries
            
        Returns:
            Summary statistics
        """
        if not files:
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'extensions': {},
                'largest_file': None,
                'smallest_file': None
            }
        
        # Calculate statistics
        total_size = sum(f.get('size_mb', 0) for f in files)
        extensions = {}
        
        for file_info in files:
            ext = file_info.get('extension', 'unknown')
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Find largest and smallest files
        files_with_size = [f for f in files if 'size_mb' in f and f['size_mb'] > 0]
        largest_file = max(files_with_size, key=lambda x: x['size_mb']) if files_with_size else None
        smallest_file = min(files_with_size, key=lambda x: x['size_mb']) if files_with_size else None
        
        return {
            'total_files': len(files),
            'total_size_mb': round(total_size, 2),
            'extensions': extensions,
            'largest_file': largest_file['filename'] if largest_file else None,
            'smallest_file': smallest_file['filename'] if smallest_file else None,
            'average_size_mb': round(total_size / len(files), 2) if files else 0
        }
