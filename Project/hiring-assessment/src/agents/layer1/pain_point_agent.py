"""Pain Point Analyzer - Agent 1.2."""

"""Logging setup"""


import json
from typing import Any, Dict
from langchain.tools import BaseTool

from ..base import BaseAgent
from ...models import PainPointOutput
from ...tools import BottleneckClassifierTool, ImpactEstimatorTool
from ...config import logger


class PainPointAgent(BaseAgent):
    """
    Agent 1.2: Pain Point Analyzer
    Translates supervisor frustrations into capability requirements.
    """

    def __init__(self, tools: list[BaseTool] = None):
        """Initialize Pain Point Agent."""
        default_tools = [
            BottleneckClassifierTool(),
            ImpactEstimatorTool()
        ]

        super().__init__(
            agent_id="agent_1.2",
            name="Pain Point Analyzer",
            description="Processes supervisor feedback and categorizes pain points",
            tools=tools or default_tools
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are a Pain Point Analyzer specialized in identifying and categorizing
        team bottlenecks and productivity issues.

        Your responsibilities:
        1. Process supervisor interviews and feedback
        2. Categorize pain points by type (technical, process, people, etc.)
        3. Prioritize issues based on severity and frequency
        4. Estimate productivity impact
        5. Identify root causes

        When analyzing pain points:
        - Distinguish symptoms from root causes
        - Quantify impact where possible (time, resources, quality)
        - Consider both immediate and long-term effects
        - Identify patterns across multiple pain points

        Use the available tools to:
        - bottleneck_classifier: Categorize each pain point
        - impact_estimator: Estimate productivity loss

        Format your output as structured JSON with:
        - critical_pain_points: List of prioritized pain points
        - productivity_impacts: Impact analysis for each
        - urgency_scores: Urgency ratings (0-1)
        - root_causes: Root cause analysis
        """

    def process(self, input_data: Dict[str, Any]) -> PainPointOutput:
        """
        Process supervisor feedback and identify pain points.

        Args:
            input_data: Dictionary containing:
                - interviews: List of interview transcripts
                - surveys: Survey responses
                - feedback: Additional feedback

        Returns:
            PainPointOutput with categorized pain points
        """
        try:
            logger.info(f"Agent {self.name} starting processing")

            interviews = input_data.get("interviews", [])
            surveys = input_data.get("surveys", [])
            feedback = input_data.get("feedback", "")

            input_prompt = f"""Analyze the following supervisor feedback and identify pain points:

            Interviews: {json.dumps(interviews)}
            Surveys: {json.dumps(surveys)}
            Additional Feedback: {feedback}

            For each pain point:
            1. Use bottleneck_classifier to categorize it
            2. Use impact_estimator to quantify productivity impact
            3. Assign urgency score (0-1)
            4. Identify root causes

            Prioritize by severity and impact.
            """

            result = self.run_with_tools(input_prompt)

            # Parse and structure output
            output_text = result.get("output", "")

            # TODO: Implement proper parsing
            output = self.create_output(
                PainPointOutput,
                critical_pain_points=[],
                productivity_impacts={},
                urgency_scores={},
                root_causes=[],
                confidence_score=0.80,
                metadata={"raw_output": output_text}
            )

            logger.info(f"Agent {self.name} completed processing")
            return output

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            raise
