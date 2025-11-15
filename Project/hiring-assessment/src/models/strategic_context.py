"""Strategic context models for Agent 1.1."""
from typing import List, Optional
from pydantic import BaseModel, Field

from .common import BaseAgentOutput, Source, Metric


class StrategyTheme(BaseModel):
    """Represents a strategic business theme."""

    name: str = Field(..., description="Name of the strategic theme")
    description: str = Field(..., description="Detailed description")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    timeline: Optional[str] = Field(None, description="Expected timeline")
    sources: List[Source] = Field(default_factory=list)


class TransformationGoal(BaseModel):
    """Represents a transformation initiative."""

    goal: str = Field(..., description="Description of the transformation goal")
    current_state: str = Field(..., description="Current state description")
    target_state: str = Field(..., description="Desired future state")
    key_milestones: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)


class RiskFactor(BaseModel):
    """Represents a potential risk."""

    risk: str = Field(..., description="Description of the risk")
    impact: str = Field(..., description="Potential impact (high, medium, low)")
    probability: str = Field(..., description="Likelihood (high, medium, low)")
    mitigation: Optional[str] = Field(None, description="Mitigation strategy")


class StrategicContextOutput(BaseAgentOutput):
    """Output schema for Strategic Context Extractor (Agent 1.1)."""

    strategic_themes: List[StrategyTheme] = Field(
        default_factory=list,
        description="High-level strategic themes identified"
    )
    success_metrics: List[Metric] = Field(
        default_factory=list,
        description="Key performance indicators for success"
    )
    transformation_goals: List[TransformationGoal] = Field(
        default_factory=list,
        description="Transformation initiatives and goals"
    )
    risk_factors: List[RiskFactor] = Field(
        default_factory=list,
        description="Identified risk factors"
    )
