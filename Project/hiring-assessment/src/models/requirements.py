"""Requirements models for Agent 2.1."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .common import BaseAgentOutput, Source


class Skill(BaseModel):
    """Represents a required skill."""

    name: str = Field(..., description="Skill name")
    category: str = Field(..., description="Category (technical, soft, domain, etc.)")
    proficiency_level: str = Field(..., description="Required level (beginner, intermediate, expert)")
    justification: str = Field(..., description="Why this skill is needed")
    sources: List[Source] = Field(default_factory=list)


class Capability(BaseModel):
    """Represents a capability that amplifies team effectiveness."""

    capability: str = Field(..., description="Description of the capability")
    impact_area: str = Field(..., description="Where this capability has impact")
    multiplier_effect: Optional[str] = Field(None, description="How this amplifies effectiveness")
    examples: List[str] = Field(default_factory=list)


class GrowthIndicator(BaseModel):
    """Represents indicators that candidate can evolve with role."""

    indicator: str = Field(..., description="Growth indicator")
    category: str = Field(..., description="Category (learning agility, adaptability, etc.)")
    assessment_method: Optional[str] = Field(None, description="How to assess this")
    importance: str = Field(..., description="Importance level (high, medium, low)")


class ConflictResolution(BaseModel):
    """Represents how conflicting requirements were resolved."""

    conflict_description: str = Field(..., description="Description of the conflict")
    resolution: str = Field(..., description="How it was resolved")
    trade_offs: List[str] = Field(default_factory=list)


class RequirementSynthesizerOutput(BaseAgentOutput):
    """Output schema for Requirement Synthesizer (Agent 2.1)."""

    must_have_skills: List[Skill] = Field(
        default_factory=list,
        description="Essential skills required for the role"
    )
    performance_multipliers: List[Capability] = Field(
        default_factory=list,
        description="Capabilities that amplify team effectiveness"
    )
    growth_indicators: Dict[str, GrowthIndicator] = Field(
        default_factory=dict,
        description="Signs candidate can evolve with role"
    )
    nice_to_have_skills: List[Skill] = Field(
        default_factory=list,
        description="Desirable but not essential skills"
    )
    conflicts_resolved: List[ConflictResolution] = Field(
        default_factory=list,
        description="How conflicts were resolved"
    )
    priority_ranking: List[str] = Field(
        default_factory=list,
        description="Prioritized list of requirements"
    )
