"""
Input sanitization and validation utilities
"""
import re
import html
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, unquote
import unicodedata

logger = logging.getLogger(__name__)

class InputSanitizer:
    """
    Comprehensive input sanitization for security and data integrity
    """
    
    # Common dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|/\*|\*/|;)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bOR\s+\w+\s*=\s*\w+)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
        r"<link",
        r"<meta",
    ]
    
    # File path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
        r"\.\.%2f",
        r"\.\.%5c",
    ]
    
    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """
        Sanitize a text string for safe processing
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            
        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            logger.warning(f"Expected string, got {type(text)}")
            return str(text)[:max_length]
        
        # Normalize Unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Remove or escape control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length]
            logger.info(f"Text truncated to {max_length} characters")
        
        # Handle HTML
        if not allow_html:
            text = html.escape(text)
        
        # Check for suspicious patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Potential XSS pattern detected: {pattern}")
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize a filename for safe file operations
        
        Args:
            filename: Input filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "untitled"
        
        # Remove URL encoding
        filename = unquote(filename)
        
        # Normalize and remove control characters
        filename = unicodedata.normalize('NFKC', filename)
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Remove path traversal attempts
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Ensure it's not empty and not too long
        if not filename or filename in ['.', '..']:
            filename = "untitled"
        
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename
    
    @classmethod
    def sanitize_query(cls, query: str) -> str:
        """
        Sanitize a search query for safe processing
        
        Args:
            query: Search query string
            
        Returns:
            Sanitized query
        """
        if not query:
            return ""
        
        # Basic sanitization
        query = cls.sanitize_string(query, max_length=1000, allow_html=False)
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected in query: {query}")
                query = re.sub(pattern, ' ', query, flags=re.IGNORECASE)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """
        Sanitize and validate a URL
        
        Args:
            url: Input URL
            
        Returns:
            Sanitized URL or empty string if invalid
        """
        if not url:
            return ""
        
        try:
            # Parse URL
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https', 'ftp', 'ftps']:
                logger.warning(f"Invalid URL scheme: {parsed.scheme}")
                return ""
            
            # Check for suspicious patterns
            full_url = parsed.geturl()
            for pattern in cls.XSS_PATTERNS:
                if re.search(pattern, full_url, re.IGNORECASE):
                    logger.warning(f"Suspicious pattern in URL: {pattern}")
                    return ""
            
            return full_url
            
        except Exception as e:
            logger.error(f"Error sanitizing URL: {str(e)}")
            return ""
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """
        Recursively sanitize a dictionary
        
        Args:
            data: Input dictionary
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized dictionary
        """
        if max_depth <= 0:
            logger.warning("Maximum sanitization depth reached")
            return {}
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            clean_key = cls.sanitize_string(str(key), max_length=100)
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[clean_key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[clean_key] = cls.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[clean_key] = [
                    cls.sanitize_string(str(item)) if isinstance(item, str) else item
                    for item in value[:100]  # Limit list size
                ]
            elif isinstance(value, (int, float, bool)) or value is None:
                sanitized[clean_key] = value
            else:
                # Convert unknown types to string and sanitize
                sanitized[clean_key] = cls.sanitize_string(str(value))
        
        return sanitized

# Validation functions
def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email or len(email) > 254:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return False
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\+\.]', '', phone)
    
    # Check if it's all digits and reasonable length
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension against allowed list
    
    Args:
        filename: The filename to check
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.txt'])
        
    Returns:
        True if extension is allowed
    """
    if not filename or not allowed_extensions:
        return False
    
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Normalize extensions (ensure they start with .)
    normalized_allowed = [
        ext if ext.startswith('.') else f'.{ext}'
        for ext in [e.lower().strip() for e in allowed_extensions]
    ]
    
    return f'.{file_ext}' in normalized_allowed

# Rate limiting helpers
import threading
import time

_request_counts = {}
_request_lock = threading.Lock()

def check_rate_limit(identifier: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
    """
    Simple in-memory rate limiting
    
    Args:
        identifier: Unique identifier (e.g., IP address, user ID)
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
        
    Returns:
        True if request is allowed
    """
    current_time = time.time()
    
    with _request_lock:
        # Clean old entries
        cutoff_time = current_time - window_seconds
        _request_counts[identifier] = [
            timestamp for timestamp in _request_counts.get(identifier, [])
            if timestamp > cutoff_time
        ]
        
        # Check if rate limit exceeded
        request_count = len(_request_counts.get(identifier, []))
        if request_count >= max_requests:
            return False
        
        # Add current request
        _request_counts.setdefault(identifier, []).append(current_time)
        return True
