"""Market intelligence models for Agent 2.2."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .common import BaseAgentOutput, Source


class MarketAvailability(BaseModel):
    """Represents market availability for a skill/role."""

    skill_or_role: str = Field(..., description="Skill or role name")
    availability: str = Field(..., description="Availability (abundant, moderate, scarce)")
    geographical_notes: Optional[str] = Field(None, description="Geographic availability notes")
    time_to_hire: Optional[str] = Field(None, description="Expected time to fill")


class SalaryBenchmark(BaseModel):
    """Represents salary benchmark data."""

    role_title: str = Field(..., description="Role or position title")
    location: str = Field(..., description="Location/market")
    min_salary: Optional[float] = Field(None, description="Minimum salary")
    median_salary: Optional[float] = Field(None, description="Median salary")
    max_salary: Optional[float] = Field(None, description="Maximum salary")
    currency: str = Field(default="USD", description="Currency")
    sources: List[Source] = Field(default_factory=list)


class CompetitiveLandscape(BaseModel):
    """Represents competitive landscape information."""

    competitor_type: str = Field(..., description="Type of competitor")
    attraction_factors: List[str] = Field(default_factory=list, description="What they offer")
    differentiation_opportunities: List[str] = Field(
        default_factory=list,
        description="How to differentiate"
    )


class EmergingSkill(BaseModel):
    """Represents an emerging skill in the market."""

    skill: str = Field(..., description="Emerging skill name")
    trend_direction: str = Field(..., description="Trend (rising, stable, declining)")
    relevance_to_role: Optional[str] = Field(None, description="Relevance to this role")
    adoption_timeline: Optional[str] = Field(None, description="Expected adoption timeline")


class SupplyDemandRatio(BaseModel):
    """Represents supply/demand for a skill."""

    skill: str = Field(..., description="Skill name")
    demand_level: str = Field(..., description="Demand level (very high, high, medium, low)")
    supply_level: str = Field(..., description="Supply level (very high, high, medium, low)")
    ratio: Optional[float] = Field(None, description="Numeric ratio if available")
    market_insights: Optional[str] = Field(None, description="Additional insights")


class MarketIntelligenceOutput(BaseAgentOutput):
    """Output schema for Market Intelligence Agent (Agent 2.2)."""

    market_availability: Dict[str, MarketAvailability] = Field(
        default_factory=dict,
        description="Market availability for required skills"
    )
    salary_benchmarks: Dict[str, SalaryBenchmark] = Field(
        default_factory=dict,
        description="Salary benchmarks for the role"
    )
    competitive_landscape: List[CompetitiveLandscape] = Field(
        default_factory=list,
        description="Competitive hiring landscape"
    )
    emerging_skills: List[EmergingSkill] = Field(
        default_factory=list,
        description="Emerging skills relevant to the role"
    )
    supply_demand_ratio: Dict[str, SupplyDemandRatio] = Field(
        default_factory=dict,
        description="Supply/demand analysis for key skills"
    )
    hiring_recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations based on market intelligence"
    )
