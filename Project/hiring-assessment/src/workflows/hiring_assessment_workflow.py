"""Main hiring assessment workflow orchestrating all agent layers."""
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..agents.layer1 import (
    StrategicContextAgent,
    PainPointAgent,
    ArtifactInspectorA,
    ArtifactInspectorB,
    ArtifactInspectorC,
)
from ..agents.layer_semi2 import ArtifactInspectorB2
from ..agents.layer2 import RequirementSynthesizer, MarketIntelligenceAgent
from ..agents.layer3 import ButAgent
from ..memory import SessionMemory
from ..config import logger


class HiringAssessmentWorkflow:
    """
    Orchestrates the multi-agent hiring assessment workflow.

    Layer Flow:
    1. Layer 1: Parallel data extraction agents
    2. Layer Semi-2: Best practices search
    3. Layer 2: Synthesis and market validation
    4. Layer 3: Critical analysis
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the workflow.

        Args:
            session_id: Optional session identifier
        """
        self.session_memory = SessionMemory(session_id=session_id)

        # Initialize all agents
        self.layer1_agents = {
            "strategic_context": StrategicContextAgent(),
            "pain_point": PainPointAgent(),
            "artifact_a": ArtifactInspectorA(),
            "artifact_b": ArtifactInspectorB(),
            "artifact_c": ArtifactInspectorC(),
        }

        self.layer_semi2_agents = {
            "artifact_b2": ArtifactInspectorB2(),
        }

        self.layer2_agents = {
            "requirement_synthesizer": RequirementSynthesizer(),
            "market_intel": MarketIntelligenceAgent(),
        }

        self.layer3_agents = {
            "but_agent": ButAgent(),
        }

        logger.info(f"Initialized HiringAssessmentWorkflow (session: {self.session_memory.session_id})")

    def run_layer1_parallel(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Layer 1 agents in parallel.

        Args:
            input_data: Input data for all Layer 1 agents

        Returns:
            Dictionary of all Layer 1 outputs
        """
        logger.info("Starting Layer 1 - Parallel Data Extraction")

        layer1_outputs = {}

        # Define tasks for each agent
        agent_tasks = {
            "strategic_context": input_data.get("strategic_context_input", {}),
            "pain_point": input_data.get("pain_point_input", {}),
            "artifact_a": input_data.get("artifact_a_input", {}),
            "artifact_c": input_data.get("artifact_c_input", {}),
        }

        # Run agents in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_agent = {
                executor.submit(agent.process, agent_tasks[agent_key]): agent_key
                for agent_key, agent in self.layer1_agents.items()
                if agent_key in agent_tasks
            }

            for future in as_completed(future_to_agent):
                agent_key = future_to_agent[future]
                try:
                    result = future.result()
                    layer1_outputs[agent_key] = result
                    self.session_memory.store_agent_output(agent_key, result)
                    logger.info(f"Completed Layer 1 agent: {agent_key}")
                except Exception as e:
                    logger.error(f"Error in Layer 1 agent {agent_key}: {e}")
                    layer1_outputs[agent_key] = {"error": str(e)}

        # Run Artifact Inspector B (depends on Artifact Inspector A)
        if "artifact_a" in layer1_outputs:
            try:
                artifact_b_output = self.layer1_agents["artifact_b"].process({
                    "inspector_a_output": layer1_outputs["artifact_a"]
                })
                layer1_outputs["artifact_b"] = artifact_b_output
                self.session_memory.store_agent_output("artifact_b", artifact_b_output)
                logger.info("Completed Layer 1 agent: artifact_b")
            except Exception as e:
                logger.error(f"Error in Artifact Inspector B: {e}")
                layer1_outputs["artifact_b"] = {"error": str(e)}

        logger.info("Completed Layer 1 - Parallel Data Extraction")
        return layer1_outputs

    def run_layer_semi2(self, layer1_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Layer Semi-2 agents.

        Args:
            layer1_outputs: Outputs from Layer 1

        Returns:
            Dictionary of Layer Semi-2 outputs
        """
        logger.info("Starting Layer Semi-2 - Best Practices Search")

        layer_semi2_outputs = {}

        # Run Artifact Inspector B2 (searches best practices for B's improvements)
        if "artifact_b" in layer1_outputs:
            try:
                improvement_areas = layer1_outputs["artifact_b"].get("improvement_areas", [])
                b2_output = self.layer_semi2_agents["artifact_b2"].process({
                    "improvement_areas": improvement_areas
                })
                layer_semi2_outputs["artifact_b2"] = b2_output
                self.session_memory.store_agent_output("artifact_b2", b2_output)
                logger.info("Completed Layer Semi-2 agent: artifact_b2")
            except Exception as e:
                logger.error(f"Error in Artifact Inspector B2: {e}")
                layer_semi2_outputs["artifact_b2"] = {"error": str(e)}

        logger.info("Completed Layer Semi-2 - Best Practices Search")
        return layer_semi2_outputs

    def run_layer2(
        self,
        layer1_outputs: Dict[str, Any],
        layer_semi2_outputs: Dict[str, Any],
        location: str = "Remote/Global",
        industry: str = "Technology"
    ) -> Dict[str, Any]:
        """
        Run Layer 2 synthesis agents.

        Args:
            layer1_outputs: Outputs from Layer 1
            layer_semi2_outputs: Outputs from Layer Semi-2
            location: Hiring location
            industry: Industry context

        Returns:
            Dictionary of Layer 2 outputs
        """
        logger.info("Starting Layer 2 - Synthesis and Market Validation")

        layer2_outputs = {}

        # Run Requirement Synthesizer
        try:
            requirements = self.layer2_agents["requirement_synthesizer"].process({
                "strategic_context": layer1_outputs.get("strategic_context", {}),
                "pain_points": layer1_outputs.get("pain_point", {}),
                "artifacts_a": layer1_outputs.get("artifact_a", {}),
                "artifacts_b": layer1_outputs.get("artifact_b", {}),
                "artifacts_c": layer1_outputs.get("artifact_c", {}),
                "best_practices": layer_semi2_outputs.get("artifact_b2", {}),
            })
            layer2_outputs["requirements"] = requirements
            self.session_memory.store_agent_output("requirements", requirements)
            logger.info("Completed Layer 2 agent: requirement_synthesizer")
        except Exception as e:
            logger.error(f"Error in Requirement Synthesizer: {e}")
            layer2_outputs["requirements"] = {"error": str(e)}

        # Run Market Intelligence Agent
        try:
            market_intel = self.layer2_agents["market_intel"].process({
                "requirements": layer2_outputs.get("requirements", {}),
                "location": location,
                "industry": industry,
            })
            layer2_outputs["market_intel"] = market_intel
            self.session_memory.store_agent_output("market_intel", market_intel)
            logger.info("Completed Layer 2 agent: market_intel")
        except Exception as e:
            logger.error(f"Error in Market Intelligence Agent: {e}")
            layer2_outputs["market_intel"] = {"error": str(e)}

        logger.info("Completed Layer 2 - Synthesis and Market Validation")
        return layer2_outputs

    def run_layer3(
        self,
        layer1_outputs: Dict[str, Any],
        layer2_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run Layer 3 critical analysis.

        Args:
            layer1_outputs: Outputs from Layer 1
            layer2_outputs: Outputs from Layer 2

        Returns:
            Dictionary of Layer 3 outputs
        """
        logger.info("Starting Layer 3 - Critical Analysis")

        layer3_outputs = {}

        # Run BUT Agent
        try:
            but_output = self.layer3_agents["but_agent"].process({
                "requirements": layer2_outputs.get("requirements", {}),
                "market_intel": layer2_outputs.get("market_intel", {}),
                "all_layer1_outputs": layer1_outputs,
            })
            layer3_outputs["but_agent"] = but_output
            self.session_memory.store_agent_output("but_agent", but_output)
            logger.info("Completed Layer 3 agent: but_agent")
        except Exception as e:
            logger.error(f"Error in BUT Agent: {e}")
            layer3_outputs["but_agent"] = {"error": str(e)}

        logger.info("Completed Layer 3 - Critical Analysis")
        return layer3_outputs

    def run(
        self,
        input_data: Dict[str, Any],
        location: str = "Remote/Global",
        industry: str = "Technology"
    ) -> Dict[str, Any]:
        """
        Run the complete workflow.

        Args:
            input_data: Input data for all agents
            location: Hiring location
            industry: Industry context

        Returns:
            Complete workflow results
        """
        logger.info("=" * 80)
        logger.info("STARTING HIRING ASSESSMENT WORKFLOW")
        logger.info("=" * 80)

        try:
            # Layer 1: Parallel data extraction
            layer1_outputs = self.run_layer1_parallel(input_data)

            # Layer Semi-2: Best practices search
            layer_semi2_outputs = self.run_layer_semi2(layer1_outputs)

            # Layer 2: Synthesis and market validation
            layer2_outputs = self.run_layer2(
                layer1_outputs,
                layer_semi2_outputs,
                location,
                industry
            )

            # Layer 3: Critical analysis
            layer3_outputs = self.run_layer3(layer1_outputs, layer2_outputs)

            # Compile final results
            final_results = {
                "session_id": self.session_memory.session_id,
                "layer1": layer1_outputs,
                "layer_semi2": layer_semi2_outputs,
                "layer2": layer2_outputs,
                "layer3": layer3_outputs,
                "summary": self.session_memory.get_summary(),
            }

            logger.info("=" * 80)
            logger.info("COMPLETED HIRING ASSESSMENT WORKFLOW")
            logger.info("=" * 80)

            return final_results

        except Exception as e:
            logger.error(f"Error in workflow execution: {e}")
            raise

    def get_session_state(self) -> Dict[str, Any]:
        """
        Get the current session state.

        Returns:
            Session state dictionary
        """
        return {
            "session_summary": self.session_memory.get_summary(),
            "agent_outputs": self.session_memory.get_all_agent_outputs(),
        }

    def clear_session(self) -> None:
        """Clear the current session."""
        self.session_memory.clear()
        logger.info("Session cleared")
