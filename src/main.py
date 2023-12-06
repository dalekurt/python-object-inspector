import signal
import sys
import time

import pika
from loguru import logger
from opentelemetry import trace

from inspect_object import InspectObject
from opentelemetry_config import configure_opentelemetry
from rabbitmq_config import (
    RABBITMQ_EXCHANGE_NAME,
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_PORT,
    RABBITMQ_QUEUE_NAME,
    RABBITMQ_USER,
)


def handle_interrupt(signum, frame):
    logger.info("Received interrupt signal. Shutting down gracefully.")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_interrupt)

# Configure OpenTelemetry
configure_opentelemetry()


def callback(ch, method, properties, body):
    try:
        filename = body.decode("utf-8")
        logger.info(f"Received event from RabbitMQ: {filename}")
        inspect_uploaded_object(filename)
    except Exception as e:
        logger.error(f"Error processing RabbitMQ message: {e}", exc_info=True)
        # Increment failed inspections counter
        failed_inspections_counter.add(1)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def inspect_uploaded_object(filename: str):
    try:
        with trace.get_tracer(__name__).start_as_current_span(
            "inspect_uploaded_object"
        ):
            # Increment objects inspected counter
            objects_inspected_counter.add(1)

            inspect_object = InspectObject(filename)
            result = inspect_object.inspect()
            if result["content"] is not None:
                logger.info(
                    f"Object inspection for '{filename}' completed successfully. Result: {result}"
                )
                # Increment successful inspections counter
                successful_inspections_counter.add(1)
            else:
                logger.warning(f"Object '{filename}' not found in 'uploads' bucket.")
                # Increment failed inspections counter
                failed_inspections_counter.add(1)
    except Exception as e:
        logger.error(f"Error inspecting object '{filename}': {e}", exc_info=True)
        # Increment failed inspections counter
        failed_inspections_counter.add(1)


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
            # Set RabbitMQ connection status metric to 1 (success)
            rabbitmq_connection_status.record(1)
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Error connecting to RabbitMQ: {e}", exc_info=True)
            logger.info(f"Retrying in {RETRY_INTERVAL} seconds...")
            time.sleep(RETRY_INTERVAL)
            retries += 1
            # Increment retry attempts counter
            retry_attempts_counter.add(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            # Set RabbitMQ connection status metric to 0 (failure)
            rabbitmq_connection_status.record(0)
    # Set RabbitMQ connection status metric to 0 (failure) when max retries are reached
    rabbitmq_connection_status.record(0)
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
            logger.error(f"Error setting up RabbitMQ consumer: {e}", exc_info=True)
        finally:
            # Close the channel if it is open
            if channel is not None and channel.is_open:
                channel.close()

            # Close the connection if it is open
            if connection is not None and connection.is_open:
                connection.close()


if __name__ == "__main__":
    # setup_logging()
    configure_opentelemetry()
    logger.info("Started successfully.")
    script_start_time = time.time()
    try:
        listen_for_rabbitmq_events()
    finally:
        # Calculate script uptime and record the value
        script_uptime = time.time() - script_start_time
        script_uptime_counter.add(int(script_uptime))
