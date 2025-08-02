"""Tests for Q&A API endpoints."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch

from app.services.rag_service import AnswerResponse, SearchResult


@pytest.mark.api
class TestAskQuestionEndpoint:
    """Test question asking endpoint."""
    
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_ask_question_success(self, mock_get_rag, client):
        """Test successful question asking."""
        # Mock RAG service
        mock_rag = AsyncMock()
        mock_sources = [
            SearchResult("doc1", "chunk1", "This is relevant content.", 0.85)
        ]
        mock_answer = AnswerResponse(
            answer="This is the answer to your question.",
            question="What is this about?",
            sources=mock_sources,
            answer_id="answer_123",
            confidence=0.9,
            processing_time=1.5,
            token_usage={"total_tokens": 100}
        )
        mock_rag.answer_question.return_value = mock_answer
        mock_get_rag.return_value = mock_rag
        
        request_data = {
            "question": "What is this about?",
            "max_results": 5,
            "include_sources": True
        }
        
        response = client.post("/qa/ask", json=request_data)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["answer"] == "This is the answer to your question."
        assert data["question"] == "What is this about?"
        assert len(data["sources"]) == 1
        assert data["confidence"] == 0.9
        assert data["processing_time"] == 1.5
        assert "answer_id" in data
        
        # Verify RAG service was called correctly
        mock_rag.answer_question.assert_called_once()
    
    def test_ask_question_empty_question(self, client):
        """Test asking empty question."""
        request_data = {"question": ""}
        
        response = client.post("/qa/ask", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_ask_question_missing_question(self, client):
        """Test request missing question field."""
        request_data = {"max_results": 5}
        
        response = client.post("/qa/ask", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_ask_question_invalid_max_results(self, client):
        """Test with invalid max_results parameter."""
        request_data = {
            "question": "What is this?",
            "max_results": 0  # Invalid
        }
        
        response = client.post("/qa/ask", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_ask_question_with_temperature(self, client):
        """Test asking question with temperature parameter."""
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            mock_answer = AnswerResponse(
                answer="Creative answer",
                question="Be creative",
                sources=[],
                answer_id="answer_456"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            request_data = {
                "question": "Be creative",
                "temperature": 1.5
            }
            
            response = client.post("/qa/ask", json=request_data)
            
            assert response.status_code == 200
            # Verify temperature was passed to RAG service
            call_args = mock_rag.answer_question.call_args
            assert call_args.kwargs["temperature"] == 1.5
    
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_ask_question_rag_error(self, mock_get_rag, client):
        """Test question asking with RAG service error."""
        mock_rag = AsyncMock()
        mock_rag.answer_question.side_effect = Exception("RAG service error")
        mock_get_rag.return_value = mock_rag
        
        request_data = {"question": "What is this?"}
        
        response = client.post("/qa/ask", json=request_data)
        
        assert response.status_code == 500
        assert "Failed to answer question" in response.json()["detail"]


@pytest.mark.api
class TestStreamingQuestionEndpoint:
    """Test streaming question endpoint."""
    
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_ask_question_stream(self, mock_get_rag, client):
        """Test streaming question asking."""
        # Mock RAG service
        mock_rag = AsyncMock()
        mock_sources = [
            SearchResult("doc1", "chunk1", "Streaming content", 0.9)
        ]
        mock_rag.search_similar.return_value = mock_sources
        
        mock_answer = AnswerResponse(
            answer="This is a streaming answer.",
            question="Stream this",
            sources=mock_sources,
            answer_id="stream_123"
        )
        mock_rag.answer_question.return_value = mock_answer
        mock_get_rag.return_value = mock_rag
        
        request_data = {"question": "Stream this"}
        
        response = client.post("/qa/ask/stream", json=request_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Check that response contains SSE data
        content = response.content.decode()
        assert "data:" in content
        assert "type" in content
    
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_ask_question_stream_error(self, mock_get_rag, client):
        """Test streaming with error."""
        mock_rag = AsyncMock()
        mock_rag.search_similar.side_effect = Exception("Search error")
        mock_get_rag.return_value = mock_rag
        
        request_data = {"question": "This will fail"}
        
        response = client.post("/qa/ask/stream", json=request_data)
        
        assert response.status_code == 200  # SSE always returns 200
        
        # Error should be in the stream
        content = response.content.decode()
        assert "error" in content


@pytest.mark.api
class TestChatEndpoint:
    """Test chat conversation endpoint."""
    
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_chat_new_session(self, mock_get_rag, client):
        """Test starting new chat session."""
        mock_rag = AsyncMock()
        mock_answer = AnswerResponse(
            answer="Hello! How can I help you?",
            question="Hello",
            sources=[],
            answer_id="chat_123"
        )
        mock_rag.answer_question.return_value = mock_answer
        mock_get_rag.return_value = mock_rag
        
        request_data = {"message": "Hello"}
        
        with patch('app.api.endpoints.qa.chat_sessions', {}):
            response = client.post("/qa/chat", json=request_data)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["response"] == "Hello! How can I help you?"
        assert "session_id" in data
        assert "message_id" in data
        assert data["conversation_length"] == 2  # User + assistant message
    
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_chat_existing_session(self, mock_get_rag, client):
        """Test continuing existing chat session."""
        mock_rag = AsyncMock()
        mock_answer = AnswerResponse(
            answer="I understand your follow-up question.",
            question="Follow up",
            sources=[],
            answer_id="chat_456"
        )
        mock_rag.answer_question.return_value = mock_answer
        mock_get_rag.return_value = mock_rag
        
        # Mock existing session
        existing_session = {
            "session_123": {
                "messages": [
                    {"role": "user", "content": "Previous message", "id": "msg1"},
                    {"role": "assistant", "content": "Previous response", "id": "msg2"}
                ],
                "created_at": "2024-01-01T00:00:00",
                "user": None
            }
        }
        
        request_data = {
            "message": "Follow up",
            "session_id": "session_123"
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', existing_session):
            response = client.post("/qa/chat", json=request_data)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == "session_123"
        assert data["conversation_length"] == 4  # 2 existing + 2 new messages
    
    def test_chat_empty_message(self, client):
        """Test chat with empty message."""
        request_data = {"message": ""}
        
        response = client.post("/qa/chat", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_chat_with_parameters(self, mock_get_rag, client):
        """Test chat with custom parameters."""
        mock_rag = AsyncMock()
        mock_answer = AnswerResponse(
            answer="Customized response",
            question="Custom question",
            sources=[],
            answer_id="chat_789"
        )
        mock_rag.answer_question.return_value = mock_answer
        mock_get_rag.return_value = mock_rag
        
        request_data = {
            "message": "Custom question",
            "max_results": 3,
            "temperature": 0.8
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', {}):
            response = client.post("/qa/chat", json=request_data)
        
        assert response.status_code == 200
        
        # Verify parameters were passed to RAG service
        call_args = mock_rag.answer_question.call_args
        assert call_args.kwargs["max_results"] == 3
        assert call_args.kwargs["temperature"] == 0.8


@pytest.mark.api
class TestConversationHistoryEndpoint:
    """Test conversation history endpoint."""
    
    def test_get_history_success(self, client):
        """Test getting conversation history successfully."""
        mock_session = {
            "session_123": {
                "messages": [
                    {"id": "msg1", "role": "user", "content": "Hello"},
                    {"id": "msg2", "role": "assistant", "content": "Hi there!"},
                    {"id": "msg3", "role": "user", "content": "How are you?"},
                    {"id": "msg4", "role": "assistant", "content": "I'm doing well!"}
                ],
                "user": None
            }
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', mock_session):
            response = client.get("/qa/history/session_123")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == "session_123"
        assert len(data["messages"]) == 4
        assert data["total_messages"] == 4
    
    def test_get_history_with_pagination(self, client):
        """Test getting history with pagination."""
        # Create session with many messages
        messages = [
            {"id": f"msg{i}", "role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(20)
        ]
        
        mock_session = {
            "session_123": {
                "messages": messages,
                "user": None
            }
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', mock_session):
            response = client.get("/qa/history/session_123?limit=5&offset=10")
        
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["messages"]) == 5
        assert data["total_messages"] == 20
    
    def test_get_history_not_found(self, client):
        """Test getting history for non-existent session."""
        with patch('app.api.endpoints.qa.chat_sessions', {}):
            response = client.get("/qa/history/nonexistent_session")
        
        assert response.status_code == 404
        assert "Chat session not found" in response.json()["detail"]
    
    def test_get_history_access_control(self, client):
        """Test access control for chat sessions."""
        mock_session = {
            "session_123": {
                "messages": [{"id": "msg1", "role": "user", "content": "Private"}],
                "user": "other_user"
            }
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', mock_session), \
             patch('app.api.endpoints.qa.get_current_user', return_value="current_user"):
            
            response = client.get("/qa/history/session_123")
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]


@pytest.mark.api
class TestFeedbackEndpoint:
    """Test feedback submission endpoint."""
    
    def test_submit_feedback_success(self, client):
        """Test successful feedback submission."""
        request_data = {
            "answer_id": "answer_123",
            "rating": 5,
            "comment": "Great answer!"
        }
        
        with patch('app.api.endpoints.qa.answer_feedback', {}):
            response = client.post("/qa/feedback", json=request_data)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["answer_id"] == "answer_123"
        assert data["rating"] == 5
        assert "feedback_id" in data
    
    def test_submit_feedback_without_comment(self, client):
        """Test feedback submission without comment."""
        request_data = {
            "answer_id": "answer_456",
            "rating": 3
        }
        
        with patch('app.api.endpoints.qa.answer_feedback', {}):
            response = client.post("/qa/feedback", json=request_data)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["answer_id"] == "answer_456"
        assert data["rating"] == 3
    
    def test_submit_feedback_invalid_rating(self, client):
        """Test feedback with invalid rating."""
        request_data = {
            "answer_id": "answer_789",
            "rating": 6  # Invalid (> 5)
        }
        
        response = client.post("/qa/feedback", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_submit_feedback_missing_fields(self, client):
        """Test feedback with missing required fields."""
        request_data = {"rating": 4}  # Missing answer_id
        
        response = client.post("/qa/feedback", json=request_data)
        
        assert response.status_code == 422  # Validation error


@pytest.mark.api  
class TestChatSessionManagementEndpoints:
    """Test chat session management endpoints."""
    
    def test_list_chat_sessions(self, client):
        """Test listing chat sessions."""
        mock_sessions = {
            "session_1": {
                "messages": [
                    {"content": "First session message", "timestamp": "2024-01-01T00:00:00"}
                ],
                "created_at": "2024-01-01T00:00:00",
                "last_updated": "2024-01-01T00:05:00",
                "user": "test_user"
            },
            "session_2": {
                "messages": [
                    {"content": "Second session with a very long message that should be truncated for preview", "timestamp": "2024-01-01T01:00:00"}
                ],
                "created_at": "2024-01-01T01:00:00",
                "user": "test_user"
            }
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', mock_sessions), \
             patch('app.api.endpoints.qa.get_current_user', return_value="test_user"):
            
            response = client.get("/qa/sessions")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["sessions"]) == 2
        assert data["total_count"] == 2
        
        # Check session structure
        session = data["sessions"][0]
        assert "session_id" in session
        assert "created_at" in session
        assert "message_count" in session
        assert "last_message_preview" in session
    
    def test_list_chat_sessions_empty(self, client):
        """Test listing chat sessions when none exist."""
        with patch('app.api.endpoints.qa.chat_sessions', {}), \
             patch('app.api.endpoints.qa.get_current_user', return_value="test_user"):
            
            response = client.get("/qa/sessions")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_count"] == 0
        assert len(data["sessions"]) == 0
    
    def test_list_chat_sessions_pagination(self, client):
        """Test listing chat sessions with pagination."""
        # Create many sessions
        mock_sessions = {
            f"session_{i}": {
                "messages": [{"content": f"Message {i}"}],
                "created_at": f"2024-01-0{i%9+1}T00:00:00",
                "user": "test_user"
            }
            for i in range(15)
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', mock_sessions), \
             patch('app.api.endpoints.qa.get_current_user', return_value="test_user"):
            
            response = client.get("/qa/sessions?limit=5&offset=10")
        
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["sessions"]) == 5
        assert data["total_count"] == 15
        assert data["limit"] == 5
        assert data["offset"] == 10
    
    def test_delete_chat_session_success(self, client):
        """Test successful chat session deletion."""
        mock_sessions = {
            "session_to_delete": {
                "messages": [
                    {"content": "Message 1"},
                    {"content": "Message 2"}
                ],
                "user": "test_user"
            }
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', mock_sessions), \
             patch('app.api.endpoints.qa.get_current_user', return_value="test_user"):
            
            response = client.delete("/qa/sessions/session_to_delete")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == "session_to_delete"
        assert data["messages_deleted"] == 2
        
        # Verify session was deleted
        assert "session_to_delete" not in mock_sessions
    
    def test_delete_chat_session_not_found(self, client):
        """Test deleting non-existent chat session."""
        with patch('app.api.endpoints.qa.chat_sessions', {}):
            response = client.delete("/qa/sessions/nonexistent_session")
        
        assert response.status_code == 404
        assert "Chat session not found" in response.json()["detail"]
    
    def test_delete_chat_session_access_denied(self, client):
        """Test deleting chat session with access control."""
        mock_sessions = {
            "protected_session": {
                "messages": [{"content": "Protected message"}],
                "user": "other_user"
            }
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', mock_sessions), \
             patch('app.api.endpoints.qa.get_current_user', return_value="current_user"):
            
            response = client.delete("/qa/sessions/protected_session")
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]


@pytest.mark.integration
class TestQAAPIIntegration:
    """Integration tests for Q&A API."""
    
    def test_complete_qa_flow(self, client):
        """Test complete Q&A flow: ask -> feedback."""
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            # Mock RAG service
            mock_rag = AsyncMock()
            mock_answer = AnswerResponse(
                answer="Integration test answer",
                question="Integration test question",
                sources=[],
                answer_id="integration_123"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            # 1. Ask question
            ask_response = client.post("/qa/ask", json={
                "question": "Integration test question"
            })
            
            assert ask_response.status_code == 200
            ask_data = ask_response.json()
            answer_id = ask_data["answer_id"]
            
            # 2. Submit feedback
            with patch('app.api.endpoints.qa.answer_feedback', {}):
                feedback_response = client.post("/qa/feedback", json={
                    "answer_id": answer_id,
                    "rating": 5,
                    "comment": "Excellent answer!"
                })
            
            assert feedback_response.status_code == 200
            feedback_data = feedback_response.json()
            assert feedback_data["answer_id"] == answer_id
    
    def test_complete_chat_flow(self, client):
        """Test complete chat flow: chat -> history -> delete."""
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag, \
             patch('app.api.endpoints.qa.chat_sessions', {}) as mock_sessions:
            
            # Mock RAG service
            mock_rag = AsyncMock()
            mock_answer = AnswerResponse(
                answer="Chat integration test",
                question="Hello chat",
                sources=[],
                answer_id="chat_integration_123"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            # 1. Start chat
            chat_response = client.post("/qa/chat", json={
                "message": "Hello chat"
            })
            
            assert chat_response.status_code == 200
            chat_data = chat_response.json()
            session_id = chat_data["session_id"]
            
            # 2. Get history
            history_response = client.get(f"/qa/history/{session_id}")
            
            assert history_response.status_code == 200
            history_data = history_response.json()
            assert history_data["session_id"] == session_id
            assert len(history_data["messages"]) == 2
            
            # 3. Delete session
            delete_response = client.delete(f"/qa/sessions/{session_id}")
            
            assert delete_response.status_code == 200
            delete_data = delete_response.json()
            assert delete_data["session_id"] == session_id
    
    def test_error_propagation(self, client):
        """Test error propagation across Q&A endpoints."""
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            # Mock RAG service to throw error
            mock_rag = AsyncMock()
            mock_rag.answer_question.side_effect = Exception("Service unavailable")
            mock_get_rag.return_value = mock_rag
            
            # Test error in ask endpoint
            ask_response = client.post("/qa/ask", json={
                "question": "This will fail"
            })
            assert ask_response.status_code == 500
            
            # Test error in chat endpoint
            chat_response = client.post("/qa/chat", json={
                "message": "This will also fail"
            })
            assert chat_response.status_code == 500
            
            # Both should return proper error responses
            for response in [ask_response, chat_response]:
                assert "application/json" in response.headers.get("content-type", "")
                assert "detail" in response.json()


@pytest.mark.performance
class TestQAAPIPerformance:
    """Performance tests for Q&A API."""
    
    def test_ask_question_performance(self, client, performance_timer):
        """Test question asking performance."""
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            mock_answer = AnswerResponse(
                answer="Fast answer",
                question="Fast question", 
                sources=[],
                answer_id="fast_123"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            performance_timer.start()
            response = client.post("/qa/ask", json={
                "question": "Fast question"
            })
            performance_timer.stop()
            
            assert response.status_code == 200
            # API should respond quickly (< 100ms for mocked service)
            assert performance_timer.elapsed < 0.1
    
    def test_chat_history_performance(self, client, performance_timer):
        """Test chat history retrieval performance."""
        # Create large chat session
        large_messages = [
            {"id": f"msg{i}", "role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(1000)
        ]
        
        mock_sessions = {
            "large_session": {
                "messages": large_messages,
                "user": None
            }
        }
        
        with patch('app.api.endpoints.qa.chat_sessions', mock_sessions):
            performance_timer.start()
            response = client.get("/qa/history/large_session?limit=50")
            performance_timer.stop()
            
            assert response.status_code == 200
            # Should handle large sessions efficiently (< 50ms)
            assert performance_timer.elapsed < 0.05
    
    def test_concurrent_requests(self, client):
        """Test concurrent Q&A requests."""
        import concurrent.futures
        import time
        
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            mock_answer = AnswerResponse(
                answer="Concurrent answer",
                question="Concurrent question",
                sources=[],
                answer_id="concurrent_123"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            def make_request():
                start_time = time.time()
                response = client.post("/qa/ask", json={
                    "question": "Concurrent question"
                })
                end_time = time.time()
                return response.status_code, end_time - start_time
            
            # Make 5 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                results = [future.result() for future in futures]
            
            # All requests should succeed
            status_codes, durations = zip(*results)
            assert all(code == 200 for code in status_codes)
            
            # Average response time should be reasonable
            avg_duration = sum(durations) / len(durations)
            assert avg_duration < 0.2  # 200ms average