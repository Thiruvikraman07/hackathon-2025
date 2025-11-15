"""Collaboration models for Agent 1.5."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .common import BaseAgentOutput


class TeamMember(BaseModel):
    """Represents a team member in the network."""

    id: str = Field(..., description="Unique identifier")
    role: Optional[str] = Field(None, description="Role or title")
    team: Optional[str] = Field(None, description="Team name")


class Interaction(BaseModel):
    """Represents an interaction between team members."""

    from_member: str = Field(..., description="Source member ID")
    to_member: str = Field(..., description="Target member ID")
    interaction_type: str = Field(..., description="Type of interaction")
    frequency: Optional[float] = Field(None, description="Interaction frequency")
    channel: Optional[str] = Field(None, description="Communication channel")


class CommunicationChannel(BaseModel):
    """Represents a communication channel."""

    name: str = Field(..., description="Channel name (Slack, email, meetings, etc.)")
    usage_frequency: str = Field(..., description="How often used")
    primary_purpose: Optional[str] = Field(None, description="Main use case")
    effectiveness: Optional[str] = Field(None, description="Perceived effectiveness")


class CollaborationPattern(BaseModel):
    """Represents a collaboration pattern."""

    pattern_type: str = Field(..., description="Type of pattern (hub-and-spoke, mesh, etc.)")
    description: str = Field(..., description="Description of the pattern")
    teams_involved: List[str] = Field(default_factory=list)
    strength: Optional[str] = Field(None, description="Pattern strength (strong, moderate, weak)")


class ArtifactInspectorCOutput(BaseAgentOutput):
    """Output schema for Artifact Inspector C (Agent 1.5)."""

    team_members: List[TeamMember] = Field(
        default_factory=list,
        description="Team members in the network"
    )
    interactions: List[Interaction] = Field(
        default_factory=list,
        description="Interactions between team members"
    )
    communication_channels: List[CommunicationChannel] = Field(
        default_factory=list,
        description="Communication channels used"
    )
    collaboration_patterns: List[CollaborationPattern] = Field(
        default_factory=list,
        description="Identified collaboration patterns"
    )
    network_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Network analysis metrics (density, centrality, etc.)"
    )
