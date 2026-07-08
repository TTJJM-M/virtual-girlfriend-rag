#!/usr/bin/env python
"""
Virtual Girlfriend RAG Knowledge Base - Backend Server
Usage: python run.py
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Host: {settings.HOST}:{settings.PORT}")
    print(f"   Database: {settings.DB_NAME} on {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"   Models: LLM={settings.DASHSCOPE_LLM_MODEL}, Embedding={settings.DASHSCOPE_EMBEDDING_MODEL}")
    print()

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
