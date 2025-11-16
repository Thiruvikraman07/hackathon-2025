"""Strategic Context Extractor - Agent 1.1."""
import json
from typing import Any, Dict
from langchain.tools import BaseTool

from ..base import BaseAgent
from ...models import StrategicContextOutput
from ...tools import DocumentParserTool
from ...memory import VectorMemory
from ...config import logger


class StrategicContextAgent(BaseAgent):
    """
    Agent 1.1: Strategic Context Extractor
    Maps high-level "why" to concrete business outcomes.
    """

    def __init__(self, tools: list[BaseTool] = None):
        """Initialize Strategic Context Agent."""
        default_tools = [DocumentParserTool()]

        super().__init__(
            agent_id="agent_1.1",
            name="Strategic Context Extractor",
            description="Analyzes strategic business objectives and transformation initiatives",
            tools=tools or default_tools
        )

        # Initialize long-term memory for strategic themes
        self.long_term_memory = VectorMemory(collection_name="strategic_context")

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are a Strategic Context Extractor specialized in analyzing business documents
        to identify strategic themes, transformation goals, success metrics, and risk factors.

        Your responsibilities:
        1. Analyze strategic business objectives from documents
        2. Identify transformation initiatives and their goals
        3. Extract success metrics and KPIs
        4. Identify potential risk factors

        When analyzing documents:
        - Focus on high-level strategic themes, not tactical details
        - Connect initiatives to business outcomes
        - Identify both explicit and implicit goals
        - Consider risks and constraints

        Format your output as a structured JSON with the following fields:
        - strategic_themes: List of strategic themes with descriptions and priorities
        - success_metrics: Key performance indicators
        - transformation_goals: Transformation initiatives with current/target states
        - risk_factors: Identified risks with impact and probability
        """

    def process(self, input_data: Dict[str, Any]) -> StrategicContextOutput:
        """
        Process input documents and extract strategic context.

        Args:
            input_data: Dictionary containing:
                - documents: List of document paths or content
                - additional_context: Optional additional context

        Returns:
            StrategicContextOutput with extracted information
        """
        try:
            logger.info(f"Agent {self.name} starting processing")

            documents = input_data.get("documents", [])
            additional_context = input_data.get("additional_context", "")

            # Build input prompt
            input_prompt = f"""Analyze the following strategic documents and extract:
            1. Strategic themes and priorities
            2. Success metrics and KPIs
            3. Transformation goals (current state -> target state)
            4. Risk factors

            Documents: {json.dumps(documents)}
            Additional Context: {additional_context}

            Provide a comprehensive strategic analysis.
            """

            # Run agent with tools
            result = self.run_with_tools(input_prompt)

            # Parse the output (this is simplified - you'd need proper parsing)
            output_text = result.get("output", "")

            # Create structured output
            # TODO: Implement proper parsing of LLM output to structured format
            output = self.create_output(
                StrategicContextOutput,
                strategic_themes=[],
                success_metrics=[],
                transformation_goals=[],
                risk_factors=[],
                confidence_score=0.85,
                metadata={"raw_output": output_text}
            )

            # Store strategic themes in long-term memory
            for theme in output.strategic_themes:
                self.long_term_memory.store(
                    text=f"{theme.name}: {theme.description}",
                    metadata={
                        "type": "strategic_theme",
                        "priority": theme.priority,
                        "agent_id": self.agent_id
                    }
                )

            logger.info(f"Agent {self.name} completed processing")
            return output

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            raise
