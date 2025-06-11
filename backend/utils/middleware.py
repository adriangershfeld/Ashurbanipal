"""
Security and rate limiting middleware for FastAPI
"""
import time
import logging
from typing import Dict, Optional, Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import ipaddress

from utils.sanitization import check_rate_limit

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware
    """
    
    def __init__(self, 
                 app,
                 enable_rate_limiting: bool = True,
                 max_requests_per_hour: int = 1000,
                 max_requests_per_minute: int = 60,
                 blocked_ips: Optional[set] = None,
                 allowed_origins: Optional[list] = None):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.max_requests_per_hour = max_requests_per_hour
        self.max_requests_per_minute = max_requests_per_minute
        self.blocked_ips = blocked_ips or set()
        self.allowed_origins = allowed_origins or []
          # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Get the client IP address with improved IPv6 support"""
        # Check for forwarded IP headers (in order of trust)
        forwarded_headers = [
            "X-Forwarded-For",
            "X-Real-IP",
            "CF-Connecting-IP",  # Cloudflare
            "X-Forwarded"
        ]
        
        for header in forwarded_headers:
            if header in request.headers:
                # Handle comma-separated IPs (X-Forwarded-For can have multiple)
                ip_list = request.headers[header].split(',')
                for ip in ip_list:
                    ip = ip.strip()
                    # Remove port if present (for IPv6: [::1]:8080 -> ::1)
                    if ip.startswith('[') and ']:' in ip:
                        ip = ip.split(']:')[0][1:]
                    elif ':' in ip and not ip.count(':') > 1:  # IPv4 with port
                        ip = ip.split(':')[0]
                    
                    try:
                        # Validate IP address (supports both IPv4 and IPv6)
                        parsed_ip = ipaddress.ip_address(ip)
                        # Skip private/loopback addresses in forwarded headers
                        if not (parsed_ip.is_private or parsed_ip.is_loopback):
                            return str(parsed_ip)
                        elif len(ip_list) == 1:  # If only one IP, use it even if private
                            return str(parsed_ip)
                    except ValueError:
                        continue
        
        # Fallback to direct connection
        client_host = request.client.host if request.client else "unknown"
        if client_host != "unknown":
            try:
                # Validate the direct connection IP
                ipaddress.ip_address(client_host)
                return client_host
            except ValueError:
                pass
        
        return "unknown"
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """Check if request shows suspicious patterns"""
        try:
            # Check for suspicious paths
            suspicious_paths = [
                "/admin", "/.env", "/wp-admin", "/phpmyadmin",
                "/config", "/backup", "/test", "/debug"
            ]
            
            if any(path in str(request.url.path).lower() for path in suspicious_paths):
                return True
            
            # Check for suspicious user agents
            user_agent = request.headers.get("User-Agent", "").lower()
            suspicious_agents = [
                "bot", "crawler", "spider", "scraper", "scanner",
                "sqlmap", "nikto", "nmap", "masscan"
            ]
            
            if any(agent in user_agent for agent in suspicious_agents):
                return True
            
            # Check for SQL injection patterns in query parameters
            query_string = str(request.url.query).lower()
            sql_patterns = [
                "union select", "or 1=1", "drop table", "insert into",
                "delete from", "update set", "exec(", "script>"
            ]
            
            if any(pattern in query_string for pattern in sql_patterns):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking suspicious request: {str(e)}")
            return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through security checks"""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # Check if IP is blocked
            if client_ip in self.blocked_ips:
                logger.warning(f"Blocked IP attempted access: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied"}
                )
            
            # Check for suspicious requests
            if self._is_suspicious_request(request):
                logger.warning(f"Suspicious request from {client_ip}: {request.url}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Request not allowed"}
                )
            
            # Rate limiting
            if self.enable_rate_limiting:
                # Check hourly rate limit
                if not check_rate_limit(
                    f"hourly_{client_ip}", 
                    self.max_requests_per_hour, 
                    3600
                ):
                    logger.warning(f"Hourly rate limit exceeded for {client_ip}")
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Hourly rate limit exceeded"},
                        headers={"Retry-After": "3600"}
                    )
                
                # Check per-minute rate limit
                if not check_rate_limit(
                    f"minute_{client_ip}", 
                    self.max_requests_per_minute, 
                    60
                ):
                    logger.warning(f"Per-minute rate limit exceeded for {client_ip}")
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"},
                        headers={"Retry-After": "60"}
                    )
            
            # Process the request
            response = await call_next(request)
            
            # Add security headers
            for header, value in self.security_headers.items():
                response.headers[header] = value
            
            # Add timing header for debugging
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log successful request
            logger.info(
                f"{request.method} {request.url.path} - {client_ip} - "
                f"{response.status_code} - {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            # Don't expose internal errors
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for detailed request logging
    """
    
    def __init__(self, app, log_body: bool = False, max_body_size: int = 1024):
        super().__init__(app)
        self.log_body = log_body
        self.max_body_size = max_body_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details"""
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url} from {client_ip}"
        )
        
        # Process request first to avoid consuming body stream
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - {process_time:.3f}s"
        )
        
        # Note: Request body logging has been moved after response processing
        # to avoid consuming the body stream and breaking downstream handlers.
        # For detailed body logging, consider using a different approach or
        # implementing it at the application level.
        
        return response

def create_security_middleware(
    enable_rate_limiting: bool = True,
    max_requests_per_hour: int = 1000,
    max_requests_per_minute: int = 60,
    blocked_ips: Optional[set] = None,
    allowed_origins: Optional[list] = None
) -> Callable:
    """
    Factory function to create security middleware with configuration
    """
    def middleware_factory(app):
        return SecurityMiddleware(
            app,
            enable_rate_limiting=enable_rate_limiting,
            max_requests_per_hour=max_requests_per_hour,
            max_requests_per_minute=max_requests_per_minute,
            blocked_ips=blocked_ips,
            allowed_origins=allowed_origins
        )
    return middleware_factory

def create_logging_middleware(
    log_body: bool = False,
    max_body_size: int = 1024
) -> Callable:
    """
    Factory function to create logging middleware with configuration
    """
    def middleware_factory(app):
        return RequestLoggingMiddleware(
            app,
            log_body=log_body,
            max_body_size=max_body_size
        )
    return middleware_factory
