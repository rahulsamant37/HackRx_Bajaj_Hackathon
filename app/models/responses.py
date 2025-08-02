"""Pydantic response models for API endpoints."""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    
    success: bool = Field(default=True, description="Request success status")
    message: Optional[str] = Field(default=None, description="Response message")
    timestamp: float = Field(description="Response timestamp")


class DocumentResponse(BaseModel):
    """Response model for document information."""
    
    id: str = Field(description="Document ID")
    filename: str = Field(description="Original filename")
    size: int = Field(description="File size in bytes")
    content_type: str = Field(description="MIME content type")
    upload_timestamp: float = Field(description="Upload timestamp")
    processing_status: str = Field(description="Processing status (pending, processing, completed, failed)")
    chunk_count: Optional[int] = Field(default=None, description="Number of chunks created")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")
    error_message: Optional[str] = Field(default=None, description="Error message if processing failed")


class ChunkResponse(BaseModel):
    """Response model for document chunk information."""
    
    id: str = Field(description="Chunk ID")
    document_id: str = Field(description="Parent document ID")
    content: str = Field(description="Chunk content")
    start_index: int = Field(description="Start position in original document")
    end_index: int = Field(description="End position in original document")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Chunk metadata")


class ProcessingStatusResponse(BaseResponse):
    """Response model for processing status."""
    
    document_id: str = Field(description="Document ID")
    status: str = Field(description="Processing status")
    progress: Optional[float] = Field(default=None, description="Processing progress (0.0-1.0)")
    steps_completed: Optional[int] = Field(default=None, description="Number of steps completed")
    total_steps: Optional[int] = Field(default=None, description="Total number of steps")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class DocumentListResponse(BaseResponse):
    """Response model for document list."""
    
    documents: List[DocumentResponse] = Field(description="List of documents")
    total_count: int = Field(description="Total number of documents")
    limit: int = Field(description="Request limit")
    offset: int = Field(description="Request offset")


class DocumentUploadResponse(BaseResponse):
    """Response model for document upload."""
    
    document_id: str = Field(description="Uploaded document ID")
    filename: str = Field(description="Original filename")
    size: int = Field(description="File size in bytes")
    status: str = Field(description="Initial processing status")


class DocumentDetailResponse(BaseResponse):
    """Response model for detailed document information."""
    
    document: DocumentResponse = Field(description="Document information")
    chunks: List[ChunkResponse] = Field(description="Document chunks")


class DeletionResponse(BaseResponse):
    """Response model for document deletion."""
    
    document_id: str = Field(description="Deleted document ID")
    chunks_deleted: int = Field(description="Number of chunks deleted")


class SearchResult(BaseModel):
    """Model for search result item."""
    
    document_id: str = Field(description="Source document ID")
    chunk_id: str = Field(description="Source chunk ID")
    content: str = Field(description="Matching content")
    score: float = Field(description="Similarity score")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Result metadata")


class AnswerResponse(BaseResponse):
    """Response model for question answering."""
    
    answer: str = Field(description="Generated answer")
    question: str = Field(description="Original question")
    sources: List[SearchResult] = Field(description="Source documents used")
    confidence: Optional[float] = Field(default=None, description="Answer confidence score")
    answer_id: str = Field(description="Unique answer ID for feedback")
    processing_time: float = Field(description="Processing time in seconds")
    token_usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage statistics")


class ChatResponse(BaseResponse):
    """Response model for chat conversation."""
    
    response: str = Field(description="Chat response")
    session_id: str = Field(description="Chat session ID")
    message_id: str = Field(description="Message ID")
    sources: List[SearchResult] = Field(description="Source documents used")
    conversation_length: int = Field(description="Number of messages in conversation")


class StreamingResponse(BaseModel):
    """Response model for streaming data."""
    
    type: str = Field(description="Stream event type")
    data: Union[str, Dict[str, Any]] = Field(description="Stream data")
    done: bool = Field(default=False, description="Stream completion status")


class HistoryResponse(BaseResponse):
    """Response model for conversation history."""
    
    session_id: str = Field(description="Session ID")
    messages: List[Dict[str, Any]] = Field(description="Conversation messages")
    total_messages: int = Field(description="Total messages in session")


class FeedbackResponse(BaseResponse):
    """Response model for feedback submission."""
    
    feedback_id: str = Field(description="Feedback record ID")
    answer_id: str = Field(description="Answer ID that was rated")
    rating: int = Field(description="Submitted rating")


class RAGStats(BaseModel):
    """Model for RAG system statistics."""
    
    total_documents: int = Field(description="Total number of documents")
    total_chunks: int = Field(description="Total number of chunks")
    vector_store_size: int = Field(description="Vector store size in bytes")
    total_queries: int = Field(description="Total number of queries processed")
    average_response_time: float = Field(description="Average response time in seconds")
    last_updated: float = Field(description="Last update timestamp")


class MetricsResponse(BaseResponse):
    """Response model for system metrics."""
    
    request_count: int = Field(description="Total request count")
    error_count: int = Field(description="Total error count")
    average_response_time: float = Field(description="Average response time")
    active_sessions: int = Field(description="Number of active sessions")
    system_resources: Dict[str, float] = Field(description="System resource usage")


class StatsResponse(BaseResponse):
    """Response model for system statistics."""
    
    rag_stats: RAGStats = Field(description="RAG system statistics")
    performance_metrics: Dict[str, Any] = Field(description="Performance metrics")
    usage_analytics: Dict[str, Any] = Field(description="Usage analytics")


class HealthResponse(BaseModel):
    """Response model for health checks."""
    
    status: str = Field(description="Health status (healthy, warning, unhealthy)")
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    timestamp: float = Field(description="Health check timestamp")
    environment: str = Field(description="Environment")


class DetailedHealthResponse(HealthResponse):
    """Response model for detailed health checks."""
    
    checks: Dict[str, Dict[str, Any]] = Field(description="Individual health checks")


class InfoResponse(BaseModel):
    """Response model for service information."""
    
    service: Dict[str, str] = Field(description="Service information")
    configuration: Dict[str, Any] = Field(description="Non-sensitive configuration")
    api: Dict[str, Optional[str]] = Field(description="API endpoints")
    system: Dict[str, str] = Field(description="System information")