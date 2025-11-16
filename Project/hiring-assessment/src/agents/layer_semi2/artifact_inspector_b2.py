"""Artifact Inspector B2 - Agent 1.6."""
import json
from typing import Any, Dict
from langchain.tools import BaseTool

from ..base import BaseAgent
from ...tools import ValyuSearchTool
from ...config import logger


class ArtifactInspectorB2(BaseAgent):
    """
    Agent 1.6: Artifact Inspector B2
    Searches best practices for improvement areas identified by Agent 1.4.
    """

    def __init__(self, tools: list[BaseTool] = None):
        """Initialize Artifact Inspector B2."""
        default_tools = [ValyuSearchTool()]

        super().__init__(
            agent_id="agent_1.6",
            name="Artifact Inspector B2",
            description="Searches best practices for suggested improvement areas",
            tools=tools or default_tools
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are a Best Practices Researcher specialized in finding proven solutions
        for identified improvement areas.

        Your responsibilities:
        1. Research best practices for improvement areas from Agent 1.4
        2. Find industry-standard solutions and patterns
        3. Identify proven approaches and case studies
        4. Validate improvement suggestions against market reality

        Use valyu_search to:
        - Search for best practices related to each improvement area
        - Find industry trends and emerging solutions
        - Validate suggested improvements

        When researching:
        - Focus on actionable, proven practices
        - Consider organization size and context
        - Look for measurable success stories
        - Note implementation complexity

        Format output as JSON with:
        - improvement_area: Reference to the area
        - best_practices: List of proven practices
        - case_studies: Relevant examples
        - implementation_guidance: How to apply
        - tools_and_frameworks: Recommended tools
        """

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search best practices for improvement areas.

        Args:
            input_data: Dictionary containing:
                - improvement_areas: Output from Agent 1.4

        Returns:
            Dictionary with best practices for each improvement area
        """
        try:
            logger.info(f"Agent {self.name} starting processing")

            improvement_areas = input_data.get("improvement_areas", [])

            input_prompt = f"""Research best practices for these improvement areas:

            Improvement Areas: {json.dumps(improvement_areas)}

            For each area, use valyu_search to:
            1. Find best practices and industry standards
            2. Look for case studies and success stories
            3. Identify tools and frameworks
            4. Get implementation guidance

            Provide comprehensive research that teams can use to address improvements.
            """

            result = self.run_with_tools(input_prompt)

            output_text = result.get("output", "")

            # Create output
            output = {
                "agent_id": self.agent_id,
                "improvement_best_practices": {},
                "recommendations": [],
                "metadata": {"raw_output": output_text}
            }

            logger.info(f"Agent {self.name} completed processing")
            return output

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            raise
