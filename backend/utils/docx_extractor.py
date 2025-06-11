"""
DOCX text extraction utilities
"""
import logging
from pathlib import Path
from typing import Dict, Any
import zipfile
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class DOCXExtractor:
    """Extract text content from DOCX files"""
    
    def __init__(self):
        self.namespace = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a DOCX file
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not path_obj.suffix.lower() == '.docx':
                raise ValueError(f"Not a DOCX file: {file_path}")
            
            logger.info(f"Extracting text from DOCX: {file_path}")
            
            text_content = self._extract_text_from_docx(path_obj)
            
            if not text_content:
                logger.warning(f"No text content found in {file_path}")
                return {"text": "", "metadata": {"error": "No text content found"}}
            
            metadata = {
                "file_path": str(path_obj),
                "file_size": path_obj.stat().st_size,
                "char_count": len(text_content),
                "word_count": len(text_content.split()),
                "extraction_method": "xml_parsing"
            }
            
            logger.info(f"Successfully extracted {len(text_content)} characters from {path_obj.name}")
            
            return {
                "text": text_content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
            return {
                "text": "",
                "metadata": {"error": str(e)}
            }
    
    def _extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text using XML parsing of DOCX structure"""
        try:
            text_parts = []
            
            with zipfile.ZipFile(file_path, 'r') as docx_zip:
                # Check if document.xml exists (main content)
                if 'word/document.xml' not in docx_zip.namelist():
                    logger.error("No document.xml found in DOCX file")
                    return ""
                
                # Extract main document content
                document_xml = docx_zip.read('word/document.xml')
                root = ET.fromstring(document_xml)
                
                # Find all text elements
                for text_elem in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    if text_elem.text:
                        text_parts.append(text_elem.text)
                
                # Add paragraph breaks
                paragraphs = []
                current_paragraph = []
                
                for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    para_text = ""
                    for text_elem in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                        if text_elem.text:
                            para_text += text_elem.text
                    
                    if para_text.strip():
                        paragraphs.append(para_text.strip())
                
                # Join paragraphs with double newlines
                full_text = '\n\n'.join(paragraphs)
                
                return full_text
                
        except zipfile.BadZipFile:
            logger.error(f"Invalid DOCX file (corrupted ZIP): {file_path}")
            return ""
        except ET.ParseError as e:
            logger.error(f"XML parsing error in DOCX: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error parsing DOCX: {e}")
            return ""
    def is_valid_docx(self, file_path: str) -> bool:
        """Check if file is a valid DOCX file"""
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                return False
            
            if not path_obj.suffix.lower() == '.docx':
                return False
            
            # Check if it's a valid ZIP file with DOCX structure
            with zipfile.ZipFile(path_obj, 'r') as docx_zip:
                required_files = ['[Content_Types].xml', 'word/document.xml']
                for required_file in required_files:
                    if required_file not in docx_zip.namelist():
                        return False
            
            return True
            
        except (zipfile.BadZipFile, FileNotFoundError, PermissionError):
            return False
        except Exception:
            return False

def extract_docx_text(file_path: str) -> str:
    """
    Convenience function to extract text from DOCX file
    
    Args:
        file_path: Path to DOCX file
        
    Returns:
        Extracted text content
    """
    extractor = DOCXExtractor()
    result = extractor.extract_text(file_path)
    return result.get("text", "")

if __name__ == "__main__":
    # Test the extractor
    import sys
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        extractor = DOCXExtractor()
        
        if extractor.is_valid_docx(test_file):
            result = extractor.extract_text(test_file)
            print(f"Extracted {len(result['text'])} characters")
            print(f"Metadata: {result['metadata']}")
            print(f"Text preview: {result['text'][:500]}...")
        else:
            print(f"Invalid DOCX file: {test_file}")
    else:
        print("Usage: python docx_extractor.py <path_to_docx_file>")
