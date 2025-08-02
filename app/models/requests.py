"""Pydantic request models for API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ValidationInfo


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    
    chunk_size: Optional[int] = Field(
        default=None,
        description="Custom chunk size for document processing",
        gt=0,
        le=5000,
    )
    chunk_overlap: Optional[int] = Field(
        default=None,
        description="Custom chunk overlap for document processing",
        ge=0,
        le=1000,
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for the document",
    )
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate chunk overlap is less than chunk size."""
        if v is not None and info.data.get("chunk_size") is not None:
            if v >= info.data["chunk_size"]:
                raise ValueError("Chunk overlap must be less than chunk size")
        return v


class ChunkingConfigRequest(BaseModel):
    """Request model for document chunking configuration."""
    
    chunk_size: int = Field(
        default=1000,
        description="Size of text chunks",
        gt=0,
        le=5000,
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks",
        ge=0,
        le=1000,
    )
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info: ValidationInfo) -> int:
        """Validate chunk overlap is less than chunk size."""
        if v >= info.data["chunk_size"]:
            raise ValueError("Chunk overlap must be less than chunk size")
        return v


class DocumentDeleteRequest(BaseModel):
    """Request model for document deletion."""
    
    document_id: str = Field(
        ...,
        description="ID of the document to delete",
        min_length=1,
    )


class DocumentSearchRequest(BaseModel):
    """Request model for document search."""
    
    query: Optional[str] = Field(
        default=None,
        description="Search query",
        max_length=1000,
    )
    limit: Optional[int] = Field(
        default=10,
        description="Maximum number of results",
        gt=0,
        le=100,
    )
    offset: Optional[int] = Field(
        default=0,
        description="Number of results to skip",
        ge=0,
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Search filters",
    )


class ReprocessingRequest(BaseModel):
    """Request model for document reprocessing."""
    
    chunk_size: Optional[int] = Field(
        default=None,
        description="New chunk size for reprocessing",
        gt=0,
        le=5000,
    )
    chunk_overlap: Optional[int] = Field(
        default=None,
        description="New chunk overlap for reprocessing",
        ge=0,
        le=1000,
    )
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate chunk overlap is less than chunk size."""
        if v is not None and info.data.get("chunk_size") is not None:
            if v >= info.data["chunk_size"]:
                raise ValueError("Chunk overlap must be less than chunk size")
        return v


class QuestionRequest(BaseModel):
    """Request model for question asking."""
    
    question: str = Field(
        ...,
        description="Question to ask",
        min_length=1,
        max_length=1000,
    )
    max_results: Optional[int] = Field(
        default=5,
        description="Maximum number of context documents to use",
        gt=0,
        le=20,
    )
    temperature: Optional[float] = Field(
        default=None,
        description="Response creativity (0.0-2.0)",
        ge=0.0,
        le=2.0,
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens in response",
        gt=0,
        le=4000,
    )
    include_sources: Optional[bool] = Field(
        default=True,
        description="Include source documents in response",
    )


class ChatRequest(BaseModel):
    """Request model for conversational chat."""
    
    message: str = Field(
        ...,
        description="Chat message",
        min_length=1,
        max_length=1000,
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Chat session ID",
    )
    max_results: Optional[int] = Field(
        default=5,
        description="Maximum number of context documents to use",
        gt=0,
        le=20,
    )
    temperature: Optional[float] = Field(
        default=None,
        description="Response creativity (0.0-2.0)",
        ge=0.0,
        le=2.0,
    )


class FeedbackRequest(BaseModel):
    """Request model for answer feedback."""
    
    answer_id: str = Field(
        ...,
        description="ID of the answer being rated",
        min_length=1,
    )
    rating: int = Field(
        ...,
        description="Rating (1-5 stars)",
        ge=1,
        le=5,
    )
    comment: Optional[str] = Field(
        default=None,
        description="Optional feedback comment",
        max_length=1000,
    )


class HistoryRequest(BaseModel):
    """Request model for conversation history."""
    
    session_id: str = Field(
        ...,
        description="Chat session ID",
        min_length=1,
    )
    limit: Optional[int] = Field(
        default=50,
        description="Maximum number of messages to return",
        gt=0,
        le=1000,
    )
    offset: Optional[int] = Field(
        default=0,
        description="Number of messages to skip",
        ge=0,
    )