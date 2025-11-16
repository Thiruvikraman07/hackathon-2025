"""
FastAPI Server for Hackathon 2025 - Hiring Assessment Pipeline
Minimal starting point for Track A candidate evaluation API
"""

import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add core to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "core"))

# Import pipelines
from track_a_iron_man.combined_pipeline import combined_pipeline

# Initialize FastAPI app
app = FastAPI(
    title="Hiring Assessment API",
    description="AI-powered candidate evaluation system for Track A",
    version="1.0.0"
)


# ============================================
# Request/Response Models
# ============================================

class EvaluationRequest(BaseModel):
    """Request model for candidate evaluation"""
    company_repo: str = Field(
        description="GitHub repository (e.g., 'fastapi/fastapi')",
        examples=["fastapi/fastapi"]
    )
    job_title: str = Field(
        description="Job title for the position",
        examples=["Senior Python Backend Developer"]
    )
    salary_range: Optional[str] = Field(
        default=None,
        description="Salary range",
        examples=["$140k-$180k"]
    )
    additional_requirements: Optional[List[str]] = Field(
        default=None,
        description="Additional job requirements"
    )
    testing: bool = Field(
        default=True,
        description="Enable caching mode for faster responses"
    )


class EvaluationResponse(BaseModel):
    """Response model for candidate evaluation"""
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


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str


# ============================================
# API Endpoints
# ============================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@app.post("/evaluate", response_model=EvaluationResponse)
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

        # Return response
        return EvaluationResponse(
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


@app.post("/generate-jd")
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
