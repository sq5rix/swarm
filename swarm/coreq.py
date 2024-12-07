from typing import Any, Dict, List, Optional

from openai import OpenAI

from .handler import RabbitMQHandler
from .types import Agent, Response


class SwarmRabbitMQ:
    """Extended Swarm class with RabbitMQ support"""

    def __init__(self, client=None, rabbitmq_config: Dict[str, Any] = None):
        if not client:
            client = OpenAI()
        self.client = client

        # Initialize RabbitMQ handler
        self.rabbitmq = RabbitMQHandler(**(rabbitmq_config or {}))
        self.agent_queues = {}

    def register_agent(self, agent: Agent):
        """Register agent and create its message queue"""
        queue_name = f"agent_{agent.name.lower().replace(' ', '_')}_queue"
        routing_key = f"agent.{agent.name.lower().replace(' ', '_')}"

        self.rabbitmq.setup_queue(queue_name, routing_key)
        self.agent_queues[agent.name] = {
            "queue": queue_name,
            "routing_key": routing_key,
        }

    def handoff_to_agent(
        self,
        from_agent: Agent,
        to_agent: Agent,
        messages: List[Dict[str, str]],
        context_variables: Dict[str, Any],
    ):
        """Handle agent handoff through RabbitMQ"""
        if to_agent.name not in self.agent_queues:
            self.register_agent(to_agent)

        handoff_message = {
            "from_agent": from_agent.name,
            "messages": messages,
            "context_variables": context_variables,
        }

        self.rabbitmq.publish_message(
            self.agent_queues[to_agent.name]["routing_key"], handoff_message
        )

    def run(
        self,
        agent: Agent,
        messages: List[Dict[str, str]],
        context_variables: Dict[str, Any] = None,
        model_override: str = None,
        stream: bool = False,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ) -> Response:

        # Register agent if not already registered
        if agent.name not in self.agent_queues:
            self.register_agent(agent)

        # Original run logic here, but with RabbitMQ integration
        # ... (existing run logic)

    def __del__(self):
        """Cleanup RabbitMQ connection on deletion"""
        if hasattr(self, "rabbitmq"):
            self.rabbitmq.close()
