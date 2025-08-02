"""Question-Answering API endpoints."""

import uuid
import json
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.api.deps import (
    get_rag_service,
    get_current_user,
    validate_search_params,
    query_rate_limit,
)
from app.models.requests import QuestionRequest, ChatRequest, FeedbackRequest, HistoryRequest
from app.models.responses import (
    AnswerResponse as AnswerResponseModel,
    ChatResponse,
    StreamingResponse as StreamingResponseModel,
    HistoryResponse,
    FeedbackResponse,
    BaseResponse,
)
from app.services.rag_service import RAGService, AnswerResponse
from app.utils.logger import get_logger, log_business_event, get_request_id
from app.utils.exceptions import RAGServiceError, ValidationError, GeminiAPIError

router = APIRouter()
logger = get_logger(__name__)

# In-memory storage for chat sessions and feedback (in production, use Redis/database)
chat_sessions = {}
answer_feedback = {}


@router.post(
    "/ask",
    response_model=AnswerResponseModel,
    summary="Ask a question",
    description="Ask a question and get an AI-generated answer based on uploaded documents."
)
async def ask_question(
    request: QuestionRequest,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: Optional[str] = Depends(get_current_user),
    _rate_limit: None = Depends(query_rate_limit),
):
    """Ask a question and get an answer from the RAG system."""
    try:
        logger.info(
            "question_asked",
            question_length=len(request.question),
            max_results=request.max_results,
            user=current_user,
            request_id=get_request_id()
        )
        
        # Get answer from RAG service
        answer = await rag_service.answer_question(
            question=request.question,
            max_results=request.max_results or 5,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        # Log business event
        log_business_event(
            logger,
            "question_answered",
            {
                "answer_id": answer.answer_id,
                "question_length": len(request.question),
                "answer_length": len(answer.answer),
                "source_count": len(answer.sources),
                "processing_time": answer.processing_time,
                "user": current_user,
            }
        )
        
        # Convert to response model
        return AnswerResponseModel(
            success=True,
            message="Question answered successfully",
            timestamp=datetime.now().timestamp(),
            answer=answer.answer,
            question=answer.question,
            sources=[source.to_dict() for source in answer.sources],
            confidence=answer.confidence,
            answer_id=answer.answer_id,
            processing_time=answer.processing_time,
            token_usage=answer.token_usage,
        )
        
    except (ValidationError, RAGServiceError, GeminiAPIError) as e:
        logger.warning("question_answering_error", error=str(e), question=request.question[:100])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("unexpected_question_error", error=str(e), question=request.question[:100])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.post(
    "/ask/stream",
    summary="Ask a question with streaming response",
    description="Ask a question and receive a streaming response for real-time answer generation."
)
async def ask_question_stream(
    request: QuestionRequest,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: Optional[str] = Depends(get_current_user),
    _rate_limit: None = Depends(query_rate_limit),
):
    """Ask a question with streaming response."""
    
    async def generate_streaming_response() -> AsyncGenerator[str, None]:
        """Generate streaming response events."""
        answer_id = str(uuid.uuid4())
        
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'answer_id': answer_id, 'question': request.question})}\\n\\n"
            
            # Search for context
            yield f"data: {json.dumps({'type': 'status', 'message': 'Searching for relevant context...'})}\\n\\n"
            
            search_results = await rag_service.search_similar(
                request.question, 
                k=request.max_results or 5
            )
            
            yield f"data: {json.dumps({'type': 'sources_found', 'count': len(search_results)})}\\n\\n"
            
            # For streaming, we would need to modify the RAG service to support streaming
            # For now, get the complete answer and simulate streaming
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating answer...'})}\\n\\n"
            
            answer = await rag_service.answer_question(
                question=request.question,
                max_results=request.max_results or 5,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            
            # Simulate streaming by sending answer in chunks
            words = answer.answer.split()
            current_text = ""
            
            for i, word in enumerate(words):
                current_text += word + " "
                if i % 5 == 0 or i == len(words) - 1:  # Send every 5 words or at the end
                    yield f"data: {json.dumps({'type': 'answer_chunk', 'text': current_text.strip()})}\\n\\n"
            
            # Send final response with complete data
            final_response = {
                'type': 'complete',
                'answer_id': answer.answer_id,
                'answer': answer.answer,
                'sources': [source.to_dict() for source in answer.sources],
                'confidence': answer.confidence,
                'processing_time': answer.processing_time,
                'token_usage': answer.token_usage,
            }
            
            yield f"data: {json.dumps(final_response)}\\n\\n"
            
            # Log business event
            log_business_event(
                logger,
                "streaming_question_answered",
                {
                    "answer_id": answer.answer_id,
                    "question_length": len(request.question),
                    "answer_length": len(answer.answer),
                    "source_count": len(answer.sources),
                    "user": current_user,
                }
            )
            
        except Exception as e:
            logger.error("streaming_question_error", error=str(e), answer_id=answer_id)
            error_response = {
                'type': 'error',
                'error': str(e),
                'answer_id': answer_id
            }
            yield f"data: {json.dumps(error_response)}\\n\\n"
    
    return EventSourceResponse(generate_streaming_response())


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat conversation",
    description="Engage in a conversational Q&A with memory of previous messages."
)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: Optional[str] = Depends(get_current_user),
    _rate_limit: None = Depends(query_rate_limit),
):
    """Engage in conversational Q&A with session memory."""
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "user": current_user,
            }
        
        session = chat_sessions[session_id]
        
        # Add user message to session
        user_message = {
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat(),
        }
        session["messages"].append(user_message)
        
        # For conversational context, we could enhance the question with previous messages
        # For now, treat each message independently
        enhanced_question = request.message
        
        # Get answer from RAG service
        answer = await rag_service.answer_question(
            question=enhanced_question,
            max_results=request.max_results or 5,
            temperature=request.temperature,
        )
        
        # Add assistant message to session
        assistant_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": answer.answer,
            "timestamp": datetime.now().isoformat(),
            "sources": [source.to_dict() for source in answer.sources],
            "confidence": answer.confidence,
        }
        session["messages"].append(assistant_message)
        
        # Update session
        session["last_updated"] = datetime.now().isoformat()
        
        # Log business event
        log_business_event(
            logger,
            "chat_message_processed",
            {
                "session_id": session_id,
                "message_length": len(request.message),
                "response_length": len(answer.answer),
                "conversation_length": len(session["messages"]),
                "user": current_user,
            }
        )
        
        return ChatResponse(
            success=True,
            message="Chat response generated",
            timestamp=datetime.now().timestamp(),
            response=answer.answer,
            session_id=session_id,
            message_id=assistant_message["id"],
            sources=[source.to_dict() for source in answer.sources],
            conversation_length=len(session["messages"]),
        )
        
    except Exception as e:
        logger.error("chat_error", error=str(e), session_id=request.session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get(
    "/history/{session_id}",
    response_model=HistoryResponse,
    summary="Get conversation history",
    description="Retrieve the conversation history for a specific chat session."
)
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[str] = Depends(get_current_user),
):
    """Get conversation history for a session."""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session not found: {session_id}"
            )
        
        session = chat_sessions[session_id]
        
        # Check if user has access to this session (simple check)
        if current_user and session.get("user") != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        # Apply pagination
        messages = session["messages"]
        total_messages = len(messages)
        paginated_messages = messages[offset:offset + limit]
        
        return HistoryResponse(
            success=True,
            message="Conversation history retrieved",
            timestamp=datetime.now().timestamp(),
            session_id=session_id,
            messages=paginated_messages,
            total_messages=total_messages,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_history_error", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation history: {str(e)}"
        )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit answer feedback",
    description="Provide feedback (rating and comments) on an answer to help improve the system."
)
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: Optional[str] = Depends(get_current_user),
):
    """Submit feedback for an answer."""
    try:
        feedback_id = str(uuid.uuid4())
        
        # Store feedback
        feedback_record = {
            "id": feedback_id,
            "answer_id": feedback.answer_id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "user": current_user,
            "timestamp": datetime.now().isoformat(),
        }
        
        answer_feedback[feedback_id] = feedback_record
        
        # Log business event
        log_business_event(
            logger,
            "feedback_submitted",
            {
                "feedback_id": feedback_id,
                "answer_id": feedback.answer_id,
                "rating": feedback.rating,
                "has_comment": bool(feedback.comment),
                "user": current_user,
            }
        )
        
        return FeedbackResponse(
            success=True,
            message="Feedback submitted successfully",
            timestamp=datetime.now().timestamp(),
            feedback_id=feedback_id,
            answer_id=feedback.answer_id,
            rating=feedback.rating,
        )
        
    except Exception as e:
        logger.error("submit_feedback_error", error=str(e), answer_id=feedback.answer_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get(
    "/sessions",
    summary="List chat sessions",
    description="Get a list of chat sessions for the current user."
)
async def list_chat_sessions(
    current_user: Optional[str] = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    """List chat sessions for the current user."""
    try:
        # Filter sessions by user
        user_sessions = []
        
        for session_id, session_data in chat_sessions.items():
            if current_user and session_data.get("user") == current_user:
                # Get last message for preview
                last_message = session_data["messages"][-1] if session_data["messages"] else None
                
                session_summary = {
                    "session_id": session_id,
                    "created_at": session_data.get("created_at"),
                    "last_updated": session_data.get("last_updated"),
                    "message_count": len(session_data["messages"]),
                    "last_message_preview": last_message["content"][:100] + "..." if last_message and len(last_message["content"]) > 100 else last_message["content"] if last_message else None,
                }
                user_sessions.append(session_summary)
        
        # Sort by last updated (most recent first)
        user_sessions.sort(key=lambda x: x.get("last_updated", x.get("created_at", "")), reverse=True)
        
        # Apply pagination
        total_sessions = len(user_sessions)
        paginated_sessions = user_sessions[offset:offset + limit]
        
        return {
            "success": True,
            "message": f"Retrieved {len(paginated_sessions)} chat sessions",
            "timestamp": datetime.now().timestamp(),
            "sessions": paginated_sessions,
            "total_count": total_sessions,
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        logger.error("list_sessions_error", error=str(e), user=current_user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chat sessions: {str(e)}"
        )


@router.delete(
    "/sessions/{session_id}",
    summary="Delete chat session",
    description="Delete a chat session and all its messages."
)
async def delete_chat_session(
    session_id: str,
    current_user: Optional[str] = Depends(get_current_user),
):
    """Delete a chat session."""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session not found: {session_id}"
            )
        
        session = chat_sessions[session_id]
        
        # Check if user has access to this session
        if current_user and session.get("user") != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        # Delete session
        message_count = len(session["messages"])
        del chat_sessions[session_id]
        
        # Log business event
        log_business_event(
            logger,
            "chat_session_deleted",
            {
                "session_id": session_id,
                "message_count": message_count,
                "user": current_user,
            }
        )
        
        return {
            "success": True,
            "message": "Chat session deleted successfully",
            "timestamp": datetime.now().timestamp(),
            "session_id": session_id,
            "messages_deleted": message_count,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_session_error", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat session: {str(e)}"
        )