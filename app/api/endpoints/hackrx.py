"""HackRx endpoint for document processing and Q&A."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.requests import HackRxRequest
from app.models.responses import HackRxResponse
from app.services.url_document_service import URLDocumentService
from app.api.deps import verify_api_key
from app.utils.logger import get_logger
from app.utils.exceptions import DocumentProcessingError


router = APIRouter()
logger = get_logger(__name__)


@router.post("/run", response_model=HackRxResponse)
async def hackrx_run(
    request: HackRxRequest,
    user: str = Depends(verify_api_key),
) -> HackRxResponse:
    """Process document from URL and answer questions.
    
    This endpoint downloads a document from the provided URL,
    processes it through the RAG system, and answers the given questions.
    
    Args:
        request: HackRx request with document URL and questions
        user: Authenticated user (from API key)
        
    Returns:
        HackRx response with answers
        
    Raises:
        HTTPException: If processing fails
    """
    logger.info(
        f"HackRx request received",
        extra={
            "user": user,
            "document_url": request.documents,
            "question_count": len(request.questions),
            "questions": request.questions[:3]  # Log first 3 questions only
        }
    )
    
    try:
        # Initialize URL document service
        url_service = URLDocumentService()
        
        # Process document and answer questions
        answers = await url_service.process_and_answer_questions(
            url=request.documents,
            questions=request.questions
        )
        
        logger.info(
            f"HackRx request completed successfully",
            extra={
                "user": user,
                "document_url": request.documents,
                "answers_count": len(answers)
            }
        )
        
        return HackRxResponse(answers=answers)
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document processing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in HackRx endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )


@router.get("/health")
async def hackrx_health():
    """Health check for HackRx endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "endpoint": "hackrx",
        "message": "HackRx endpoint is operational"
    }
