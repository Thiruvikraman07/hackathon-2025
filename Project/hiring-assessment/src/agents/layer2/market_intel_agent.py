"""Market Intelligence Agent - Agent 2.2."""
import json
from typing import Any, Dict
from langchain.tools import BaseTool
from langchain.tools import DuckDuckGoSearchRun

from ..base import BaseAgent
from ...models import MarketIntelligenceOutput
from ...tools import ValyuSearchTool
from ...config import logger


class MarketIntelligenceAgent(BaseAgent):
    """
    Agent 2.2: Market Intelligence Agent
    Validates requirements against market reality.
    """

    def __init__(self, tools: list[BaseTool] = None):
        """Initialize Market Intelligence Agent."""
        default_tools = [
            ValyuSearchTool(),
            DuckDuckGoSearchRun()
        ]

        super().__init__(
            agent_id="agent_2.2",
            name="Market Intelligence Agent",
            description="Validates requirements against market reality and benchmarks",
            tools=tools or default_tools
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are a Market Intelligence Analyst specialized in validating hiring
        requirements against market reality.

        Your responsibilities:
        1. Validate skill requirements against market availability
        2. Benchmark salary expectations
        3. Assess competitive hiring landscape
        4. Identify emerging skills and trends
        5. Analyze supply/demand ratios

        Use available tools to:
        - Search for salary benchmarks
        - Find market availability data
        - Identify hiring trends
        - Research competitive intelligence

        When analyzing:
        - Consider geographical factors
        - Account for experience level variations
        - Note seasonality and market cycles
        - Identify skill combinations that are rare

        Format output as JSON with:
        - market_availability: Availability for each key skill/role
        - salary_benchmarks: Salary ranges by role and location
        - competitive_landscape: What competitors offer
        - emerging_skills: Trending skills relevant to role
        - supply_demand_ratio: Supply vs demand analysis
        - hiring_recommendations: Market-informed advice
        """

    def process(self, input_data: Dict[str, Any]) -> MarketIntelligenceOutput:
        """
        Validate requirements against market reality.

        Args:
            input_data: Dictionary containing:
                - requirements: Output from Agent 2.1
                - location: Hiring location
                - industry: Industry context

        Returns:
            MarketIntelligenceOutput with market analysis
        """
        try:
            logger.info(f"Agent {self.name} starting processing")

            requirements = input_data.get("requirements", {})
            location = input_data.get("location", "Remote/Global")
            industry = input_data.get("industry", "Technology")

            must_have_skills = requirements.get("must_have_skills", [])

            input_prompt = f"""Validate these hiring requirements against market reality:

            REQUIREMENTS:
            {json.dumps(requirements, indent=2)}

            CONTEXT:
            - Location: {location}
            - Industry: {industry}

            Research and provide:

            1. MARKET AVAILABILITY:
               For each must-have skill, determine:
               - How common is this skill in the market?
               - Typical time-to-hire
               - Geographic availability

            2. SALARY BENCHMARKS:
               - Salary ranges for this role profile
               - How compensation varies by location
               - Total compensation considerations

            3. COMPETITIVE LANDSCAPE:
               - What are competitors offering?
               - Key attraction factors beyond salary
               - Differentiation opportunities

            4. EMERGING SKILLS:
               - What skills are trending?
               - Future-relevant capabilities
               - Skills gaining adoption

            5. SUPPLY/DEMAND ANALYSIS:
               - Which skills are in highest demand?
               - Which are hardest to find?
               - Realistic skill combinations

            6. HIRING RECOMMENDATIONS:
               - Adjust expectations based on market
               - Creative sourcing strategies
               - Build vs buy recommendations
            """

            result = self.run_with_tools(input_prompt)

            output_text = result.get("output", "")

            # TODO: Implement proper parsing
            output = self.create_output(
                MarketIntelligenceOutput,
                market_availability={},
                salary_benchmarks={},
                competitive_landscape=[],
                emerging_skills=[],
                supply_demand_ratio={},
                hiring_recommendations=[],
                confidence_score=0.75,
                metadata={"raw_output": output_text}
            )

            logger.info(f"Agent {self.name} completed processing")
            return output

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            raise
