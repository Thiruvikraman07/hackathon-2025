"""Common models and base classes."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BaseAgentOutput(BaseModel):
    """Base class for all agent outputs."""

    agent_id: str = Field(..., description="Identifier for the agent")
    timestamp: str = Field(..., description="Timestamp of the output")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in the output")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Source(BaseModel):
    """Represents a data source."""

    type: str = Field(..., description="Type of source (document, interview, code, etc.)")
    name: str = Field(..., description="Name or identifier of the source")
    location: Optional[str] = Field(None, description="File path or URL")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class Metric(BaseModel):
    """Represents a measurable metric."""

    name: str = Field(..., description="Metric name")
    value: Optional[float] = Field(None, description="Numeric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    description: Optional[str] = Field(None, description="Description of the metric")
