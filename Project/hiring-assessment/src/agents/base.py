"""Base agent class and utilities."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool

from ..config import settings, logger
from ..models.common import BaseAgentOutput


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        tools: Optional[List[BaseTool]] = None,
        temperature: float = None
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Agent description
            tools: List of tools available to the agent
            temperature: LLM temperature (defaults to settings)
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.tools = tools or []
        self.temperature = temperature if temperature is not None else settings.temperature

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=self.temperature,
            openai_api_key=settings.openai_api_key
        )

        logger.info(f"Initialized agent: {self.name} ({self.agent_id})")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> BaseAgentOutput:
        """
        Process input and generate output.

        Args:
            input_data: Input data for processing

        Returns:
            Agent output
        """
        pass

    def create_agent_executor(
        self,
        system_prompt: Optional[str] = None,
        additional_messages: Optional[List] = None
    ) -> AgentExecutor:
        """
        Create an agent executor with tools.

        Args:
            system_prompt: Optional custom system prompt
            additional_messages: Additional message placeholders

        Returns:
            Configured agent executor
        """
        prompt_messages = [
            ("system", system_prompt or self.get_system_prompt()),
        ]

        if additional_messages:
            prompt_messages.extend(additional_messages)

        prompt_messages.extend([
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        prompt = ChatPromptTemplate.from_messages(prompt_messages)

        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            return_intermediate_steps=True
        )

        return executor

    def create_output(
        self,
        output_class: type[BaseAgentOutput],
        **kwargs
    ) -> BaseAgentOutput:
        """
        Create a standardized agent output.

        Args:
            output_class: Output class to instantiate
            **kwargs: Additional fields for the output

        Returns:
            Agent output instance
        """
        return output_class(
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def run_with_tools(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent with tools.

        Args:
            input_text: Input prompt
            context: Optional context dictionary

        Returns:
            Agent execution result
        """
        try:
            executor = self.create_agent_executor()

            result = executor.invoke({
                "input": input_text,
                **(context or {})
            })

            logger.info(f"Agent {self.name} completed execution")
            return result

        except Exception as e:
            logger.error(f"Error running agent {self.name}: {e}")
            raise

    def run_simple(
        self,
        input_text: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Run the agent without tools (simple LLM call).

        Args:
            input_text: Input text
            system_prompt: Optional system prompt override

        Returns:
            LLM response
        """
        try:
            messages = [
                ("system", system_prompt or self.get_system_prompt()),
                ("human", input_text)
            ]

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"Error in simple run for agent {self.name}: {e}")
            raise
