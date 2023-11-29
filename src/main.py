# src/main.py
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
    RABBITMQ_EXCHANGE_NAME,
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_PORT,
    RABBITMQ_QUEUE_NAME,
    RABBITMQ_USER,
)

# TODO: Constants for the logger
LOG_FILE = "logs/app.log"
LOG_ROTATION = "5 MB"
LOG_LEVEL = "INFO"
LOG_FORMAT = "{time} - {level} - {message}"
RETRY_INTERVAL = 5


def handle_interrupt(signum, frame):
    logger.info("Received interrupt signal. Shutting down gracefully.")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_interrupt)


# Logging
def setup_logging():
    logger.add(LOG_FILE, rotation=LOG_ROTATION, level=LOG_LEVEL, format=LOG_FORMAT)


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


# Max retries for the retry logic
MAX_RETRIES = 3


def connect_to_rabbitmq():
    connection = None
    retries = 0
    while retries < MAX_RETRIES:
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
            logger.info(f"Retrying in {RETRY_INTERVAL} seconds...")
            time.sleep(RETRY_INTERVAL)
            retries += 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    logger.error("Max retries reached. Unable to connect to RabbitMQ.")
    sys.exit(1)


def listen_for_rabbitmq_events():
    connection = None
    channel = None

    while True:
        try:
            connection = connect_to_rabbitmq()
            channel = connection.channel()
            channel.exchange_declare(
                exchange=RABBITMQ_EXCHANGE_NAME, exchange_type="fanout"
            )
            result = channel.queue_declare(queue=RABBITMQ_QUEUE_NAME, exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(
                exchange=RABBITMQ_EXCHANGE_NAME, queue=result.method.queue
            )
            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            logger.info(
                f"Connected to RabbitMQ. Waiting for events on {RABBITMQ_QUEUE_NAME} queue. To exit press Ctrl+C"
            )
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Error setting up RabbitMQ consumer: {e}")
        finally:
            # Close the channel if it is open
            if channel is not None and channel.is_open:
                channel.close()

            # Close the connection if it is open
            if connection is not None and connection.is_open:
                connection.close()


def handle_interrupt(signum, frame):
    logger.info("Received interrupt signal. Shutting down gracefully.")
    sys.exit(0)


if __name__ == "__main__":
    setup_logging()
    logger.info("Started successfully.")
    listen_for_rabbitmq_events()
