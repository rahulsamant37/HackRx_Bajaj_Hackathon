"""Vercel entry point for RAG Q&A Foundation."""

from app.main import app

# Export the app for Vercel
__all__ = ["app"]
