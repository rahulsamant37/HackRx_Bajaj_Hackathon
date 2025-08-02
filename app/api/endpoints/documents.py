"""Document management API endpoints."""

import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.responses import JSONResponse

from app.api.deps import (
    get_document_processor,
    get_rag_service,
    get_current_user,
    validate_file_upload,
    save_upload_file,
    cleanup_temp_file,
    validate_pagination,
    upload_rate_limit,
)
from app.models.requests import DocumentUploadRequest, DocumentSearchRequest, ReprocessingRequest
from app.models.responses import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DeletionResponse,
    ProcessingStatusResponse,
    BaseResponse,
)
from app.services.document_service import DocumentProcessor
from app.services.rag_service import RAGService
from app.utils.logger import get_logger, log_business_event, get_request_id
from app.utils.exceptions import DocumentProcessingError, VectorStoreError, ValidationError

router = APIRouter()
logger = get_logger(__name__)

# In-memory storage for processing status (in production, use Redis or database)
processing_status = {}


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process document",
    description="Upload a document file and process it for RAG system. Supports PDF, TXT, DOCX, and MD files."
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to upload"),
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    metadata: Optional[str] = None,  # JSON string for additional metadata
    document_processor: DocumentProcessor = Depends(get_document_processor),
    rag_service: RAGService = Depends(get_rag_service),
    current_user: Optional[str] = Depends(get_current_user),
    _rate_limit: None = Depends(upload_rate_limit),
):
    """Upload and process document for RAG system."""
    # Validate file
    validated_file = validate_file_upload(file)
    
    # Save file temporarily
    temp_file_path = await save_upload_file(validated_file)
    
    try:
        # Parse additional metadata if provided
        additional_metadata = {}
        if metadata:
            try:
                import json
                additional_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in metadata field"
                )
        
        # Add user info to metadata
        if current_user:
            additional_metadata["uploaded_by"] = current_user
        additional_metadata["upload_timestamp"] = datetime.now().isoformat()
        additional_metadata["request_id"] = get_request_id()
        
        # Start processing in background
        document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(file.filename) % 10000:04d}"
        
        # Set initial processing status
        processing_status[document_id] = {
            "status": "processing",
            "progress": 0.0,
            "steps_completed": 0,
            "total_steps": 3,  # process file, create embeddings, add to vector store
            "started_at": datetime.now().isoformat(),
            "filename": file.filename,
        }
        
        # Schedule background processing
        background_tasks.add_task(
            process_document_background,
            document_id,
            temp_file_path,
            file.filename,
            file.content_type or "application/octet-stream",
            chunk_size,
            chunk_overlap,
            additional_metadata,
            document_processor,
            rag_service,
        )
        
        # Log business event
        log_business_event(
            logger,
            "document_upload_started",
            {
                "document_id": document_id,
                "filename": file.filename,
                "file_size": getattr(file, 'size', 0),
                "user": current_user,
            }
        )
        
        return DocumentUploadResponse(
            success=True,
            message="Document upload started. Processing in background.",
            timestamp=datetime.now().timestamp(),
            document_id=document_id,
            filename=file.filename,
            size=getattr(file, 'size', 0),
            status="processing",
        )
        
    except HTTPException:
        # Clean up temp file on validation errors
        cleanup_temp_file(temp_file_path)
        raise
    except Exception as e:
        # Clean up temp file on unexpected errors
        cleanup_temp_file(temp_file_path)
        logger.error("document_upload_error", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start document processing: {str(e)}"
        )


async def process_document_background(
    document_id: str,
    temp_file_path: str,
    filename: str,
    content_type: str,
    chunk_size: Optional[int],
    chunk_overlap: Optional[int],
    metadata: Dict[str, Any],
    document_processor: DocumentProcessor,
    rag_service: RAGService,
):
    """Background task for processing documents."""
    try:
        logger.info("background_processing_started", document_id=document_id, filename=filename)
        
        # Step 1: Process document
        processing_status[document_id].update({
            "status": "processing",
            "progress": 0.1,
            "steps_completed": 0,
            "current_step": "Processing document content"
        })
        
        processed_doc = await document_processor.process_file(
            temp_file_path,
            chunk_size,
            chunk_overlap,
            metadata
        )
        
        # Update document ID to match our generated one
        processed_doc.id = document_id
        
        # Step 2: Create embeddings and add to vector store
        processing_status[document_id].update({
            "progress": 0.5,
            "steps_completed": 1,
            "current_step": "Creating embeddings"
        })
        
        await rag_service.add_document(processed_doc)
        
        # Step 3: Complete
        processing_status[document_id].update({
            "status": "completed",
            "progress": 1.0,
            "steps_completed": 3,
            "current_step": "Processing complete",
            "completed_at": datetime.now().isoformat(),
            "chunk_count": len(processed_doc.chunks),
        })
        
        logger.info(
            "background_processing_completed",
            document_id=document_id,
            chunk_count=len(processed_doc.chunks)
        )
        
        # Log business event
        log_business_event(
            logger,
            "document_processed_successfully",
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_count": len(processed_doc.chunks),
            }
        )
        
    except Exception as e:
        # Update status with error
        processing_status[document_id].update({
            "status": "failed",
            "error_message": str(e),
            "failed_at": datetime.now().isoformat(),
        })
        
        logger.error(
            "background_processing_failed",
            document_id=document_id,
            filename=filename,
            error=str(e)
        )
        
        # Log business event
        log_business_event(
            logger,
            "document_processing_failed",
            {
                "document_id": document_id,
                "filename": filename,
                "error": str(e),
            }
        )
    
    finally:
        # Always clean up temp file
        cleanup_temp_file(temp_file_path)


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List documents",
    description="Retrieve a list of uploaded documents with pagination support."
)
async def list_documents(
    limit: int = 10,
    offset: int = 0,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: Optional[str] = Depends(get_current_user),
):
    """List uploaded documents with pagination."""
    # Validate pagination parameters
    limit, offset = validate_pagination(limit, offset)
    
    try:
        # Get system stats to understand what documents exist
        stats = rag_service.get_stats()
        
        # For now, return basic information from processing status
        # In production, this would come from a proper database
        documents = []
        all_docs = list(processing_status.items())
        
        # Apply pagination
        paginated_docs = all_docs[offset:offset + limit]
        
        for doc_id, status_info in paginated_docs:
            # Create basic document response
            doc_response = {
                "id": doc_id,
                "filename": status_info.get("filename", ""),
                "size": 0,  # Would be stored in database
                "content_type": "application/octet-stream",
                "upload_timestamp": datetime.fromisoformat(status_info.get("started_at", datetime.now().isoformat())).timestamp(),
                "processing_status": status_info.get("status", "unknown"),
                "chunk_count": status_info.get("chunk_count"),
                "metadata": {},
                "error_message": status_info.get("error_message"),
            }
            documents.append(doc_response)
        
        return DocumentListResponse(
            success=True,
            message=f"Retrieved {len(documents)} documents",
            timestamp=datetime.now().timestamp(),
            documents=documents,
            total_count=len(all_docs),
            limit=limit,
            offset=offset,
        )
        
    except Exception as e:
        logger.error("list_documents_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
    description="Retrieve detailed information about a specific document including its chunks."
)
async def get_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: Optional[str] = Depends(get_current_user),
):
    """Get detailed document information."""
    try:
        # Check if document exists in processing status
        if document_id not in processing_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        status_info = processing_status[document_id]
        
        # For a complete implementation, this would fetch from a database
        # For now, return basic information
        document_info = {
            "id": document_id,
            "filename": status_info.get("filename", ""),
            "size": 0,
            "content_type": "application/octet-stream",
            "upload_timestamp": datetime.fromisoformat(status_info.get("started_at", datetime.now().isoformat())).timestamp(),
            "processing_status": status_info.get("status", "unknown"),
            "chunk_count": status_info.get("chunk_count"),
            "metadata": {},
            "error_message": status_info.get("error_message"),
        }
        
        # Return empty chunks list for now (would fetch from database)
        chunks = []
        
        return DocumentDetailResponse(
            success=True,
            message="Document details retrieved",
            timestamp=datetime.now().timestamp(),
            document=document_info,
            chunks=chunks,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_document_error", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete(
    "/{document_id}",
    response_model=DeletionResponse,
    summary="Delete document",
    description="Remove a document and all its chunks from the system."
)
async def delete_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: Optional[str] = Depends(get_current_user),
):
    """Delete document from the system."""
    try:
        # Check if document exists
        if document_id not in processing_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # Delete from vector store
        deleted = await rag_service.delete_document(document_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found in vector store: {document_id}"
            )
        
        # Remove from processing status
        status_info = processing_status.pop(document_id, {})
        chunks_deleted = status_info.get("chunk_count", 0)
        
        # Log business event
        log_business_event(
            logger,
            "document_deleted",
            {
                "document_id": document_id,
                "chunks_deleted": chunks_deleted,
                "user": current_user,
            }
        )
        
        return DeletionResponse(
            success=True,
            message="Document deleted successfully",
            timestamp=datetime.now().timestamp(),
            document_id=document_id,
            chunks_deleted=chunks_deleted,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_document_error", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get(
    "/{document_id}/status",
    response_model=ProcessingStatusResponse,
    summary="Get processing status",
    description="Check the processing status of an uploaded document."
)
async def get_processing_status(
    document_id: str,
    current_user: Optional[str] = Depends(get_current_user),
):
    """Get document processing status."""
    try:
        if document_id not in processing_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        status_info = processing_status[document_id]
        
        return ProcessingStatusResponse(
            success=True,
            message="Processing status retrieved",
            timestamp=datetime.now().timestamp(),
            document_id=document_id,
            status=status_info.get("status", "unknown"),
            progress=status_info.get("progress"),
            steps_completed=status_info.get("steps_completed"),
            total_steps=status_info.get("total_steps"),
            error_message=status_info.get("error_message"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_processing_status_error", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve processing status: {str(e)}"
        )


@router.post(
    "/{document_id}/reprocess",
    response_model=ProcessingStatusResponse,
    summary="Reprocess document",
    description="Reprocess an existing document with new chunking parameters."
)
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    request: ReprocessingRequest,
    document_processor: DocumentProcessor = Depends(get_document_processor),
    rag_service: RAGService = Depends(get_rag_service),
    current_user: Optional[str] = Depends(get_current_user),
):
    """Reprocess document with new parameters."""
    try:
        # Check if document exists
        if document_id not in processing_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # For a complete implementation, we would:
        # 1. Retrieve original file from storage
        # 2. Delete existing document from vector store
        # 3. Reprocess with new parameters
        # 4. Add back to vector store
        
        # For now, return that reprocessing is not fully implemented
        return ProcessingStatusResponse(
            success=False,
            message="Reprocessing feature not fully implemented yet",
            timestamp=datetime.now().timestamp(),
            document_id=document_id,
            status="error",
            error_message="Reprocessing requires persistent file storage implementation",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("reprocess_document_error", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess document: {str(e)}"
        )