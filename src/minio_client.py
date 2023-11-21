# minio_client.py
"""
Minio client module for accessing objects in the 'uploads' bucket.
"""
import os

from minio import Minio
from minio.error import S3Error


def access_minio_objects(object_name):
    """
    Access Minio objects in the 'uploads' bucket and check if the specified object exists.

    Parameters:
    - object_name (str): The name of the object to check in the Minio bucket.

    Returns:
    - None
    """
    # Retrieve Minio server details from environment variables
    minio_access_key = os.getenv("MINIO_ACCESS_KEY")
    minio_secret_key = os.getenv("MINIO_SECRET_KEY")
    minio_endpoint = os.getenv("MINIO_ENDPOINT")
    minio_bucket_name = "uploads"

    # Validate that environment variables are set
    if not minio_access_key or not minio_secret_key or not minio_endpoint:
        print(
            "Please set MINIO_ACCESS_KEY, MINIO_SECRET_KEY, and MINIO_ENDPOINT environment variables."
        )
        return

    # Initialize the Minio client
    minio_client = Minio(
        minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False,  # Set to True if using HTTPS
    )

    try:
        # Check if the specified object exists in the bucket
        minio_client.stat_object(minio_bucket_name, object_name)

        print(f"Object '{object_name}' found in '{minio_bucket_name}' bucket.")
    except S3Error as e:
        print(
            f"Object '{object_name}' not found in '{minio_bucket_name}' bucket. Error: {e}"
        )
