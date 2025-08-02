# 🚀 Quick Start Guide

This guide will get your RAG Q&A Foundation system up and running in minutes.

## Prerequisites

- Python 3.11 or higher
- Google Gemini API key (for embeddings and chat completions)

## Step 1: Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# REQUIRED: Set your Google Gemini API key
vim .env  # or use your preferred editor
```

**Minimum required configuration:**
```env
GOOGLE_API_KEY=your_actual_google_gemini_api_key_here
```

## Step 3: Run the Application

```bash
# Start the server
python -m app.main

# Alternative using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 4: Verify Installation

1. **Check Health**: Visit http://localhost:8000/health
2. **View API Docs**: Visit http://localhost:8000/docs
3. **Test Basic Function**: Use the interactive API documentation

## Step 5: Upload Your First Document

### Using the API:

```bash
# Upload a document (replace with your file)
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@your_document.pdf"

# Check processing status
curl -X GET "http://localhost:8000/documents/{document_id}/status"
```

### Using the Interactive Docs:

1. Go to http://localhost:8000/docs
2. Find the `POST /documents/upload` endpoint
3. Click "Try it out"
4. Upload a PDF, TXT, DOCX, or MD file
5. Execute and note the `document_id` in the response

## Step 6: Ask Your First Question

```bash
# Ask a question about your uploaded documents
curl -X POST "http://localhost:8000/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?",
    "max_results": 5,
    "include_sources": true
  }'
```

## 🎉 You're Ready!

Your RAG Q&A system is now running with:

- ✅ Document processing (PDF, TXT, DOCX, MD)
- ✅ Vector embeddings with FAISS
- ✅ AI-powered question answering
- ✅ Streaming responses
- ✅ Conversational chat
- ✅ Full API documentation

## Next Steps

### Explore the API

Visit http://localhost:8000/docs to explore all available endpoints:

- **Document Management**: Upload, list, delete documents
- **Q&A**: Ask questions, stream responses, chat conversations
- **Monitoring**: Health checks and system stats

### Configuration Options

Check `.env.example` for advanced configuration:

- Chunk size and overlap settings
- Rate limiting parameters
- Vector store configuration
- Logging levels

### Production Deployment

For production use:

1. Set `ENVIRONMENT=production` in your `.env`
2. Use a reverse proxy (nginx)
3. Set up proper logging aggregation
4. Configure monitoring and alerting
5. Use external databases for session storage

## Troubleshooting

### Common Issues

2. **ModuleNotFoundError**: Make sure you activated the virtual environment and installed dependencies
3. **Google Gemini API Error**: Verify your API key is correct and has sufficient credits
3. **File Upload Issues**: Check file size limits in configuration
4. **Vector Store Errors**: Ensure the data directory is writable

### Getting Help

- Check the logs in `./logs/app.log`
- Visit http://localhost:8000/health/detailed for system status
- Review the comprehensive documentation in `/docs`

## Example Usage

```python
import requests

# Upload document
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/documents/upload",
        files={"file": f}
    )
    doc_id = response.json()["document_id"]

# Ask question
response = requests.post(
    "http://localhost:8000/qa/ask",
    json={
        "question": "Summarize the key points",
        "max_results": 3
    }
)
answer = response.json()["answer"]
print(answer)
```

---

**Happy RAG-ing! 🤖📚**