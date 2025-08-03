"""Service for downloading and processing documents from URLs."""

import os
import tempfile
import asyncio
from typing import Tuple, List
from urllib.parse import urlparse
import mimetypes

import httpx
# from fastapi import HTTPException

from app.config import get_settings
from app.services.document_service import DocumentProcessor
from app.services.rag_service import RAGService
from app.utils.logger import get_logger
from app.utils.exceptions import DocumentProcessingError


class URLDocumentService:
    """Service for downloading and processing documents from URLs."""
    
    def __init__(self):
        """Initialize URL document service."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.document_processor = DocumentProcessor()
        self.rag_service = RAGService()
    
    async def download_document(self, url: str) -> Tuple[str, str, int]:
        """Download document from URL.
        
        Args:
            url: Document URL
            
        Returns:
            Tuple of (file_path, content_type, file_size)
            
        Raises:
            DocumentProcessingError: If download fails
        """
        try:
            # Parse URL to get filename
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            # If no filename from URL, create one based on content type
            if not filename or '.' not in filename:
                filename = "document"
            
            # Download the file
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Get content type
                content_type = response.headers.get('content-type', 'application/octet-stream')
                
                # Determine file extension if not present
                if '.' not in filename:
                    extension = mimetypes.guess_extension(content_type.split(';')[0])
                    if extension:
                        filename += extension
                    else:
                        filename += '.pdf'  # Default to PDF
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=os.path.splitext(filename)[1]
                ) as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name
                
                file_size = len(response.content)
                
                self.logger.info(
                    f"Downloaded document from URL",
                    extra={
                        "url": url,
                        "filename": filename,
                        "content_type": content_type,
                        "file_size": file_size,
                        "temp_path": temp_path
                    }
                )
                
                return temp_path, content_type, file_size
                
        except httpx.HTTPError as e:
            self.logger.error(f"Failed to download document from URL: {e}")
            raise DocumentProcessingError(f"Failed to download document: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error downloading document: {e}")
            raise DocumentProcessingError(f"Unexpected error: {str(e)}")
    
    async def process_and_answer_questions(
        self, 
        url: str, 
        questions: List[str]
    ) -> List[str]:
        """Download document, process it, and answer questions.
        
        Args:
            url: Document URL
            questions: List of questions to answer
            
        Returns:
            List of answers
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        try:
            # Ensure RAG service is initialized
            await self.rag_service._ensure_initialized()
            
            # Download document for RAG processing
            temp_path = None
            try:
                # Download document
                temp_path, content_type, file_size = await self.download_document(url)
                
                # Validate file size
                if file_size > self.settings.max_file_size:
                    max_size_mb = self.settings.max_file_size / (1024 * 1024)
                    raise DocumentProcessingError(
                        f"File too large ({file_size} bytes). Maximum size: {max_size_mb}MB"
                    )
                
                # Read file content
                with open(temp_path, 'rb') as f:
                    file_content = f.read()
                
                filename = os.path.basename(urlparse(url).path) or "document.pdf"
                
                # Process document directly using the temp file path
                processed_document = await self.document_processor.process_file(temp_path)
                
                # Add to RAG service vector store
                await self.rag_service.add_document(processed_document)
                
                # Answer all questions
                answers = []
                for i, question in enumerate(questions, 1):
                    try:
                        self.logger.info(f"Processing question {i}/{len(questions)}: {question[:100]}...")
                        
                        result = await self.rag_service.answer_question(
                            question=question,
                            max_results=5
                        )
                        
                        # Clean answer text to handle Unicode issues
                        clean_answer = result.answer.encode('utf-8', errors='ignore').decode('utf-8')
                        clean_answer = clean_answer.strip()
                        
                        if not clean_answer:
                            clean_answer = "I could not find sufficient information to answer this question."
                        
                        answers.append(clean_answer)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to answer question '{question}': {e}")
                        answers.append(f"Error processing question: {str(e)}")
                
                return answers
                
            finally:
                # Clean up temporary file
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        self.logger.warning(f"Failed to cleanup temporary file: {e}")
                        
        except Exception as e:
            self.logger.error(f"Failed to process document and answer questions: {e}")
            raise DocumentProcessingError(f"Failed to process document: {str(e)}")