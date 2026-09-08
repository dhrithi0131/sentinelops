from fastapi import FastAPI

from backend.config import settings


app = FastAPI(
    title=settings.app_name,
    description="AI-powered Kubernetes incident intelligence platform",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "status": "running",
        "environment": settings.environment,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }
