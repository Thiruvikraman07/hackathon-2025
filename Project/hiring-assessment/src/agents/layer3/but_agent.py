"""BUT Agent - Agent 3.1."""
import json
from typing import Any, Dict, List

from ..base import BaseAgent
from ...config import logger


class ButAgent(BaseAgent):
    """
    Agent 3.1: "BUT" Agent
    Finds problems, conflicts, and feasibility issues.
    """

    def __init__(self):
        """Initialize BUT Agent."""
        super().__init__(
            agent_id="agent_3.1",
            name="BUT Agent",
            description="Identifies conflicts, contradictions, and feasibility issues",
            tools=[]  # Critical thinking agent, no tools needed
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are the "BUT" Agent - a critical analyst specialized in finding problems,
        conflicts, contradictions, and feasibility issues.

        Your role is to be skeptical and challenge assumptions. Ask "but what about...?" for:

        1. CONFLICTS & CONTRADICTIONS:
           - Do requirements conflict with each other?
           - Are there contradictions between layers?
           - Do strategic goals align with tactical needs?

        2. FEASIBILITY ISSUES:
           - Is this realistic given market constraints?
           - Can these requirements coexist in one person?
           - Is the timeline achievable?
           - Are salary expectations aligned with requirements?

        3. HIDDEN ASSUMPTIONS:
           - What assumptions are being made?
           - Are they valid?
           - What could go wrong?

        4. TRADE-OFFS NOT CONSIDERED:
           - What are we optimizing for?
           - What are we sacrificing?
           - Are the trade-offs worth it?

        5. GAPS & MISSING CONSIDERATIONS:
           - What's not being addressed?
           - What questions haven't been asked?
           - What data is missing?

        Be constructive in your criticism:
        - Identify the problem clearly
        - Explain why it's a problem
        - Suggest how to address it
        - Rate severity (critical, high, medium, low)

        Format output as JSON with:
        - conflicts: List of identified conflicts
        - feasibility_issues: Feasibility concerns
        - hidden_assumptions: Unvalidated assumptions
        - trade_offs: Unacknowledged trade-offs
        - gaps: Missing considerations
        - recommendations: How to address issues
        """

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze outputs for conflicts and feasibility issues.

        Args:
            input_data: Dictionary containing:
                - requirements: Synthesized requirements (Agent 2.1)
                - market_intel: Market intelligence (Agent 2.2)
                - all_layer1_outputs: All Layer 1 outputs

        Returns:
            Dictionary with identified issues and recommendations
        """
        try:
            logger.info(f"Agent {self.name} starting processing")

            requirements = input_data.get("requirements", {})
            market_intel = input_data.get("market_intel", {})
            layer1_outputs = input_data.get("all_layer1_outputs", {})

            input_prompt = f"""Critically analyze these outputs for problems:

            SYNTHESIZED REQUIREMENTS:
            {json.dumps(requirements, indent=2)}

            MARKET INTELLIGENCE:
            {json.dumps(market_intel, indent=2)}

            LAYER 1 INPUTS:
            {json.dumps(layer1_outputs, indent=2)}

            Apply critical analysis:

            1. CONFLICTS & CONTRADICTIONS:
               - Do requirements conflict with each other?
               - Do strategic goals conflict with pain points?
               - Are there internal inconsistencies?

            2. FEASIBILITY ISSUES:
               - Can we realistically find someone with these requirements?
               - Do market conditions support these expectations?
               - Is the skill combination too rare?
               - Are salary expectations realistic?
               - Is the timeline achievable?

            3. HIDDEN ASSUMPTIONS:
               - What assumptions underlie these requirements?
               - Are they validated?
               - Which could be wrong?

            4. TRADE-OFFS NOT ACKNOWLEDGED:
               - What are we optimizing for?
               - What are we giving up?
               - Are alternative approaches being considered?

            5. GAPS & MISSING ELEMENTS:
               - What important factors aren't addressed?
               - What data is missing?
               - What risks aren't considered?

            For each issue found:
            - Describe it clearly
            - Explain the impact
            - Rate severity
            - Suggest resolution

            Be thorough and skeptical. This is quality assurance.
            """

            result = self.run_simple(input_prompt)

            # Create output
            output = {
                "agent_id": self.agent_id,
                "conflicts": [],
                "feasibility_issues": [],
                "hidden_assumptions": [],
                "trade_offs": [],
                "gaps": [],
                "recommendations": [],
                "overall_assessment": "",
                "metadata": {"raw_output": result}
            }

            logger.info(f"Agent {self.name} completed processing")
            return output

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            raise
