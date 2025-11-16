"""
Job Description generation endpoints
"""

from typing import Optional

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/jd", tags=["job-description"])


@router.post("/generate")
async def generate_job_description(
    company_repo: str = Form(..., description="GitHub repository"),
    job_title: str = Form(..., description="Job title"),
    salary_range: Optional[str] = Form(None),
    additional_requirements: Optional[str] = Form(None),
    testing: bool = Form(True)
):
    """
    Generate a job description from a GitHub repository.

    Args:
        company_repo: GitHub repository (e.g., "fastapi/fastapi")
        job_title: Job title for the position
        salary_range: Optional salary range
        additional_requirements: Optional comma-separated requirements
        testing: Enable caching mode

    Returns:
        Job description in TOON format
    """
    try:
        import sys
        from pathlib import Path

        # Add core to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root / "core"))

        from track_a_iron_man.pipeline1_jd_generator import generate_jd

        # Parse additional requirements
        req_list = None
        if additional_requirements:
            req_list = [req.strip() for req in additional_requirements.split(",")]

        # Generate JD
        jd, jd_toon = generate_jd(
            company_repo=company_repo,
            job_title=job_title,
            salary_range=salary_range,
            additional_requirements=req_list,
            verbose=False,
            testing=testing
        )

        return JSONResponse(content={
            "job_title": jd.job_title,
            "company_repo": jd.repository,
            "experience_level": jd.experience_level,
            "salary_range": jd.salary_range,
            "jd_toon": jd_toon,
            "summary": jd.summary
        })

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"JD generation failed: {str(e)}"
        )
