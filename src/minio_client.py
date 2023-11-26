# src/minio_client.py
"""
Minio client module for accessing objects in the 'uploads' bucket.
"""
from minio import Minio

from config_utils import get_env_variable


def initialize_minio_client():
    """
    Initialize the Minio client.

    Returns:
    - Minio: An instance of the Minio client.
    """
    minio_access_key = get_env_variable("MINIO_ACCESS_KEY")
    minio_secret_key = get_env_variable("MINIO_SECRET_KEY")
    minio_endpoint = get_env_variable("MINIO_ENDPOINT", "localhost")

    if not minio_access_key or not minio_secret_key or not minio_endpoint:
        raise ValueError(
            "Please set MINIO_ACCESS_KEY, MINIO_SECRET_KEY, and MINIO_ENDPOINT environment variables."
        )

    return Minio(
        minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False,  # Set to True if using HTTPS
    )


def get_bucket_name():
    """
    Get the name of the Minio bucket.

    Returns:
    - str: The name of the Minio bucket.
    """
    return "uploads"
