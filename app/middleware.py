"""Custom middleware for the RAG Q&A system."""

import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.exceptions import RAGServiceError
from app.utils.logger import get_logger, set_request_id, log_performance, log_error


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app):
        """Initialize request logging middleware."""
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process HTTP request and log details.
        
        Args:
            request: HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response
        """
        # Generate and set request ID
        request_id = set_request_id()
        
        # Extract request details
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request start
        start_time = time.time()
        self.logger.info(
            "request_started",
            request_id=request_id,
            method=method,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log successful response
            self.logger.info(
                "request_completed",
                request_id=request_id,
                method=method,
                url=url,
                status_code=response.status_code,
                duration_seconds=duration,
            )
            
            # Log performance metric
            log_performance(
                self.logger,
                f"{method} {request.url.path}",
                duration,
                status_code=response.status_code,
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            log_error(
                self.logger,
                e,
                f"{method} {url}",
                request_id=request_id,
                duration_seconds=duration,
            )
            
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling and formatting errors."""
    
    def __init__(self, app):
        """Initialize error handling middleware."""
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process HTTP request with error handling.
        
        Args:
            request: HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response or error response
        """
        try:
            return await call_next(request)
            
        except RAGServiceError as e:
            # Handle custom RAG service errors
            self.logger.warning(
                "rag_service_error",
                error_code=e.error_code,
                error_message=e.message,
                error_details=e.details,
            )
            
            return JSONResponse(
                status_code=400,
                content=e.to_dict(),
            )
            
        except ValueError as e:
            # Handle validation errors
            self.logger.warning(
                "validation_error",
                error_message=str(e),
            )
            
            return JSONResponse(
                status_code=422,
                content={
                    "error": "VALIDATION_ERROR",
                    "message": str(e),
                    "details": {},
                },
            )
            
        except FileNotFoundError as e:
            # Handle file not found errors
            self.logger.warning(
                "file_not_found_error",
                error_message=str(e),
            )
            
            return JSONResponse(
                status_code=404,
                content={
                    "error": "FILE_NOT_FOUND",
                    "message": "Requested file not found",
                    "details": {"original_error": str(e)},
                },
            )
            
        except PermissionError as e:
            # Handle permission errors
            self.logger.warning(
                "permission_error",
                error_message=str(e),
            )
            
            return JSONResponse(
                status_code=403,
                content={
                    "error": "PERMISSION_DENIED",
                    "message": "Insufficient permissions",
                    "details": {"original_error": str(e)},
                },
            )
            
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(
                "unexpected_error",
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {
                        "error_type": type(e).__name__,
                    },
                },
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response.
        
        Args:
            request: HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        """Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests.
        
        Args:
            request: HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response or rate limit error
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Check rate limit
        current_time = time.time()
        minute_window = int(current_time // 60)
        
        # Clean old entries
        self.request_counts = {
            key: value for key, value in self.request_counts.items()
            if key[1] >= minute_window - 1
        }
        
        # Count requests for this IP in current window
        current_requests = sum(
            count for (ip, window), count in self.request_counts.items()
            if ip == client_ip and window == minute_window
        )
        
        if current_requests >= self.requests_per_minute:
            self.logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                current_requests=current_requests,
                limit=self.requests_per_minute,
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
                    "details": {
                        "current_requests": current_requests,
                        "limit": self.requests_per_minute,
                        "retry_after": 60,
                    },
                },
                headers={"Retry-After": "60"},
            )
        
        # Increment request count
        key = (client_ip, minute_window)
        self.request_counts[key] = self.request_counts.get(key, 0) + 1
        
        return await call_next(request)