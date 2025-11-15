"""Pain point models for Agent 1.2."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .common import BaseAgentOutput, Source


class PainPoint(BaseModel):
    """Represents a pain point or bottleneck."""

    description: str = Field(..., description="Description of the pain point")
    category: str = Field(..., description="Category (technical, process, people, etc.)")
    severity: str = Field(..., description="Severity level (critical, high, medium, low)")
    frequency: Optional[str] = Field(None, description="How often it occurs")
    affected_teams: List[str] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)


class ProductivityImpact(BaseModel):
    """Represents productivity impact of a pain point."""

    pain_point_id: str = Field(..., description="Reference to the pain point")
    estimated_hours_lost: Optional[float] = Field(None, description="Hours lost per week/month")
    team_size_affected: Optional[int] = Field(None, description="Number of people affected")
    financial_impact: Optional[str] = Field(None, description="Estimated financial impact")
    quality_impact: Optional[str] = Field(None, description="Impact on quality")


class RootCause(BaseModel):
    """Represents a root cause analysis."""

    pain_point_id: str = Field(..., description="Reference to the pain point")
    root_cause: str = Field(..., description="Identified root cause")
    contributing_factors: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)


class PainPointOutput(BaseAgentOutput):
    """Output schema for Pain Point Analyzer (Agent 1.2)."""

    critical_pain_points: List[PainPoint] = Field(
        default_factory=list,
        description="Identified pain points prioritized by severity"
    )
    productivity_impacts: Dict[str, ProductivityImpact] = Field(
        default_factory=dict,
        description="Productivity impact analysis for each pain point"
    )
    urgency_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Urgency scores (0-1) for each pain point"
    )
    root_causes: List[RootCause] = Field(
        default_factory=list,
        description="Root cause analysis for major pain points"
    )
