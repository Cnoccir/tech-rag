import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",  # Ensure correct path
        host="0.0.0.0",
        port=8000,
        reload=True
    )
