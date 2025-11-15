"""Requirement Synthesizer - Agent 2.1."""
import json
from typing import Any, Dict, List

from ..base import BaseAgent
from ...models import RequirementSynthesizerOutput
from ...config import logger


class RequirementSynthesizer(BaseAgent):
    """
    Agent 2.1: Requirement Synthesizer
    Merges inputs from Layer 1 agents and resolves conflicts.
    """

    def __init__(self):
        """Initialize Requirement Synthesizer."""
        super().__init__(
            agent_id="agent_2.1",
            name="Requirement Synthesizer",
            description="Synthesizes requirements from all Layer 1 inputs",
            tools=[]  # This agent uses reasoning, not tools
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are a Requirements Synthesizer specialized in merging diverse inputs
        into coherent hiring requirements.

        Your responsibilities:
        1. Merge outputs from all Layer 1 agents
        2. Resolve conflicts and contradictions
        3. Weight requirements by importance and strategic alignment
        4. Distinguish must-haves from nice-to-haves
        5. Identify performance multipliers and growth indicators

        When synthesizing:
        - Align technical requirements with strategic goals
        - Consider pain points as indicators of needed capabilities
        - Balance current needs with future growth
        - Resolve conflicts through strategic prioritization

        Input sources:
        - Strategic Context (Agent 1.1): Business objectives and goals
        - Pain Points (Agent 1.2): Current challenges and bottlenecks
        - Artifacts A (Agent 1.3): Current technical capabilities
        - Artifacts B (Agent 1.4): Improvement areas
        - Artifacts C (Agent 1.5): Collaboration patterns
        - Best Practices (Agent 1.6): Industry standards

        Format output as JSON with:
        - must_have_skills: Essential skills with justifications
        - performance_multipliers: Capabilities that amplify effectiveness
        - growth_indicators: Signs candidate can evolve
        - nice_to_have_skills: Desirable but not essential
        - conflicts_resolved: How contradictions were handled
        - priority_ranking: Prioritized requirements list
        """

    def process(self, input_data: Dict[str, Any]) -> RequirementSynthesizerOutput:
        """
        Synthesize requirements from Layer 1 outputs.

        Args:
            input_data: Dictionary containing all Layer 1 agent outputs

        Returns:
            RequirementSynthesizerOutput with synthesized requirements
        """
        try:
            logger.info(f"Agent {self.name} starting processing")

            # Extract Layer 1 outputs
            strategic_context = input_data.get("strategic_context", {})
            pain_points = input_data.get("pain_points", {})
            artifacts_a = input_data.get("artifacts_a", {})
            artifacts_b = input_data.get("artifacts_b", {})
            artifacts_c = input_data.get("artifacts_c", {})
            best_practices = input_data.get("best_practices", {})

            input_prompt = f"""Synthesize hiring requirements from the following inputs:

            1. STRATEGIC CONTEXT:
            {json.dumps(strategic_context, indent=2)}

            2. PAIN POINTS & BOTTLENECKS:
            {json.dumps(pain_points, indent=2)}

            3. CURRENT TECHNICAL CAPABILITIES:
            {json.dumps(artifacts_a, indent=2)}

            4. IMPROVEMENT AREAS:
            {json.dumps(artifacts_b, indent=2)}

            5. COLLABORATION PATTERNS:
            {json.dumps(artifacts_c, indent=2)}

            6. BEST PRACTICES:
            {json.dumps(best_practices, indent=2)}

            Synthesize these inputs into coherent hiring requirements:

            1. MUST-HAVE SKILLS: What is absolutely necessary?
               - Link each skill to strategic goals or critical pain points
               - Specify proficiency levels
               - Provide clear justifications

            2. PERFORMANCE MULTIPLIERS: What amplifies team effectiveness?
               - Capabilities that unlock team potential
               - Skills that address multiple pain points
               - Enablers of transformation goals

            3. GROWTH INDICATORS: What shows candidate can evolve?
               - Learning agility markers
               - Adaptability signals
               - Future-readiness indicators

            4. CONFLICTS RESOLUTION: Document any conflicts found and how resolved
               - Trade-offs made
               - Prioritization rationale

            Ensure requirements are:
            - Specific and measurable
            - Aligned with strategic priorities
            - Realistic for the market
            - Balanced between current needs and future growth
            """

            result = self.run_simple(input_prompt)

            # TODO: Implement proper parsing
            output = self.create_output(
                RequirementSynthesizerOutput,
                must_have_skills=[],
                performance_multipliers=[],
                growth_indicators={},
                nice_to_have_skills=[],
                conflicts_resolved=[],
                priority_ranking=[],
                confidence_score=0.85,
                metadata={"raw_output": result}
            )

            logger.info(f"Agent {self.name} completed processing")
            return output

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            raise
