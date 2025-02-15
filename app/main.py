from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, documents
from app.config import get_settings

settings = get_settings()

# Create FastAPI app
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

# Include routers
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

@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {
        "status": "online",
        "message": "Tech RAG API is running",
        "version": "1.0.0"
    }
