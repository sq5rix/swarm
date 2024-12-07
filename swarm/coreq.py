import datetime
import json
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from openai import OpenAI

DEBUG = True  # Global debug flag

from .handler import RabbitMQHandler
from .types import Agent, Response


class SwarmRabbitMQ:
    """Extended Swarm class with RabbitMQ support"""

    def __init__(self, client=None, rabbitmq_config: Dict[str, Any] = None):
        if not client:
            client = OpenAI()
        self.client = client

        # Simple default configuration
        default_config = {
            "host": "localhost",
            "port": 5672,
            "username": "guest",
            "password": "guest",
        }

        # Update with user provided config
        if rabbitmq_config:
            default_config.update(rabbitmq_config)

        if DEBUG:
            print(f"[DEBUG] Connecting with config: {default_config}")

        # Initialize RabbitMQ handler
        self.rabbitmq = RabbitMQHandler(**default_config)
        self.agent_queues = {}
        self.registered_agents = []  # Track registered agents

        if DEBUG:
            print(f"[DEBUG] Initialized SwarmRabbitMQ with config: {default_config}")
            if self.verify_connection():
                print("[DEBUG] Successfully connected to RabbitMQ")

    def register_agent(self, agent: Agent) -> bool:
        """Register agent and create its message queue

        Returns:
            bool: True if agent was registered, False if already registered
        """
        try:
            if not self.verify_connection():
                raise ConnectionError("RabbitMQ connection is not available")

            if agent.name in self.agent_queues:
                if DEBUG:
                    print(f"[DEBUG] Agent {agent.name} already registered")
                    print(
                        f"[DEBUG] Current queue info: {self.agent_queues[agent.name]}"
                    )
                return False

            if DEBUG:
                print(f"[DEBUG] Registering new agent: {agent.name}")

            queue_name = f"agent_{agent.name.lower().replace(' ', '_')}_queue"
            routing_key = f"agent.{agent.name.lower().replace(' ', '_')}"

            # Try to setup queue with confirmation
            try:
                # Check if queue exists first
                try:
                    existing_queue = self.rabbitmq.channel.queue_declare(
                        queue=queue_name, passive=True
                    )
                    if DEBUG:
                        print(f"[DEBUG] Queue '{queue_name}' already exists")
                except Exception:
                    # Queue doesn't exist, create it with all properties
                    self.rabbitmq.channel.queue_declare(
                        queue=queue_name,
                        durable=True,
                        arguments={
                            "x-message-ttl": 3600000,  # 1 hour message TTL
                            "x-queue-type": "classic",
                        },
                    )
                    if DEBUG:
                        print(f"[DEBUG] Created new queue '{queue_name}'")

                # Bind queue to exchange
                self.rabbitmq.channel.queue_bind(
                    exchange="amq.topic", queue=queue_name, routing_key=routing_key
                )

                # Verify queue
                queue_check = self.rabbitmq.channel.queue_declare(
                    queue=queue_name, passive=True
                )
                if DEBUG:
                    print(f"[DEBUG] Queue '{queue_name}' created successfully")
                    print(
                        f"[DEBUG] Queue stats: messages={queue_check.method.message_count}, consumers={queue_check.method.consumer_count}"
                    )
            except Exception as e:
                print(f"[ERROR] Failed to setup queue for agent {agent.name}: {str(e)}")
                raise

            self.agent_queues[agent.name] = {
                "queue_name": queue_name,
                "routing_key": routing_key,
                "created_at": datetime.datetime.now().isoformat(),
            }
            self.registered_agents.append(agent)
            return True

        except Exception as e:
            print(f"[ERROR] Agent registration failed: {str(e)}")
            return False

    def register_agents(self, agents: List[Agent]) -> List[Agent]:
        """Register multiple agents at once

        Returns:
            List[Agent]: List of successfully registered agents
        """
        registered = []
        for agent in agents:
            if self.register_agent(agent):
                registered.append(agent)
        return registered

    def get_registered_agents(self) -> List[Agent]:
        """Get list of all registered agents"""
        return self.registered_agents.copy()

    def debug_queues(self) -> Dict[str, Any]:
        """Debug method to get queue information"""
        debug_info = {}
        try:
            for agent_name, queue_info in self.agent_queues.items():
                queue_name = queue_info["queue_name"]
                try:
                    queue_stats = self.rabbitmq.channel.queue_declare(
                        queue_name, passive=True
                    )
                    debug_info[agent_name] = {
                        "queue_name": queue_name,
                        "message_count": queue_stats.method.message_count,
                        "consumer_count": queue_stats.method.consumer_count,
                        "routing_key": queue_info["routing_key"],
                        "status": "active",
                    }
                except Exception as e:
                    debug_info[agent_name] = {
                        "queue_name": queue_name,
                        "message_count": 0,
                        "consumer_count": 0,
                        "routing_key": queue_info["routing_key"],
                        "status": "error",
                        "error": str(e),
                    }
            if DEBUG:
                print(f"[DEBUG] Active queues: {len(debug_info)}")
            return debug_info
        except Exception as e:
            print(f"[ERROR] Failed to get queue debug info: {str(e)}")
            return {}

    def verify_connection(self) -> bool:
        try:
            if (
                not hasattr(self.rabbitmq, "connection")
                or not self.rabbitmq.connection
                or not self.rabbitmq.connection.is_open
            ):
                if DEBUG:
                    print("[DEBUG] Connection is closed, attempting to reconnect...")
                # Reinitialize the handler
                config = {
                    "host": self.rabbitmq.host,
                    "port": self.rabbitmq.port,
                    "username": self.rabbitmq.username,
                    "password": self.rabbitmq.password,
                }
                self.rabbitmq = RabbitMQHandler(**config)
                return (
                    hasattr(self.rabbitmq, "connection")
                    and self.rabbitmq.connection.is_open
                )

            if (
                not hasattr(self.rabbitmq, "channel")
                or not self.rabbitmq.channel
                or not self.rabbitmq.channel.is_open
            ):
                if DEBUG:
                    print("[DEBUG] Channel is closed, attempting to recreate...")
                # Reinitialize the handler
                config = {
                    "host": self.rabbitmq.host,
                    "port": self.rabbitmq.port,
                    "username": self.rabbitmq.username,
                    "password": self.rabbitmq.password,
                }
                self.rabbitmq = RabbitMQHandler(**config)
                return (
                    hasattr(self.rabbitmq, "channel") and self.rabbitmq.channel.is_open
                )

            # Test connection with a lightweight operation
            self.rabbitmq.connection.process_data_events()
            return True

        except Exception as e:
            print(f"[ERROR] Connection verification failed: {str(e)}")
            try:
                if DEBUG:
                    print("[DEBUG] Attempting to reconnect after error...")
                self.rabbitmq.reconnect()
                return self.rabbitmq.connection.is_open
            except Exception as reconnect_error:
                print(f"[ERROR] Reconnection failed: {str(reconnect_error)}")
                return False

    def handoff_to_agent(
        self,
        from_agent: Agent,
        to_agent: Agent,
        messages: List[Dict[str, str]],
        context_variables: Dict[str, Any],
    ):
        """Handle agent handoff through RabbitMQ"""
        if DEBUG:
            print(f"\n=== HANDOFF START: {from_agent.name} -> {to_agent.name} ===")
            print(f"Queue status before handoff:")
            print(json.dumps(self.debug_queues(), indent=2))

        if to_agent.name not in self.agent_queues:
            self.register_agent(to_agent)

        handoff_message = {
            "from_agent": from_agent.name,
            "messages": messages,
            "context_variables": context_variables,
        }

        routing_key = self.agent_queues[to_agent.name]["routing_key"]
        if DEBUG:
            print(f"\nPublishing message:")
            print(f"- Routing key: {routing_key}")
            print(f"- Message size: {len(str(handoff_message))} bytes")
            print(f"- To agent: {to_agent.name}")

        self.rabbitmq.publish_message(routing_key, handoff_message)

        if DEBUG:
            print(f"\nQueue status after handoff:")
            print(json.dumps(self.debug_queues(), indent=2))
            print(f"=== HANDOFF END ===\n")

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
        """Run agent with message queue integration"""
        if context_variables is None:
            context_variables = {}

        # Register agent if not already registered
        if agent.name not in self.agent_queues:
            self.register_agent(agent)

        if DEBUG:
            print(f"\n=== STARTING RUN FOR {agent.name} ===")
            print(f"Initial messages: {json.dumps(messages, indent=2)}")
            print(f"Context variables: {json.dumps(context_variables, indent=2)}")

        # Publish initial message to agent's queue
        routing_key = self.agent_queues[agent.name]["routing_key"]
        initial_message = {
            "messages": messages,
            "context_variables": context_variables,
            "model": model_override,
            "stream": stream,
            "debug": debug,
            "max_turns": max_turns,
            "execute_tools": execute_tools,
        }

        if DEBUG:
            print(f"\nPublishing initial message to {agent.name}")
            print(f"Routing key: {routing_key}")
            print(f"Message size: {len(str(initial_message))} bytes")

        self.rabbitmq.publish_message(routing_key, initial_message)

        # Get queue info after publishing
        if DEBUG:
            queue_info = self.debug_queues()
            print("\nQueue status after publishing:")
            print(json.dumps(queue_info, indent=2))

        # For now, return a simple response
        return Response(
            agent=agent,
            messages=messages,
            context_variables=context_variables,
            final_message="Message queued for processing",
        )

    @contextmanager
    def ensure_connection(self):
        """Context manager to ensure RabbitMQ connection is available"""
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                if self.verify_connection():
                    yield
                    break
                retry_count += 1
                if DEBUG:
                    print(f"[DEBUG] Connection attempt {retry_count}/{max_retries}")
                time.sleep(1)  # Wait before retry
            except Exception as e:
                print(f"[ERROR] Operation failed: {str(e)}")
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                time.sleep(1)

    def start_consuming(self, agent: Agent, callback=None):
        """Start consuming messages for an agent"""
        if agent.name not in self.agent_queues:
            raise ValueError(f"Agent {agent.name} not registered")

        queue_name = self.agent_queues[agent.name]["queue_name"]

        def default_callback(ch, method, properties, body):
            """Default message processing callback"""
            try:
                message = json.loads(body)
                if DEBUG:
                    print(f"\n[DEBUG] Received message for {agent.name}:")
                    print(json.dumps(message, indent=2))

                # Process message here
                if callback:
                    callback(message)

                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                print(f"[ERROR] Error processing message: {str(e)}")
                # Negative acknowledgment - message will be requeued
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        if DEBUG:
            print(f"[DEBUG] Starting consumer for {agent.name} on queue {queue_name}")

        # Set up consumer
        self.rabbitmq.channel.basic_qos(prefetch_count=1)
        self.rabbitmq.channel.basic_consume(
            queue=queue_name, on_message_callback=default_callback
        )

        try:
            if DEBUG:
                print(f"[DEBUG] Waiting for messages for {agent.name}...")
            self.rabbitmq.channel.start_consuming()
        except KeyboardInterrupt:
            if DEBUG:
                print(f"[DEBUG] Stopping consumer for {agent.name}")
            self.rabbitmq.channel.stop_consuming()

    def __del__(self):
        """Cleanup RabbitMQ connection on deletion"""
        if hasattr(self, "rabbitmq"):
            try:
                self.rabbitmq.close()
                if DEBUG:
                    print("[DEBUG] RabbitMQ connection closed properly")
            except Exception as e:
                print(f"[ERROR] Error closing RabbitMQ connection: {str(e)}")
