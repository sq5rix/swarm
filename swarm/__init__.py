from .core import *  # Original swarm imports
from .rabbitmq.swarm import SwarmRabbitMQ  # New import

__all__ = ["SwarmRabbitMQ", "Agent"]  # Add all relevant exports
