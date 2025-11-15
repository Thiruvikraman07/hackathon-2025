"""Data models for the hiring assessment system."""
from .common import BaseAgentOutput, Source, Metric
from .strategic_context import (
    StrategicContextOutput,
    StrategyTheme,
    TransformationGoal,
    RiskFactor
)
from .pain_points import (
    PainPointOutput,
    PainPoint,
    ProductivityImpact,
    RootCause
)
from .artifacts import (
    ArtifactInspectorAOutput,
    ArtifactInspectorBOutput,
    Technology,
    ArtifactType,
    ComplexityMetric,
    Dependency,
    ImprovementArea
)
from .collaboration import (
    ArtifactInspectorCOutput,
    TeamMember,
    Interaction,
    CommunicationChannel,
    CollaborationPattern
)
from .requirements import (
    RequirementSynthesizerOutput,
    Skill,
    Capability,
    GrowthIndicator,
    ConflictResolution
)
from .market_intel import (
    MarketIntelligenceOutput,
    MarketAvailability,
    SalaryBenchmark,
    CompetitiveLandscape,
    EmergingSkill,
    SupplyDemandRatio
)

__all__ = [
    # Common
    "BaseAgentOutput",
    "Source",
    "Metric",
    # Strategic Context
    "StrategicContextOutput",
    "StrategyTheme",
    "TransformationGoal",
    "RiskFactor",
    # Pain Points
    "PainPointOutput",
    "PainPoint",
    "ProductivityImpact",
    "RootCause",
    # Artifacts
    "ArtifactInspectorAOutput",
    "ArtifactInspectorBOutput",
    "Technology",
    "ArtifactType",
    "ComplexityMetric",
    "Dependency",
    "ImprovementArea",
    # Collaboration
    "ArtifactInspectorCOutput",
    "TeamMember",
    "Interaction",
    "CommunicationChannel",
    "CollaborationPattern",
    # Requirements
    "RequirementSynthesizerOutput",
    "Skill",
    "Capability",
    "GrowthIndicator",
    "ConflictResolution",
    # Market Intelligence
    "MarketIntelligenceOutput",
    "MarketAvailability",
    "SalaryBenchmark",
    "CompetitiveLandscape",
    "EmergingSkill",
    "SupplyDemandRatio",
]
