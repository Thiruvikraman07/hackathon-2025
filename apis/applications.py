"""
Application management endpoints for listing and retrieving candidate applications
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .storage import storage

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationSummary(BaseModel):
    """Summary model for application list view"""
    id: str = Field(..., description="Unique application ID")
    candidate_name: str = Field(..., description="Candidate's name")
    job_title: str = Field(..., description="Job title applied for")
    company_repo: str = Field(..., description="Company GitHub repository")
    final_score: int = Field(..., ge=0, le=100, description="Overall evaluation score")
    is_hire: bool = Field(..., description="Hire decision")
    decision_category: str = Field(..., description="Decision category (hire/no-hire)")
    created_at: str = Field(..., description="Application submission timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")


class ApplicationDetail(BaseModel):
    """Detailed application model with full evaluation results"""
    id: str = Field(..., description="Unique application ID")
    candidate_name: str = Field(..., description="Candidate's name")
    job_title: str = Field(..., description="Job title applied for")
    company_repo: str = Field(..., description="Company GitHub repository")
    final_score: int = Field(..., ge=0, le=100, description="Overall evaluation score")
    is_hire: bool = Field(..., description="Hire decision")
    decision_category: str = Field(..., description="Decision category (hire/no-hire)")
    decision_reason: str = Field(..., description="Detailed reasoning for the decision")
    top_strengths: List[str] = Field(..., description="Candidate's top strengths")
    critical_gaps: List[str] = Field(..., description="Critical skill gaps identified")
    jd_toon: str = Field(..., description="Job description in TOON format")
    evaluation_toon: str = Field(..., description="Full evaluation in TOON format")
    created_at: str = Field(..., description="Application submission timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")


class ApplicationListResponse(BaseModel):
    """Response model for application list with pagination"""
    total: int = Field(..., description="Total number of applications")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum records returned")
    applications: List[ApplicationSummary] = Field(..., description="List of applications")


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    skip: int = Query(0, ge=0, description="Number of records to skip (pagination)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    is_hire: Optional[bool] = Query(None, description="Filter by hire decision (true/false/null for all)")
):
    """
    List all candidate applications with pagination and optional filtering.

    Returns a summary view of all applications sorted by creation date (newest first).

    Args:
        skip: Number of records to skip for pagination (default: 0)
        limit: Maximum number of records to return (default: 100, max: 500)
        is_hire: Optional filter - true for hired, false for not hired, null/omit for all

    Returns:
        Paginated list of application summaries with total count

    Example:
        GET /applications?skip=0&limit=20
        GET /applications?is_hire=true&limit=10
    """
    try:
        # Get total count
        total = storage.count_applications(is_hire=is_hire)

        # Get applications
        applications = storage.list_applications(
            skip=skip,
            limit=limit,
            is_hire=is_hire
        )

        # Convert to summary models
        summaries = [
            ApplicationSummary(
                id=app['id'],
                candidate_name=app['candidate_name'],
                job_title=app['job_title'],
                company_repo=app['company_repo'],
                final_score=app['final_score'],
                is_hire=app['is_hire'],
                decision_category=app['decision_category'],
                created_at=app['created_at'],
                updated_at=app['updated_at']
            )
            for app in applications
        ]

        return ApplicationListResponse(
            total=total,
            skip=skip,
            limit=limit,
            applications=summaries
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list applications: {str(e)}"
        )


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(application_id: str):
    """
    Get detailed information about a specific application by ID.

    Returns the complete evaluation results including:
    - Full hire decision reasoning
    - Detailed strengths and gaps analysis
    - TOON format outputs for both JD and evaluation

    Args:
        application_id: Unique application ID (UUID)

    Returns:
        Complete application details with full evaluation

    Raises:
        404: Application not found

    Example:
        GET /applications/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        # Retrieve application from storage
        application = storage.get_application(application_id)

        if not application:
            raise HTTPException(
                status_code=404,
                detail=f"Application with ID '{application_id}' not found"
            )

        # Return detailed application
        return ApplicationDetail(
            id=application['id'],
            candidate_name=application['candidate_name'],
            job_title=application['job_title'],
            company_repo=application['company_repo'],
            final_score=application['final_score'],
            is_hire=application['is_hire'],
            decision_category=application['decision_category'],
            decision_reason=application['decision_reason'],
            top_strengths=application['top_strengths'],
            critical_gaps=application['critical_gaps'],
            jd_toon=application['jd_toon'],
            evaluation_toon=application['evaluation_toon'],
            created_at=application['created_at'],
            updated_at=application['updated_at']
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve application: {str(e)}"
        )


@router.delete("/{application_id}")
async def delete_application(application_id: str):
    """
    Delete an application by ID.

    Args:
        application_id: Unique application ID (UUID)

    Returns:
        Success message

    Raises:
        404: Application not found

    Example:
        DELETE /applications/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        success = storage.delete_application(application_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Application with ID '{application_id}' not found"
            )

        return {
            "message": f"Application {application_id} deleted successfully",
            "deleted_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete application: {str(e)}"
        )
