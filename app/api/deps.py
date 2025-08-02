"""API dependencies for dependency injection."""

import tempfile
import os
from typing import Generator, Optional
from functools import lru_cache

from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings
from app.services.document_service import DocumentProcessor
from app.services.rag_service import RAGService
from app.utils.logger import get_logger
from app.utils.exceptions import ValidationError

# Initialize security scheme
security = HTTPBearer(auto_error=False)
logger = get_logger(__name__)


@lru_cache()
def get_document_processor() -> DocumentProcessor:
    """Get document processor instance.
    
    Returns:
        DocumentProcessor instance
    """
    return DocumentProcessor()


@lru_cache()
def get_rag_service() -> RAGService:
    """Get RAG service instance.
    
    Returns:
        RAGService instance
    """
    return RAGService()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Get current user from authorization header.
    
    Args:
        credentials: Authorization credentials
        
    Returns:
        User identifier or None for now (simplified auth)
        
    Note:
        This is a simplified implementation. In production, you would
        validate JWT tokens and return actual user information.
    """
    # For now, return a default user if credentials are provided
    # In production, implement proper JWT validation
    if credentials:
        return "default_user"
    return None


def validate_file_upload(file: UploadFile) -> UploadFile:
    """Validate uploaded file.
    
    Args:
        file: Uploaded file
        
    Returns:
        Validated file
        
    Raises:
        HTTPException: If file validation fails
    """
    settings = get_settings()
    
    # Check if file is provided
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}. "
                   f"Supported types: {', '.join(settings.supported_extensions)}"
        )
    
    # Check file size (if available)
    if hasattr(file, 'size') and file.size:
        if file.size > settings.max_file_size:
            max_size_mb = settings.max_file_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_size_mb}MB"
            )
    
    return file


async def save_upload_file(file: UploadFile) -> str:
    """Save uploaded file to temporary location.
    
    Args:
        file: Uploaded file
        
    Returns:
        Path to saved temporary file
        
    Raises:
        HTTPException: If file saving fails
    """
    try:
        # Create temporary file with original extension
        file_extension = os.path.splitext(file.filename)[1]
        
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=file_extension,
            prefix="upload_"
        ) as temp_file:
            # Read and write file content
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            
            # Reset file pointer for potential reuse
            await file.seek(0)
            
            logger.info(
                "file_saved_temporarily",
                filename=file.filename,
                temp_path=temp_file.name,
                size=len(content)
            )
            
            return temp_file.name
            
    except Exception as e:
        logger.error("file_save_error", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )


def cleanup_temp_file(file_path: str) -> None:
    """Clean up temporary file.
    
    Args:
        file_path: Path to temporary file
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.debug("temp_file_cleaned", file_path=file_path)
    except Exception as e:
        logger.warning("temp_file_cleanup_error", file_path=file_path, error=str(e))


def validate_pagination(
    limit: int = 10,
    offset: int = 0
) -> tuple[int, int]:
    """Validate pagination parameters.
    
    Args:
        limit: Number of items per page
        offset: Number of items to skip
        
    Returns:
        Validated (limit, offset) tuple
        
    Raises:
        HTTPException: If parameters are invalid
    """
    if limit <= 0 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )
    
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be non-negative"
        )
    
    return limit, offset


def validate_search_params(
    query: Optional[str] = None,
    max_results: int = 5
) -> tuple[Optional[str], int]:
    """Validate search parameters.
    
    Args:
        query: Search query
        max_results: Maximum results to return
        
    Returns:
        Validated (query, max_results) tuple
        
    Raises:
        HTTPException: If parameters are invalid
    """
    if query is not None and len(query.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    if max_results <= 0 or max_results > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_results must be between 1 and 20"
        )
    
    return query, max_results


class RateLimitDependency:
    """Rate limiting dependency for specific endpoints."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """Initialize rate limit dependency.
        
        Args:
            max_requests: Maximum requests in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_history = {}  # Simple in-memory storage
    
    def __call__(self, user: Optional[str] = Depends(get_current_user)) -> None:
        """Check rate limit for user.
        
        Args:
            user: Current user (or IP-based identifier)
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        import time
        
        # Use user ID or default identifier
        identifier = user or "anonymous"
        current_time = time.time()
        
        # Clean old entries
        self.request_history = {
            key: timestamps for key, timestamps in self.request_history.items()
            if any(ts > current_time - self.window_seconds for ts in timestamps)
        }
        
        # Get request history for this identifier
        user_requests = self.request_history.get(identifier, [])
        
        # Filter to current window
        recent_requests = [
            ts for ts in user_requests 
            if ts > current_time - self.window_seconds
        ]
        
        # Check limit
        if len(recent_requests) >= self.max_requests:
            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                requests_in_window=len(recent_requests),
                limit=self.max_requests
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds.",
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Add current request
        recent_requests.append(current_time)
        self.request_history[identifier] = recent_requests


# Pre-configured rate limiters for different endpoints
upload_rate_limit = RateLimitDependency(max_requests=5, window_seconds=300)  # 5 uploads per 5 minutes
query_rate_limit = RateLimitDependency(max_requests=30, window_seconds=60)   # 30 queries per minute