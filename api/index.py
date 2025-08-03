"""
Vercel serverless function entry point for FastAPI application.
This file adapts the FastAPI app to work with Vercel's serverless runtime.
"""

from fastapi import FastAPI
from mangum import Mangum
from app.main import app

# Create the handler for Vercel
handler = Mangum(app, lifespan="off")
