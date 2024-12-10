import json
import logging
from functools import wraps
from typing import Any, Dict, Optional

import pika


class RabbitMQHandler:
    """Handler for RabbitMQ communications in Swarm system"""

    def __init__(self, host="localhost", port=5672, username="guest", password="guest"):
        self.credentials = pika.PlainCredentials(username, password)
        self.parameters = pika.ConnectionParameters(
            host=host, port=port, credentials=self.credentials
        )
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        """Establish connection to RabbitMQ server"""
        try:
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            # Declare exchange for agent communication
            self.channel.exchange_declare(
                exchange="agent_exchange", exchange_type="topic"
            )
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    def ensure_connection(func):
        """Decorator to ensure RabbitMQ connection is active"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.connection or self.connection.is_closed:
                self._connect()
            return func(self, *args, **kwargs)

        return wrapper

    @ensure_connection
    def publish_message(self, routing_key: str, message: Dict[str, Any]):
        """Publish message to specific routing key"""
        try:
            self.channel.basic_publish(
                exchange="agent_exchange",
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ),
            )
        except Exception as e:
            logging.error(f"Failed to publish message: {str(e)}")
            raise

    @ensure_connection
    def setup_queue(self, queue_name: str, routing_key: str):
        """Setup queue and bind it to the exchange"""
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(
            exchange="agent_exchange", queue=queue_name, routing_key=routing_key
        )

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
