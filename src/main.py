# main.py
"""
Main script for checking the existence of a specified Minio object in the 'uploads' bucket.
"""

import signal
import sys
import time

import pika
from loguru import logger

from inspect_object import InspectObject
from rabbitmq_config import (
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_PORT,
    RABBITMQ_USER,
)


def handle_interrupt(signum, frame):
    logger.info("Received interrupt signal. Shutting down gracefully.")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_interrupt)

# Configure logging
logger.add(
    "app.log", rotation="5 MB", level="INFO", format="{time} - {level} - {message}"
)


def callback(ch, method, properties, body):
    try:
        filename = body.decode("utf-8")
        logger.info(f"Received event from RabbitMQ: {filename}")
        inspect_uploaded_object(filename)
    except Exception as e:
        logger.error(f"Error processing RabbitMQ message: {e}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def inspect_uploaded_object(filename: str):
    try:
        inspect_object = InspectObject(filename)
        result = inspect_object.inspect()
        if result["content"] is not None:
            logger.info(
                f"Object inspection for '{filename}' completed successfully. Result: {result}"
            )
        else:
            logger.warning(f"Object '{filename}' not found in 'uploads' bucket.")
    except Exception as e:
        logger.error(f"Error inspecting object '{filename}': {e}")


def connect_to_rabbitmq():
    connection = None
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD),
                )
            )
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"Error connecting to RabbitMQ: {e}")
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)


def listen_for_rabbitmq_events():
    connection = None
    channel = None

    while True:
        try:
            connection = connect_to_rabbitmq()
            channel = connection.channel()
            channel.exchange_declare(exchange="minio_exchange", exchange_type="fanout")
            result = channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange="minio_exchange", queue=queue_name)
            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            logger.info(
                "Connected to RabbitMQ. Waiting for events. To exit press Ctrl+C"
            )
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Error setting up RabbitMQ consumer: {e}")
        finally:
            # Close the connection if it is open
            if connection is not None and connection.is_open:
                connection.close()


if __name__ == "__main__":
    listen_for_rabbitmq_events()
