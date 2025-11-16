"""
Step-by-Step Pipeline Execution Tracker

Provides detailed tracking of pipeline execution steps with:
- Input/output tracking for each step
- Timing and performance metrics
- Error tracking and debugging info
- Integration with LangSmith
- Frontend-ready JSON output
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from contextlib import contextmanager
import time
import traceback
import os


class StepType(str, Enum):
    """Types of steps in the pipeline"""
    DETECTION = "detection"
    METADATA = "metadata_fetch"
    FILE_STRUCTURE = "file_structure_fetch"
    CODE_FETCH = "code_fetch"
    AGENT_REASONING = "agent_reasoning"
    VALIDATION = "validation"
    OUTPUT_GENERATION = "output_generation"
    INITIALIZATION = "initialization"


class StepStatus(str, Enum):
    """Status of each step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepData(BaseModel):
    """Data for a single execution step"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    step_id: str = Field(description="Unique step identifier")
    step_type: StepType
    step_name: str = Field(description="Human-readable step name")
    status: StepStatus = StepStatus.PENDING

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None

    # Input/Output
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)

    # Reasoning & Metadata
    reason: Optional[str] = None
    decision_point: Optional[str] = None
    tool_used: Optional[str] = None

    # Error handling
    error: Optional[str] = None
    error_traceback: Optional[str] = None

    # Metrics
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    files_processed: Optional[int] = None


class PipelineExecution(BaseModel):
    """Complete pipeline execution tracking"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    execution_id: str
    pipeline_name: str = "pipeline1_jd_generator"

    # Configuration
    repository_type: Optional[Literal["github", "local"]] = None
    repository_path: str
    job_title: str
    salary_range: Optional[str] = None
    additional_requirements: List[str] = Field(default_factory=list)

    # Execution tracking
    steps: List[StepData] = Field(default_factory=list)
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None

    # Status
    overall_status: StepStatus = StepStatus.IN_PROGRESS
    success: bool = False

    # LangSmith integration
    langsmith_run_id: Optional[str] = None
    langsmith_url: Optional[str] = None
    langsmith_project: Optional[str] = None

    # Aggregated metrics
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_files_analyzed: int = 0

    # Output
    output_file_path: Optional[str] = None
    output_size_bytes: Optional[int] = None

    def to_frontend_json(self) -> Dict[str, Any]:
        """Convert to frontend-friendly JSON format"""
        return {
            "executionId": self.execution_id,
            "pipeline": self.pipeline_name,
            "repository": {
                "type": self.repository_type,
                "path": self.repository_path
            },
            "config": {
                "jobTitle": self.job_title,
                "salaryRange": self.salary_range,
                "additionalRequirements": self.additional_requirements
            },
            "timeline": [
                {
                    "id": step.step_id,
                    "type": step.step_type,
                    "name": step.step_name,
                    "status": step.status,
                    "startTime": step.start_time.isoformat() if step.start_time else None,
                    "endTime": step.end_time.isoformat() if step.end_time else None,
                    "durationMs": step.duration_ms,
                    "input": step.input_data,
                    "output": step.output_data,
                    "reason": step.reason,
                    "decisionPoint": step.decision_point,
                    "toolUsed": step.tool_used,
                    "error": step.error,
                    "metrics": {
                        "tokens": step.tokens_used,
                        "cost": step.cost_usd,
                        "filesProcessed": step.files_processed
                    }
                }
                for step in self.steps
            ],
            "summary": {
                "status": self.overall_status,
                "success": self.success,
                "startTime": self.start_time.isoformat(),
                "endTime": self.end_time.isoformat() if self.end_time else None,
                "totalDurationMs": self.total_duration_ms,
                "totalTokens": self.total_tokens,
                "totalCostUsd": self.total_cost_usd,
                "filesAnalyzed": self.total_files_analyzed
            },
            "langsmith": {
                "runId": self.langsmith_run_id,
                "url": self.langsmith_url,
                "project": self.langsmith_project
            },
            "output": {
                "filePath": self.output_file_path,
                "sizeBytes": self.output_size_bytes
            }
        }

    def get_summary_text(self) -> str:
        """Get human-readable summary"""
        status_emoji = "✅" if self.success else "❌"
        duration = f"{self.total_duration_ms/1000:.2f}s" if self.total_duration_ms else "N/A"

        summary = f"""
{status_emoji} Pipeline Execution Summary
{"="*60}
Execution ID: {self.execution_id}
Repository: {self.repository_path} ({self.repository_type or 'unknown'})
Job Title: {self.job_title}
Status: {self.overall_status}
Duration: {duration}

Steps Executed: {len(self.steps)}
Files Analyzed: {self.total_files_analyzed}
Total Tokens: {self.total_tokens}
Total Cost: ${self.total_cost_usd:.4f}

Output: {self.output_file_path or 'N/A'}
"""

        if self.langsmith_url:
            summary += f"\nLangSmith Trace: {self.langsmith_url}\n"

        return summary


class StepTracker:
    """Context manager for tracking pipeline steps"""

    def __init__(self, execution: PipelineExecution, verbose: bool = True):
        self.execution = execution
        self.current_step: Optional[StepData] = None
        self.verbose = verbose

    @contextmanager
    def track_step(
        self,
        step_type: StepType,
        step_name: str,
        input_data: Dict[str, Any] = None,
        reason: str = None,
        tool_used: str = None
    ):
        """Track a single step execution"""
        step = StepData(
            step_id=f"step_{len(self.execution.steps) + 1}",
            step_type=step_type,
            step_name=step_name,
            input_data=input_data or {},
            reason=reason,
            tool_used=tool_used,
            start_time=datetime.now(),
            status=StepStatus.IN_PROGRESS
        )

        self.execution.steps.append(step)
        self.current_step = step

        if self.verbose:
            print(f"\n🔄 {step_name}...")
            if reason:
                print(f"   💡 {reason}")

        start = time.time()

        try:
            yield step

            # Success
            step.status = StepStatus.SUCCESS
            step.end_time = datetime.now()
            step.duration_ms = (time.time() - start) * 1000

            if self.verbose:
                print(f"   ✅ Completed in {step.duration_ms:.0f}ms")

        except Exception as e:
            # Failure
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.error_traceback = traceback.format_exc()
            step.end_time = datetime.now()
            step.duration_ms = (time.time() - start) * 1000

            if self.verbose:
                print(f"   ❌ Failed: {str(e)}")

            raise

        finally:
            self.current_step = None

    def update_output(self, output_data: Dict[str, Any]):
        """Update current step's output"""
        if self.current_step:
            self.current_step.output_data.update(output_data)

    def update_metrics(self, tokens: int = None, cost: float = None, files: int = None):
        """Update current step's metrics"""
        if self.current_step:
            if tokens is not None:
                self.current_step.tokens_used = tokens
                self.execution.total_tokens += tokens
            if cost is not None:
                self.current_step.cost_usd = cost
                self.execution.total_cost_usd += cost
            if files is not None:
                self.current_step.files_processed = files
                self.execution.total_files_analyzed += files

    def add_decision_point(self, decision: str):
        """Add decision point to current step"""
        if self.current_step:
            self.current_step.decision_point = decision

    def finalize(self, success: bool = True):
        """Finalize execution tracking"""
        self.execution.end_time = datetime.now()
        self.execution.total_duration_ms = (
            (self.execution.end_time - self.execution.start_time).total_seconds() * 1000
        )
        self.execution.success = success
        self.execution.overall_status = StepStatus.SUCCESS if success else StepStatus.FAILED


def get_langsmith_url(run_id: str, project: str = None) -> Optional[str]:
    """Get LangSmith URL for a run"""
    try:
        from langsmith import Client

        if not os.getenv('LANGSMITH_API_KEY'):
            return None

        ls_client = Client()
        run = ls_client.read_run(run_id)
        return run.url
    except Exception:
        # Fallback to generic URL
        if project:
            return f"https://smith.langchain.com/o/projects/p/{project}/r/{run_id}"
        return f"https://smith.langchain.com"
