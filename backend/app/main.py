# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from backend.app.routers import auth, documents, chat
from backend.app.config import get_settings
from backend.app.logging_config import setup_logging

# Setup logging first
setup_logging()
logger = logging.getLogger("app")

settings = get_settings()

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Tech RAG API",
        description="API for the Tech RAG document management system",
        version="1.0.0",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8501"],  # Streamlit default port
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers with proper prefixes
    app.include_router(
        auth.router,
        prefix=settings.api_prefix,
        tags=["Authentication"]
    )

    app.include_router(
        documents.router,
        prefix=settings.api_prefix,
        tags=["Documents"]
    )

    app.include_router(
        chat.router,
        prefix=settings.api_prefix,
        tags=["Chat"]
    )

    return app

# Create the application instance
app = create_application()

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting Tech RAG API")
    # Add any additional startup tasks here

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Tech RAG API")
    # Add any cleanup tasks here

@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    logger.debug("Root endpoint accessed")
    return {
        "status": "online",
        "message": "Tech RAG API is running",
        "version": "1.0.0"
    }
