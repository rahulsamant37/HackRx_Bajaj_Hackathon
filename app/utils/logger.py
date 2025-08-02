"""Structured logging utilities for the RAG Q&A system."""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

import structlog

from app.config import get_settings

# Context variable for request ID tracking
request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def add_request_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request ID to log events."""
    request_id = request_id_context.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp to log events."""
    import time
    event_dict["timestamp"] = time.time()
    return event_dict


def setup_logging() -> None:
    """Set up structured logging configuration."""
    settings = get_settings()
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(message)s",
        stream=sys.stdout,
    )
    
    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        add_timestamp,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    # Add format-specific processors
    if settings.log_format == "json":
        processors.extend([
            structlog.processors.JSONRenderer()
        ])
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request ID in context.
    
    Args:
        request_id: Request ID to set, generates one if None
        
    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_context.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get current request ID from context.
    
    Returns:
        Current request ID or None
    """
    return request_id_context.get()


def log_performance(
    logger: structlog.BoundLogger,
    operation: str,
    duration: float,
    **kwargs: Any,
) -> None:
    """Log performance metrics.
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        **kwargs: Additional context
    """
    logger.info(
        "performance_metric",
        operation=operation,
        duration_seconds=duration,
        **kwargs,
    )


def log_error(
    logger: structlog.BoundLogger,
    error: Exception,
    operation: str,
    **kwargs: Any,
) -> None:
    """Log error with context.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        operation: Operation that failed
        **kwargs: Additional context
    """
    logger.error(
        "operation_failed",
        operation=operation,
        error_type=type(error).__name__,
        error_message=str(error),
        **kwargs,
        exc_info=True,
    )


def log_business_event(
    logger: structlog.BoundLogger,
    event_type: str,
    event_data: Dict[str, Any],
    **kwargs: Any,
) -> None:
    """Log business events for analytics.
    
    Args:
        logger: Logger instance
        event_type: Type of business event
        event_data: Event data
        **kwargs: Additional context
    """
    logger.info(
        "business_event",
        event_type=event_type,
        event_data=event_data,
        **kwargs,
    )


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__module__)


# Performance timing decorator
def log_execution_time(operation: str):
    """Decorator to log execution time of functions.
    
    Args:
        operation: Name of the operation being timed
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            import time
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance(logger, operation, duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_performance(logger, operation, duration, success=False)
                log_error(logger, e, operation)
                raise
        
        def sync_wrapper(*args, **kwargs):
            import time
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance(logger, operation, duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_performance(logger, operation, duration, success=False)
                log_error(logger, e, operation)
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator