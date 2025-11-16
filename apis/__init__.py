"""
API endpoints package for Hackathon 2025
"""

from .evaluation import router as evaluation_router
from .job_description import router as job_description_router
from .health import router as health_router
from .applications import router as applications_router

__all__ = [
    "evaluation_router",
    "job_description_router",
    "health_router",
    "applications_router",
]
