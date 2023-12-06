# src/opentelemetry_config.py

from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.prometheus import PrometheusMetricsExporter
from opentelemetry.instrumentation.pika import PikaInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricsExportSpanProcessor

# Constants for the logger
LOG_FILE = "logs/app.log"
LOG_ROTATION = "1 MB"
LOG_LEVEL = "INFO"
LOG_FORMAT = "{time} - {level} - {message}"
RETRY_INTERVAL = 5


def configure_opentelemetry():
    # Configure logging
    setup_logging()

    # Configure OpenTelemetry with Prometheus exporter
    trace.set_tracer_provider(trace.TracerProvider())

    metrics_exporter = PrometheusMetricsExporter(endpoint=":9464/metrics")

    meter_provider = MeterProvider()
    meter_provider.add_exporter(metrics_exporter)

    trace.get_tracer_provider().add_span_processor(
        MetricsExportSpanProcessor(meter_provider)
    )

    # Start the OpenTelemetry Pika instrumentation
    PikaInstrumentor().instrument()

    # Define and register custom metrics
    meter = meter_provider.get_meter(__name__)

    # Object Inspection Metrics
    objects_inspected_counter = meter.create_counter(
        name="objects_inspected",
        description="Count of objects inspected",
        unit="1",
    )

    successful_inspections_counter = meter.create_counter(
        name="successful_inspections",
        description="Count of successful object inspections",
        unit="1",
    )

    failed_inspections_counter = meter.create_counter(
        name="failed_inspections",
        description="Count of failed object inspections",
        unit="1",
    )

    # Other Metrics
    object_inspection_processing_time = meter.create_value_recorder(
        name="object_inspection_processing_time",
        description="Processing time for object inspections",
        unit="ms",
    )

    # RabbitMQ Connection Metrics
    rabbitmq_connection_status = meter.create_value_recorder(
        name="rabbitmq_connection_status",
        description="RabbitMQ connection status",
        unit="1",
    )

    # Retry Metrics
    retry_attempts_counter = meter.create_counter(
        name="retry_attempts",
        description="Count of retry attempts when connecting to RabbitMQ",
        unit="1",
    )

    # Minio Object Availability Metrics
    minio_object_availability = meter.create_value_recorder(
        name="minio_object_availability",
        description="Minio object availability status",
        unit="1",
    )

    # Script Uptime Metrics
    script_uptime_counter = meter.create_counter(
        name="script_uptime",
        description="Total uptime of the script",
        unit="s",
    )

    # Memory Usage Metrics
    memory_usage_recorder = meter.create_value_recorder(
        name="memory_usage",
        description="Memory usage of the script",
        unit="MB",
    )


# Logging
def setup_logging():
    logger.add(LOG_FILE, rotation=LOG_ROTATION, level=LOG_LEVEL, format=LOG_FORMAT)
