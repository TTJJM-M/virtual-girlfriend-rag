from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db, async_engine, SyncSessionLocal
from app.api import auth, chat, stream_chat, knowledge
from app.services.auth_service import init_admin_user_sync
import asyncio
import os

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="虚拟女友 RAG 知识库问答系统 API",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )


# Register routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(stream_chat.router)
app.include_router(knowledge.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and admin user on startup"""
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Ensure directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)

    # Initialize database
    print("Initializing database...")
    init_db()

    # Initialize admin user
    print("Initializing admin user...")
    db = SyncSessionLocal()
    try:
        init_admin_user_sync(db)
    finally:
        db.close()

    print(f"✅ Server ready at http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API docs: http://{settings.HOST}:{settings.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await async_engine.dispose()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
