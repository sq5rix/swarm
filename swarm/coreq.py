# Required imports
import json
import threading
import time

from swarm import Agent, Swarm

DEFAULT_RABBITMQ_CONFIG = {
    "host": "localhost",
    "port": 5672,
    "username": "guest",
    "password": "guest",
}


class SwarmRabbitMQ(Swarm):
    def __init__(self, rabbitmq_config=DEFAULT_RABBITMQ_CONFIG):
        """Initialize the SwarmMQ with RabbitMQ configuration."""
        super().__init__()
        self.rabbitmq_config = rabbitmq_config
        self.agents = []
        self.consumer_threads = []

    def register_agent(self, agent):
        """Register an agent with the SwarmMQ."""
        self.agents.append(agent)
        print(f"Agent {agent.name} registered.")

    def start_consumer_for_agent(self, agent):
        """Start a consumer thread for an agent."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                print(f"\n[INFO] Starting consumer for {agent.name}")
                self.start_consuming(agent, callback=self.message_handler)
                break
            except Exception as e:
                retry_count += 1
                print(f"[ERROR] Consumer error for {agent.name}: {str(e)}")
                if retry_count < max_retries:
                    wait_time = retry_count * 5  # Exponential backoff
                    print(
                        f"[INFO] Retry {retry_count}/{max_retries} for {agent.name} in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] Max retries reached for {agent.name}")
                    break

    def message_handler(self, message):
        """Handle received messages."""
        print("\n=== Message Received ===")
        print(f"Content: {json.dumps(message, indent=2)}")

        if "messages" in message:
            for msg in message["messages"]:
                if msg["role"] == "user":
                    print(f"\nProcessing user message: {msg['content']}")
                    # Add your message processing logic here

        if "context_variables" in message:
            print(
                f"\nContext variables: {json.dumps(message['context_variables'], indent=2)}"
            )

    def handoff_to_agent(self, sender, receiver, messages, context):
        """Handoff message from one agent to another."""
        try:
            print(f"Handoff from {sender.name} to {receiver.name}")
            # Implement the handoff logic here
            return {"status": "success", "message": "Handoff completed"}
        except Exception as e:
            print(f"[ERROR] Failed to handoff: {str(e)}")
            return {"status": "failure", "message": str(e)}


def run(self, agent, messages, context_variables=None):
    """Run the agent with provided messages."""
    context_variables = context_variables or {}
    print("\n=== Sending Messages ===")
    try:
        # Assuming `super().run()` returns a Response object with accessible attributes
        response = super().run(agent, messages, context_variables=context_variables)

        # Accessing attributes directly from the Response object
        serializable_response = {
            "agent": str(getattr(response, "agent", "")),
            "status": str(getattr(response, "status", "")),
            "message_count": int(getattr(response, "message_count", 0)),
            "final_message": str(getattr(response, "final_message", "")),
            "context": getattr(response, "context", {}),
        }

        print(f"Run response: {json.dumps(serializable_response, indent=2)}")
        return serializable_response
    except Exception as e:
        print(f"[ERROR] Failed to process response: {str(e)}")
        return None

    def start_consuming(self, agent, callback):
        """Mocked function to simulate start consuming messages."""
        # In a real-world scenario, this method would connect to RabbitMQ and consume messages.
        print(f"Consuming messages for agent {agent.name}")


# Example RabbitMQ configuration
rabbitmq_config = {
    "host": "localhost",
    "port": 5672,
    "username": "guest",
    "password": "guest",
}

# Example usage
if __name__ == "__main__":
    client = SwarmMQ(rabbitmq_config=rabbitmq_config)
    agent_a = Agent(name="Agent A", role="Sender")
    agent_b = Agent(name="Agent B", role="Receiver")

    client.register_agent(agent_a)
    client.register_agent(agent_b)

    for agent in client.agents:
        consumer_thread = threading.Thread(
            target=client.start_consumer_for_agent, args=(agent,), daemon=True
        )
        client.consumer_threads.append(consumer_thread)
        consumer_thread.start()

    time.sleep(1)  # Wait for consumers to start
    test_messages = [{"role": "user", "content": "I want to talk to agent B."}]
    context = {"conversation_id": "test_123", "timestamp": time.time()}
    client.run(agent_a, test_messages, context_variables=context)
