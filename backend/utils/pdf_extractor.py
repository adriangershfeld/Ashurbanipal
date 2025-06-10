"""
PDF text extraction utilities - Stub implementation
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extract text content from PDF files - Stub implementation"""
    
    def __init__(self):
        self.available = False
        logger.warning("PDF extraction dependencies not installed. Using stub implementation.")
        
    def extract_text(self, file_path: str, method: str = "auto") -> Dict[str, Any]:
        """
        Extract text from PDF file - Stub implementation
        
        Args:
            file_path: Path to PDF file
            method: Extraction method (ignored in stub)
            
        Returns:
            Dict with placeholder data
        """
        logger.warning(f"PDF extraction not implemented: {file_path}")
        return {
            "text": f"PDF extraction not yet implemented for: {Path(file_path).name}",
            "pages": 0,
            "metadata": {},
            "error": "PDF dependencies not installed"
        }
    
    def extract_pages_range(self, file_path: str, start_page: int, end_page: int) -> str:
        """Extract text from a specific range of pages - Stub implementation"""
        logger.warning(f"PDF page range extraction not implemented: {file_path}")
        return f"PDF page extraction not yet implemented for: {Path(file_path).name}"
