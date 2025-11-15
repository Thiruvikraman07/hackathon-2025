"""Session memory for conversation-level state management."""
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage

from ..config import logger


class SessionMemory:
    """
    Session-level memory for managing conversation state and intermediate results.
    This memory is ephemeral and exists only during the current workflow execution.
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize session memory.

        Args:
            session_id: Optional session identifier
        """
        self.session_id = session_id or self._generate_session_id()
        self.created_at = datetime.now()

        # Conversation memory
        self.conversation_memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )

        # Custom state storage
        self.state: Dict[str, Any] = {}

        # Agent outputs storage
        self.agent_outputs: Dict[str, Any] = {}

        logger.info(f"Initialized SessionMemory with ID: {self.session_id}")

    @staticmethod
    def _generate_session_id() -> str:
        """Generate a unique session ID."""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to conversation memory.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        try:
            if role == "user":
                self.conversation_memory.chat_memory.add_user_message(content)
            elif role == "assistant":
                self.conversation_memory.chat_memory.add_ai_message(content)
            else:
                # For system or other roles, we can store in state
                self.set_state(f"message_{role}_{len(self.state)}", content)

            logger.debug(f"Added {role} message to session {self.session_id}")
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise

    def get_messages(self) -> List[BaseMessage]:
        """
        Get all conversation messages.

        Returns:
            List of messages
        """
        return self.conversation_memory.chat_memory.messages

    def set_state(self, key: str, value: Any) -> None:
        """
        Set a state variable.

        Args:
            key: State key
            value: State value
        """
        self.state[key] = value
        logger.debug(f"Set state: {key} = {str(value)[:100]}")

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a state variable.

        Args:
            key: State key
            default: Default value if key doesn't exist

        Returns:
            State value
        """
        return self.state.get(key, default)

    def store_agent_output(self, agent_id: str, output: Any) -> None:
        """
        Store an agent's output.

        Args:
            agent_id: Agent identifier
            output: Agent output
        """
        self.agent_outputs[agent_id] = {
            "output": output,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Stored output for agent: {agent_id}")

    def get_agent_output(self, agent_id: str) -> Optional[Any]:
        """
        Get an agent's output.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent output if exists
        """
        result = self.agent_outputs.get(agent_id)
        return result["output"] if result else None

    def get_all_agent_outputs(self) -> Dict[str, Any]:
        """
        Get all agent outputs.

        Returns:
            Dictionary of all agent outputs
        """
        return {
            agent_id: data["output"]
            for agent_id, data in self.agent_outputs.items()
        }

    def clear(self) -> None:
        """Clear all session memory."""
        self.conversation_memory.clear()
        self.state.clear()
        self.agent_outputs.clear()
        logger.info(f"Cleared session memory: {self.session_id}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the session.

        Returns:
            Session summary
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "message_count": len(self.get_messages()),
            "state_keys": list(self.state.keys()),
            "agent_outputs": list(self.agent_outputs.keys())
        }
