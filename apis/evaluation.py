"""
Candidate evaluation endpoints
"""

import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

# Add core to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "core"))

from .storage import storage

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvaluationResponse(BaseModel):
    """Response model for candidate evaluation"""
    application_id: str = Field(..., description="Unique application ID for future reference")
    candidate_name: str
    job_title: str
    company_repo: str
    final_score: int
    is_hire: bool
    decision_category: str
    decision_reason: str
    top_strengths: List[str]
    critical_gaps: List[str]
    jd_toon: str
    evaluation_toon: str


@router.post("/", response_model=EvaluationResponse)
async def evaluate_candidate(
    resume: UploadFile = File(..., description="Candidate's resume PDF"),
    company_repo: str = Form(..., description="GitHub repository (e.g., 'fastapi/fastapi')"),
    job_title: str = Form(..., description="Job title"),
    salary_range: Optional[str] = Form(None, description="Salary range"),
    additional_requirements: Optional[str] = Form(
        None,
        description="Additional requirements (comma-separated)"
    ),
    testing: bool = Form(True, description="Enable caching mode")
):
    """
    Evaluate a candidate against a job description generated from a GitHub repository.

    This endpoint:
    1. Generates a job description from the company's GitHub repo
    2. Analyzes the candidate's resume
    3. Evaluates the candidate's GitHub profile (if available)
    4. Returns a comprehensive evaluation with hire/no-hire decision

    Args:
        resume: PDF file of candidate's resume
        company_repo: GitHub repository (e.g., "fastapi/fastapi")
        job_title: Job title for the position
        salary_range: Optional salary range
        additional_requirements: Optional comma-separated list of requirements
        testing: Enable caching for faster responses (default: True)

    Returns:
        Comprehensive evaluation with decision and reasoning
    """
    try:
        from track_a_iron_man.combined_pipeline import combined_pipeline

        # Validate file type
        if not resume.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Resume must be a PDF file"
            )

        # Save uploaded file temporarily
        temp_dir = Path("./temp")
        temp_dir.mkdir(exist_ok=True)

        resume_path = temp_dir / resume.filename
        with open(resume_path, "wb") as f:
            content = await resume.read()
            f.write(content)

        # Parse additional requirements
        req_list = None
        if additional_requirements:
            req_list = [req.strip() for req in additional_requirements.split(",")]

        # Run the combined pipeline
        jd, jd_toon, evaluation, eval_toon = combined_pipeline(
            company_repo=company_repo,
            job_title=job_title,
            resume_pdf_path=str(resume_path),
            salary_range=salary_range,
            additional_requirements=req_list,
            verbose=False,  # Disable verbose output for API
            testing=testing
        )

        # Clean up temporary file
        resume_path.unlink()

        # Extract final decision from evaluation
        final_decision = evaluation.final_decision

        # Prepare application data
        application_data = {
            "candidate_name": evaluation.candidate_name,
            "job_title": job_title,
            "company_repo": company_repo,
            "final_score": final_decision.overall_score,
            "is_hire": final_decision.is_fit,
            "decision_category": "hire" if final_decision.is_fit else "no-hire",
            "decision_reason": final_decision.decision_reason,
            "top_strengths": evaluation.resume_analysis.key_strengths[:5],
            "critical_gaps": [gap.gap_name for gap in evaluation.skill_gaps if gap.severity == "critical"],
            "jd_toon": jd_toon,
            "evaluation_toon": eval_toon
        }

        # Save application to storage
        application_id = storage.create_application(application_data)

        # Return response with application ID
        return EvaluationResponse(
            application_id=application_id,
            candidate_name=evaluation.candidate_name,
            job_title=job_title,
            company_repo=company_repo,
            final_score=final_decision.overall_score,
            is_hire=final_decision.is_fit,
            decision_category="hire" if final_decision.is_fit else "no-hire",
            decision_reason=final_decision.decision_reason,
            top_strengths=evaluation.resume_analysis.key_strengths[:5],
            critical_gaps=[gap.gap_name for gap in evaluation.skill_gaps if gap.severity == "critical"],
            jd_toon=jd_toon,
            evaluation_toon=eval_toon
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )
