"""Tests for document management API endpoints."""

import pytest
import io
import json
from unittest.mock import Mock, AsyncMock, patch


@pytest.mark.api
class TestDocumentUploadEndpoint:
    """Test document upload endpoint."""
    
    @patch('app.api.endpoints.documents.get_document_processor')
    @patch('app.api.endpoints.documents.get_rag_service')
    def test_upload_document_success(self, mock_get_rag, mock_get_processor, client):
        """Test successful document upload."""
        # Mock services
        mock_processor = AsyncMock()
        mock_rag = AsyncMock()
        mock_get_processor.return_value = mock_processor
        mock_get_rag.return_value = mock_rag
        
        # Create test file
        test_file = io.BytesIO(b"This is test document content.")
        
        with patch('app.api.endpoints.documents.save_upload_file') as mock_save:
            mock_save.return_value = "/tmp/test_file.txt"
            
            response = client.post(
                "/documents/upload",
                files={"file": ("test.txt", test_file, "text/plain")}
            )
        
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data
        assert data["filename"] == "test.txt"
        assert data["status"] == "processing"
    
    def test_upload_document_no_file(self, client):
        """Test upload without file."""
        response = client.post("/documents/upload")
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_document_unsupported_type(self, client):
        """Test upload with unsupported file type."""
        test_file = io.BytesIO(b"test content")
        
        response = client.post(
            "/documents/upload",
            files={"file": ("test.xyz", test_file, "application/octet-stream")}
        )
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    def test_upload_document_with_metadata(self, client):
        """Test upload with additional metadata."""
        test_file = io.BytesIO(b"This is test content.")
        metadata = {"category": "test", "priority": "high"}
        
        with patch('app.api.endpoints.documents.get_document_processor'), \
             patch('app.api.endpoints.documents.get_rag_service'), \
             patch('app.api.endpoints.documents.save_upload_file') as mock_save:
            
            mock_save.return_value = "/tmp/test_file.txt"
            
            response = client.post(
                "/documents/upload",
                files={"file": ("test.txt", test_file, "text/plain")},
                data={"metadata": json.dumps(metadata)}
            )
        
        assert response.status_code == 201
    
    def test_upload_document_invalid_metadata(self, client):
        """Test upload with invalid JSON metadata."""
        test_file = io.BytesIO(b"This is test content.")
        
        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", test_file, "text/plain")},
            data={"metadata": "invalid json"}
        )
        
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]
    
    def test_upload_document_with_chunking_params(self, client):
        """Test upload with custom chunking parameters."""
        test_file = io.BytesIO(b"This is test content.")
        
        with patch('app.api.endpoints.documents.get_document_processor'), \
             patch('app.api.endpoints.documents.get_rag_service'), \
             patch('app.api.endpoints.documents.save_upload_file') as mock_save:
            
            mock_save.return_value = "/tmp/test_file.txt"
            
            response = client.post(
                "/documents/upload",
                files={"file": ("test.txt", test_file, "text/plain")},
                data={
                    "chunk_size": "500",
                    "chunk_overlap": "50"
                }
            )
        
        assert response.status_code == 201


@pytest.mark.api
class TestDocumentListEndpoint:
    """Test document listing endpoint."""
    
    @patch('app.api.endpoints.documents.get_rag_service')
    def test_list_documents_empty(self, mock_get_rag, client):
        """Test listing documents when none exist."""
        mock_rag = Mock()
        mock_rag.get_stats.return_value = {"total_documents": 0}
        mock_get_rag.return_value = mock_rag
        
        with patch('app.api.endpoints.documents.processing_status', {}):
            response = client.get("/documents/")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["documents"] == []
        assert data["total_count"] == 0
    
    @patch('app.api.endpoints.documents.get_rag_service')
    def test_list_documents_with_data(self, mock_get_rag, client):
        """Test listing documents with existing data."""
        mock_rag = Mock()
        mock_rag.get_stats.return_value = {"total_documents": 2}
        mock_get_rag.return_value = mock_rag
        
        # Mock processing status
        mock_status = {
            "doc_1": {
                "filename": "test1.txt",
                "status": "completed",
                "started_at": "2024-01-01T00:00:00",
                "chunk_count": 5
            },
            "doc_2": {
                "filename": "test2.pdf", 
                "status": "processing",
                "started_at": "2024-01-01T01:00:00"
            }
        }
        
        with patch('app.api.endpoints.documents.processing_status', mock_status):
            response = client.get("/documents/")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["documents"]) == 2
        assert data["total_count"] == 2
        
        # Check document structure
        doc = data["documents"][0]
        assert "id" in doc
        assert "filename" in doc
        assert "processing_status" in doc
    
    def test_list_documents_pagination(self, client):
        """Test document listing with pagination."""
        with patch('app.api.endpoints.documents.get_rag_service'), \
             patch('app.api.endpoints.documents.processing_status', {}):
            
            response = client.get("/documents/?limit=5&offset=10")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 10
    
    def test_list_documents_invalid_pagination(self, client):
        """Test document listing with invalid pagination parameters."""
        # Invalid limit
        response = client.get("/documents/?limit=0")
        assert response.status_code == 400
        assert "Limit must be between 1 and 100" in response.json()["detail"]
        
        # Invalid offset
        response = client.get("/documents/?offset=-1")
        assert response.status_code == 400
        assert "Offset must be non-negative" in response.json()["detail"]


@pytest.mark.api
class TestDocumentDetailEndpoint:
    """Test document detail endpoint."""
    
    def test_get_document_success(self, client):
        """Test getting document details successfully."""
        mock_status = {
            "doc_123": {
                "filename": "test.txt",
                "status": "completed",
                "started_at": "2024-01-01T00:00:00",
                "chunk_count": 3
            }
        }
        
        with patch('app.api.endpoints.documents.processing_status', mock_status), \
             patch('app.api.endpoints.documents.get_rag_service'):
            
            response = client.get("/documents/doc_123")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["document"]["id"] == "doc_123"
        assert data["document"]["filename"] == "test.txt"
        assert "chunks" in data
    
    def test_get_document_not_found(self, client):
        """Test getting non-existent document."""
        with patch('app.api.endpoints.documents.processing_status', {}):
            response = client.get("/documents/nonexistent_doc")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]


@pytest.mark.api
class TestDocumentDeletionEndpoint:
    """Test document deletion endpoint."""
    
    @patch('app.api.endpoints.documents.get_rag_service')
    def test_delete_document_success(self, mock_get_rag, client):
        """Test successful document deletion."""
        mock_rag = AsyncMock()
        mock_rag.delete_document.return_value = True
        mock_get_rag.return_value = mock_rag
        
        mock_status = {
            "doc_123": {
                "filename": "test.txt",
                "chunk_count": 5
            }
        }
        
        with patch('app.api.endpoints.documents.processing_status', mock_status):
            response = client.delete("/documents/doc_123")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["document_id"] == "doc_123"
        assert data["chunks_deleted"] == 5
        
        # Verify document was removed from processing status
        mock_rag.delete_document.assert_called_once_with("doc_123")
    
    def test_delete_document_not_found(self, client):
        """Test deleting non-existent document."""
        with patch('app.api.endpoints.documents.processing_status', {}):
            response = client.delete("/documents/nonexistent_doc")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]
    
    @patch('app.api.endpoints.documents.get_rag_service')
    def test_delete_document_vector_store_not_found(self, mock_get_rag, client):
        """Test deleting document not found in vector store."""
        mock_rag = AsyncMock()
        mock_rag.delete_document.return_value = False
        mock_get_rag.return_value = mock_rag
        
        mock_status = {"doc_123": {"filename": "test.txt"}}
        
        with patch('app.api.endpoints.documents.processing_status', mock_status):
            response = client.delete("/documents/doc_123")
        
        assert response.status_code == 404
        assert "Document not found in vector store" in response.json()["detail"]


@pytest.mark.api  
class TestProcessingStatusEndpoint:
    """Test processing status endpoint."""
    
    def test_get_processing_status_success(self, client):
        """Test getting processing status successfully."""
        mock_status = {
            "doc_123": {
                "status": "processing",
                "progress": 0.5,
                "steps_completed": 2,
                "total_steps": 4,
                "current_step": "Creating embeddings"
            }
        }
        
        with patch('app.api.endpoints.documents.processing_status', mock_status):
            response = client.get("/documents/doc_123/status")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["document_id"] == "doc_123"
        assert data["status"] == "processing"
        assert data["progress"] == 0.5
        assert data["steps_completed"] == 2
        assert data["total_steps"] == 4
    
    def test_get_processing_status_completed(self, client):
        """Test getting status for completed document."""
        mock_status = {
            "doc_123": {
                "status": "completed",
                "progress": 1.0,
                "steps_completed": 3,
                "total_steps": 3,
                "chunk_count": 10
            }
        }
        
        with patch('app.api.endpoints.documents.processing_status', mock_status):
            response = client.get("/documents/doc_123/status")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 1.0
    
    def test_get_processing_status_failed(self, client):
        """Test getting status for failed document."""
        mock_status = {
            "doc_123": {
                "status": "failed",
                "error_message": "Processing failed due to invalid format"
            }
        }
        
        with patch('app.api.endpoints.documents.processing_status', mock_status):
            response = client.get("/documents/doc_123/status")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Processing failed due to invalid format"
    
    def test_get_processing_status_not_found(self, client):
        """Test getting status for non-existent document."""
        with patch('app.api.endpoints.documents.processing_status', {}):
            response = client.get("/documents/nonexistent_doc/status")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]


@pytest.mark.api
class TestReprocessDocumentEndpoint:
    """Test document reprocessing endpoint."""
    
    def test_reprocess_document_not_implemented(self, client):
        """Test reprocessing endpoint (currently not fully implemented)."""
        mock_status = {
            "doc_123": {
                "filename": "test.txt",
                "status": "completed"
            }
        }
        
        request_data = {
            "chunk_size": 800,
            "chunk_overlap": 100
        }
        
        with patch('app.api.endpoints.documents.processing_status', mock_status):
            response = client.post(
                "/documents/doc_123/reprocess",
                json=request_data
            )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not fully implemented" in data["message"]
    
    def test_reprocess_document_not_found(self, client):
        """Test reprocessing non-existent document."""
        request_data = {
            "chunk_size": 800,
            "chunk_overlap": 100
        }
        
        with patch('app.api.endpoints.documents.processing_status', {}):
            response = client.post(
                "/documents/nonexistent_doc/reprocess",
                json=request_data
            )
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]


@pytest.mark.integration
class TestDocumentAPIIntegration:
    """Integration tests for document API."""
    
    @patch('app.api.endpoints.documents.process_document_background')
    def test_upload_and_check_status_flow(self, mock_process_bg, client):
        """Test complete upload and status checking flow."""
        test_file = io.BytesIO(b"This is integration test content.")
        
        with patch('app.api.endpoints.documents.get_document_processor'), \
             patch('app.api.endpoints.documents.get_rag_service'), \
             patch('app.api.endpoints.documents.save_upload_file') as mock_save:
            
            mock_save.return_value = "/tmp/test_file.txt"
            
            # Upload document
            upload_response = client.post(
                "/documents/upload",
                files={"file": ("integration_test.txt", test_file, "text/plain")}
            )
            
            assert upload_response.status_code == 201
            upload_data = upload_response.json()
            document_id = upload_data["document_id"]
            
            # Simulate processing status update
            with patch('app.api.endpoints.documents.processing_status', {
                document_id: {
                    "status": "processing",
                    "progress": 0.5,
                    "steps_completed": 1,
                    "total_steps": 3
                }
            }):
                # Check status
                status_response = client.get(f"/documents/{document_id}/status")
                
                assert status_response.status_code == 200
                status_data = status_response.json()
                assert status_data["document_id"] == document_id
                assert status_data["status"] == "processing"
    
    def test_document_lifecycle(self, client):
        """Test complete document lifecycle: upload -> list -> detail -> delete."""
        test_file = io.BytesIO(b"Lifecycle test content.")
        
        with patch('app.api.endpoints.documents.get_document_processor'), \
             patch('app.api.endpoints.documents.get_rag_service') as mock_get_rag, \
             patch('app.api.endpoints.documents.save_upload_file') as mock_save:
            
            mock_save.return_value = "/tmp/test_file.txt"
            mock_rag = AsyncMock()
            mock_rag.get_stats.return_value = {"total_documents": 1}
            mock_rag.delete_document.return_value = True
            mock_get_rag.return_value = mock_rag
            
            # 1. Upload document
            upload_response = client.post(
                "/documents/upload",
                files={"file": ("lifecycle_test.txt", test_file, "text/plain")}
            )
            assert upload_response.status_code == 201
            document_id = upload_response.json()["document_id"]
            
            # Simulate completed processing
            mock_processing_status = {
                document_id: {
                    "filename": "lifecycle_test.txt",
                    "status": "completed",
                    "started_at": "2024-01-01T00:00:00",
                    "chunk_count": 3
                }
            }
            
            with patch('app.api.endpoints.documents.processing_status', mock_processing_status):
                # 2. List documents
                list_response = client.get("/documents/")
                assert list_response.status_code == 200
                list_data = list_response.json()
                assert len(list_data["documents"]) == 1
                
                # 3. Get document details
                detail_response = client.get(f"/documents/{document_id}")
                assert detail_response.status_code == 200
                detail_data = detail_response.json()
                assert detail_data["document"]["id"] == document_id
                
                # 4. Delete document
                delete_response = client.delete(f"/documents/{document_id}")
                assert delete_response.status_code == 200
                delete_data = delete_response.json()
                assert delete_data["document_id"] == document_id
    
    def test_error_handling_chain(self, client):
        """Test error handling across multiple endpoints."""
        # Try to get non-existent document
        response1 = client.get("/documents/fake_doc")
        assert response1.status_code == 404
        
        # Try to get status for non-existent document
        response2 = client.get("/documents/fake_doc/status")
        assert response2.status_code == 404
        
        # Try to delete non-existent document
        response3 = client.delete("/documents/fake_doc")
        assert response3.status_code == 404
        
        # All should return proper error responses
        for response in [response1, response2, response3]:
            assert "application/json" in response.headers.get("content-type", "")
            assert "detail" in response.json()


@pytest.mark.performance
class TestDocumentAPIPerformance:
    """Performance tests for document API."""
    
    def test_list_documents_performance(self, client, performance_timer):
        """Test document listing performance."""
        # Create large mock processing status
        large_status = {
            f"doc_{i}": {
                "filename": f"test_{i}.txt",
                "status": "completed",
                "started_at": "2024-01-01T00:00:00"
            }
            for i in range(100)
        }
        
        with patch('app.api.endpoints.documents.get_rag_service'), \
             patch('app.api.endpoints.documents.processing_status', large_status):
            
            performance_timer.start()
            response = client.get("/documents/?limit=50")
            performance_timer.stop()
            
            assert response.status_code == 200
            # Should handle large datasets quickly (< 100ms)
            assert performance_timer.elapsed < 0.1
    
    def test_upload_endpoint_response_time(self, client, performance_timer):  
        """Test upload endpoint response time."""
        test_file = io.BytesIO(b"Performance test content.")
        
        with patch('app.api.endpoints.documents.get_document_processor'), \
             patch('app.api.endpoints.documents.get_rag_service'), \
             patch('app.api.endpoints.documents.save_upload_file') as mock_save:
            
            mock_save.return_value = "/tmp/perf_test.txt"
            
            performance_timer.start()
            response = client.post(
                "/documents/upload",
                files={"file": ("perf_test.txt", test_file, "text/plain")}
            )
            performance_timer.stop()
            
            assert response.status_code == 201
            # Upload endpoint should respond quickly (< 200ms)
            assert performance_timer.elapsed < 0.2