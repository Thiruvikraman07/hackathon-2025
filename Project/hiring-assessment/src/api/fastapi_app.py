"""FastAPI application for hiring assessment workflow."""
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from ..workflows import HiringAssessmentWorkflow
from ..config import settings, logger

# Initialize FastAPI app
app = FastAPI(
    title="Hiring Assessment Multi-Agent System",
    description="Multi-agent system for analyzing hiring requirements",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for workflow sessions (in production, use Redis or DB)
active_workflows: Dict[str, HiringAssessmentWorkflow] = {}


# Request/Response Models
class WorkflowInput(BaseModel):
    """Input data for hiring assessment workflow."""

    strategic_context_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input for strategic context agent"
    )
    pain_point_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input for pain point agent"
    )
    artifact_a_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input for artifact inspector A"
    )
    artifact_c_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input for artifact inspector C"
    )
    location: str = Field(
        default="Remote/Global",
        description="Hiring location"
    )
    industry: str = Field(
        default="Technology",
        description="Industry context"
    )


class WorkflowResponse(BaseModel):
    """Response from workflow execution."""

    session_id: str
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None


class SessionStatus(BaseModel):
    """Status of a workflow session."""

    session_id: str
    exists: bool
    summary: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Hiring Assessment Multi-Agent System",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "hiring-assessment-api"
    }


@app.post("/workflow/run", response_model=WorkflowResponse)
async def run_workflow(
    workflow_input: WorkflowInput,
    background_tasks: BackgroundTasks,
    session_id: Optional[str] = None
):
    """
    Run the complete hiring assessment workflow.

    Args:
        workflow_input: Input data for all agents
        background_tasks: FastAPI background tasks
        session_id: Optional session ID

    Returns:
        Workflow execution results
    """
    try:
        logger.info("Received workflow execution request")

        # Create workflow instance
        workflow = HiringAssessmentWorkflow(session_id=session_id)

        # Store in active workflows
        active_workflows[workflow.session_memory.session_id] = workflow

        # Prepare input data
        input_data = {
            "strategic_context_input": workflow_input.strategic_context_input,
            "pain_point_input": workflow_input.pain_point_input,
            "artifact_a_input": workflow_input.artifact_a_input,
            "artifact_c_input": workflow_input.artifact_c_input,
        }

        # Run workflow
        results = workflow.run(
            input_data=input_data,
            location=workflow_input.location,
            industry=workflow_input.industry
        )

        return WorkflowResponse(
            session_id=workflow.session_memory.session_id,
            status="completed",
            message="Workflow executed successfully",
            results=results
        )

    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/session/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """
    Get the status of a workflow session.

    Args:
        session_id: Session identifier

    Returns:
        Session status and summary
    """
    try:
        if session_id in active_workflows:
            workflow = active_workflows[session_id]
            summary = workflow.session_memory.get_summary()

            return SessionStatus(
                session_id=session_id,
                exists=True,
                summary=summary
            )
        else:
            return SessionStatus(
                session_id=session_id,
                exists=False,
                summary=None
            )

    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/session/{session_id}/outputs")
async def get_session_outputs(session_id: str):
    """
    Get all agent outputs for a session.

    Args:
        session_id: Session identifier

    Returns:
        All agent outputs
    """
    try:
        if session_id not in active_workflows:
            raise HTTPException(status_code=404, detail="Session not found")

        workflow = active_workflows[session_id]
        outputs = workflow.session_memory.get_all_agent_outputs()

        return {
            "session_id": session_id,
            "outputs": outputs
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session outputs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/workflow/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a workflow session.

    Args:
        session_id: Session identifier

    Returns:
        Deletion confirmation
    """
    try:
        if session_id in active_workflows:
            workflow = active_workflows[session_id]
            workflow.clear_session()
            del active_workflows[session_id]

            return {
                "message": f"Session {session_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/sessions")
async def list_sessions():
    """
    List all active workflow sessions.

    Returns:
        List of active session IDs
    """
    return {
        "active_sessions": list(active_workflows.keys()),
        "count": len(active_workflows)
    }


def start_server(
    host: str = None,
    port: int = None,
    reload: bool = False
):
    """
    Start the FastAPI server.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload
    """
    uvicorn.run(
        "src.api.fastapi_app:app",
        host=host or settings.api_host,
        port=port or settings.api_port,
        reload=reload
    )


if __name__ == "__main__":
    start_server(reload=True)
