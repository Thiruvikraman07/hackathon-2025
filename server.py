"""
FastAPI Server for Hackathon 2025 - Hiring Assessment Pipeline
Minimal starting point for Track A candidate evaluation API
"""

from fastapi import FastAPI
import uvicorn

from apis import (
    evaluation_router,
    job_description_router,
    health_router,
    applications_router
)

# Initialize FastAPI app
app = FastAPI(
    title="Hiring Assessment API",
    description="AI-powered candidate evaluation system for Track A",
    version="1.0.0"
)

# Include routers
app.include_router(health_router)
app.include_router(evaluation_router)
app.include_router(job_description_router)
app.include_router(applications_router)


# ============================================
# Server Entry Point
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
