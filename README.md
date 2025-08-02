# RAG Q&A Foundation

A production-ready Retrieval-Augmented Generation (RAG) Q&A system built with FastAPI, Google Gemini, and FAISS.

## Features

- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Google Gemini Integration**: Gemini Pro for answers and embedding-001 for embeddings
- **FAISS Vector Database**: Efficient similarity search for document retrieval
- **Multi-format Support**: PDF, TXT, DOCX, and Markdown document processing
- **Production Ready**: Comprehensive logging, error handling, and monitoring
- **Type Safe**: Full type hints with Pydantic models
- **Security**: Built-in security headers and rate limiting
- **Health Checks**: Kubernetes-ready health and readiness probes

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd rag-qa-foundation
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your Google Gemini API key and other settings
   ```

3. **Run the Application**:
   ```bash
   python -m app.main
   # Or use uvicorn directly:
   uvicorn app.main:app --reload
   ```

4. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Service Info: http://localhost:8000/health/info

## Project Structure

```
rag-qa-foundation/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── middleware.py           # Custom middleware
│   ├── models/
│   │   ├── requests.py         # Pydantic request models
│   │   └── responses.py        # Pydantic response models
│   ├── services/
│   │   ├── rag_service.py      # Core RAG logic (to be implemented)
│   │   └── document_service.py # Document processing (to be implemented)
│   ├── api/
│   │   ├── deps.py             # Dependencies (to be implemented)
│   │   └── endpoints/
│   │       ├── health.py       # Health checks
│   │       ├── documents.py    # Document management (to be implemented)
│   │       └── qa.py           # Q&A endpoints (to be implemented)
│   └── utils/
│       ├── logger.py           # Logging utilities
│       └── exceptions.py       # Custom exceptions
├── tests/                      # Test modules (to be implemented)
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

Key environment variables:

- `GOOGLE_API_KEY`: Your Google Gemini API key (required)
- `VECTOR_STORE_PATH`: Path for vector database storage
- `MAX_FILE_SIZE`: Maximum upload file size in bytes
- `CHUNK_SIZE`: Text chunk size for processing
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

See `.env.example` for all available options.

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/detailed` - Comprehensive health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe
- `GET /health/info` - Service information

### Document Management
- `POST /documents/upload` - Upload and process documents
- `GET /documents` - List uploaded documents with pagination
- `GET /documents/{id}` - Get document details and chunks
- `GET /documents/{id}/status` - Check processing status
- `DELETE /documents/{id}` - Delete document and its chunks
- `POST /documents/{id}/reprocess` - Reprocess with new parameters

### Question & Answer
- `POST /qa/ask` - Ask questions and get AI answers
- `POST /qa/ask/stream` - Ask questions with streaming responses
- `POST /qa/chat` - Conversational Q&A with session memory
- `GET /qa/history/{session_id}` - Get conversation history
- `GET /qa/sessions` - List chat sessions
- `DELETE /qa/sessions/{session_id}` - Delete chat session
- `POST /qa/feedback` - Submit feedback on answers

## Development Status

✅ **Phase 1 Complete**: Foundation & Configuration
- [x] FastAPI project structure
- [x] Configuration management with pydantic-settings
- [x] Structured logging with request tracing
- [x] Custom exceptions and error handling
- [x] Security middleware and rate limiting
- [x] Health check endpoints
- [x] Complete type safety with Pydantic models

✅ **Phase 2 Complete**: Core RAG Implementation  
- [x] Document processing service (PDF, TXT, DOCX, MD)
- [x] Core RAG service with Google Gemini & FAISS
- [x] Intelligent text chunking with overlap
- [x] Vector embeddings and similarity search
- [x] Context-aware answer generation

✅ **Phase 3 Complete**: API Endpoints
- [x] Document management API with file upload
- [x] Q&A endpoints with streaming support
- [x] Conversational chat with session memory
- [x] Background processing with status tracking
- [x] Rate limiting and user feedback system

🔄 **Next Steps**:
- [ ] Comprehensive testing framework
- [ ] Docker configuration and CI/CD
- [ ] Streamlit frontend interface
- [ ] Enhanced documentation and examples

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --log-level debug

# Run tests (when available)
pytest

# Code formatting
black .
isort .
flake8 .
```

## Monitoring

The application includes comprehensive logging and monitoring:

- **Structured Logging**: JSON logs with request tracing
- **Performance Metrics**: Request duration and resource usage
- **Health Checks**: Multiple health check endpoints
- **Error Tracking**: Detailed error logging with context

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

For detailed development guidelines, see the project documentation.