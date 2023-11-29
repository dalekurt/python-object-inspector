# src/publish_test_message.py
import os
import random
import uuid

import pika

# RabbitMQ connection parameters
from rabbitmq_config import (
    RABBITMQ_EXCHANGE_NAME,
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_PORT,
    RABBITMQ_ROUTING_KEY,
    RABBITMQ_USER,
)

# List of possible file extensions
FILE_EXTENSIONS = [".jpeg", ".jpg", ".ogg", ".mp4", ".mp3", ".wav", ".txt", ".pdf"]

# Generate a random file name with a random UUID and a random extension
random_file_name = f"{uuid.uuid4()}{random.choice(FILE_EXTENSIONS)}"

# Create a connection to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD),
    )
)

# Create a channel
channel = connection.channel()

# Declare the exchange
channel.exchange_declare(exchange=RABBITMQ_EXCHANGE_NAME, exchange_type="fanout")

# Get the queue name from the environment variable
queue_name = os.environ.get("RABBITMQ_QUEUE_NAME", "uploads")

# Publish the test message to the exchange with the specified routing key
channel.basic_publish(
    exchange=RABBITMQ_EXCHANGE_NAME,
    routing_key=RABBITMQ_ROUTING_KEY,
    body=random_file_name,
)

# Close the connection
connection.close()

print(f"Test message '{random_file_name}' published to RabbitMQ queue '{queue_name}'.")
