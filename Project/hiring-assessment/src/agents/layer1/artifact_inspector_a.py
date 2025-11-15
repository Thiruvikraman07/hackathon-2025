"""Artifact Inspector A - Agent 1.3."""
import json
from typing import Any, Dict
from langchain.tools import BaseTool

from ..base import BaseAgent
from ...models import ArtifactInspectorAOutput
from ...tools import CodeAnalyzerTool, DocumentScannerTool, ProcessMinerTool
from ...config import logger


class ArtifactInspectorA(BaseAgent):
    """
    Agent 1.3: Artifact Inspector A
    Examines actual deliverables and codebase.
    """

    def __init__(self, tools: list[BaseTool] = None):
        """Initialize Artifact Inspector A."""
        default_tools = [
            CodeAnalyzerTool(),
            DocumentScannerTool(),
            ProcessMinerTool()
        ]

        super().__init__(
            agent_id="agent_1.3",
            name="Artifact Inspector A",
            description="Analyzes code repositories, documents, and deliverables",
            tools=tools or default_tools
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are an Artifact Inspector specialized in analyzing technical deliverables,
        codebases, and documentation.

        Your responsibilities:
        1. Analyze code repositories for technology stack and patterns
        2. Examine document types and complexity
        3. Identify quality patterns and technical debt
        4. Extract dependencies and integrations

        Use the available tools:
        - code_analyzer: Parse code for languages, frameworks, patterns, complexity
        - document_scanner: Analyze document types and organization
        - process_miner: Extract workflows from tool logs

        When analyzing:
        - Identify not just what is used, but how well it's used
        - Look for patterns that indicate team capabilities
        - Note quality indicators and areas of technical debt
        - Consider system architecture and dependencies

        Format output as JSON with:
        - tech_stack: Technologies and tools used
        - artifact_types: Types of deliverables
        - complexity: Complexity measurements
        - dependencies: External dependencies
        """

    def process(self, input_data: Dict[str, Any]) -> ArtifactInspectorAOutput:
        """
        Process artifacts and extract technical information.

        Args:
            input_data: Dictionary containing:
                - repo_path: Path to code repository
                - docs_path: Path to documentation
                - log_sources: Log sources for process mining

        Returns:
            ArtifactInspectorAOutput with analysis results
        """
        try:
            logger.info(f"Agent {self.name} starting processing")

            repo_path = input_data.get("repo_path", "")
            docs_path = input_data.get("docs_path", "")
            log_sources = input_data.get("log_sources", [])

            input_prompt = f"""Analyze the following artifacts:

            Code Repository: {repo_path}
            Documentation Path: {docs_path}
            Log Sources: {json.dumps(log_sources)}

            Tasks:
            1. Use code_analyzer to analyze the codebase
            2. Use document_scanner to analyze documentation
            3. Use process_miner to extract workflows from logs

            Provide comprehensive technical analysis including:
            - Technology stack and frameworks
            - Code quality and complexity metrics
            - Documentation quality
            - Development workflows and processes
            - Dependencies and integrations
            """

            result = self.run_with_tools(input_prompt)

            output_text = result.get("output", "")

            # TODO: Implement proper parsing
            output = self.create_output(
                ArtifactInspectorAOutput,
                tech_stack=[],
                artifact_types=[],
                complexity=[],
                dependencies=[],
                confidence_score=0.85,
                metadata={"raw_output": output_text}
            )

            logger.info(f"Agent {self.name} completed processing")
            return output

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            raise
