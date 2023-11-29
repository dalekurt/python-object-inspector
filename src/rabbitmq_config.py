# src/rabbitmq_config.py
"""
RabbitMQ Configuration Module
"""
from config_utils import get_env_variable

RABBITMQ_HOST = get_env_variable("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = get_env_variable("RABBITMQ_PORT", 5672, int)
RABBITMQ_USER = get_env_variable("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = get_env_variable("RABBITMQ_PASSWORD", "password")
RABBITMQ_EXCHANGE_NAME = get_env_variable("RABBITMQ_EXCHANGE_NAME", "exchange-uploads")
RABBITMQ_QUEUE_NAME = get_env_variable("RABBITMQ_QUEUE_NAME", "uploads")
RABBITMQ_ROUTING_KEY = get_env_variable("RABBITMQ_ROUTING_KEY", "uploads")
