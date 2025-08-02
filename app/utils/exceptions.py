"""Custom exception classes for the RAG Q&A system."""

from typing import Any, Dict, Optional


class RAGServiceError(Exception):
    """Base exception for RAG service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "RAG_SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize RAG service error.
        
        Args:
            message: Error message
            error_code: Unique error code
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class DocumentProcessingError(RAGServiceError):
    """Exception raised during document processing."""
    
    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize document processing error.
        
        Args:
            message: Error message
            filename: Name of the file that caused the error
            details: Additional error details
        """
        error_details = details or {}
        if filename:
            error_details["filename"] = filename
        
        super().__init__(
            message=message,
            error_code="DOCUMENT_PROCESSING_ERROR",
            details=error_details,
        )


class EmbeddingError(RAGServiceError):
    """Exception raised during embedding generation."""
    
    def __init__(
        self,
        message: str,
        text_length: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize embedding error.
        
        Args:
            message: Error message
            text_length: Length of text that caused the error
            details: Additional error details
        """
        error_details = details or {}
        if text_length is not None:
            error_details["text_length"] = text_length
        
        super().__init__(
            message=message,
            error_code="EMBEDDING_ERROR",
            details=error_details,
        )


class VectorStoreError(RAGServiceError):
    """Exception raised during vector store operations."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize vector store error.
        
        Args:
            message: Error message
            operation: Vector store operation that failed
            details: Additional error details
        """
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="VECTOR_STORE_ERROR",
            details=error_details,
        )


class GeminiAPIError(RAGServiceError):
    """Exception raised during Google Gemini API interactions."""
    
    def __init__(
        self,
        message: str,
        api_endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Gemini API error.
        
        Args:
            message: Error message
            api_endpoint: API endpoint that failed
            status_code: HTTP status code
            details: Additional error details
        """
        error_details = details or {}
        if api_endpoint:
            error_details["api_endpoint"] = api_endpoint
        if status_code:
            error_details["status_code"] = status_code
        
        super().__init__(
            message=message,
            error_code="GEMINI_API_ERROR",
            details=error_details,
        )


class GeminiAPIError(RAGServiceError):
    """Exception raised during Google Gemini API interactions."""
    
    def __init__(
        self,
        message: str,
        api_endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Gemini API error.
        
        Args:
            message: Error message
            api_endpoint: API endpoint that failed
            status_code: HTTP status code
            details: Additional error details
        """
        error_details = details or {}
        if api_endpoint:
            error_details["api_endpoint"] = api_endpoint
        if status_code:
            error_details["status_code"] = status_code
        
        super().__init__(
            message=message,
            error_code="GEMINI_API_ERROR",
            details=error_details,
        )


class ValidationError(RAGServiceError):
    """Exception raised during data validation."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Value that failed validation
            details: Additional error details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=error_details,
        )


class AuthenticationError(RAGServiceError):
    """Exception raised during authentication."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize authentication error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationError(RAGServiceError):
    """Exception raised during authorization."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize authorization error.
        
        Args:
            message: Error message
            required_permission: Required permission that was missing
            details: Additional error details
        """
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission
        
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=error_details,
        )


class RateLimitError(RAGServiceError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        error_details = details or {}
        if retry_after is not None:
            error_details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=error_details,
        )