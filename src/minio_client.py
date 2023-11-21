# minio_client.py
"""
Minio client module for accessing objects in the 'uploads' bucket.
"""

import json
import mimetypes
import os

from minio import Minio
from minio.error import S3Error


class Object:
    """
    Represents an object in the 'uploads' bucket.
    """

    def __init__(self, name):
        """
        Create an Object instance.

        Parameters:
        - name (str): The name of the object.
        """
        self.name = name


class InspectObject(Object):
    """
    Subclass of Object with additional functions to inspect the object.
    """

    def __init__(self, name):
        super().__init__(name)

    def read_object(self):
        """
        Read the content of the object from the 'uploads' bucket.

        Returns:
        - str: An empty string.
        """
        minio_client = self._initialize_minio_client()

        try:
            data = minio_client.get_object(self._bucket_name, self.name)
            return ""

        except S3Error as e:
            print(
                f"Object '{self.name}' not found in '{self._bucket_name}' bucket. Error: {e}"
            )
            return None

    def determine_file_type(self):
        """
        Determine the file type of the object.

        Returns:
        - str: The file type of the object.
        """
        _, file_extension = os.path.splitext(self.name)
        file_extension = file_extension[1:]
        file_type, _ = mimetypes.guess_type(self.name)

        return file_type or f"Unknown ({file_extension})"

    def inspect(self):
        """
        Inspect the object by determining its file type.

        Returns:
        - dict: A dictionary containing the object's name and file type.
        """
        file_type = self.determine_file_type()

        return {
            "name": self.name,
            "content": "",  # Return an empty string for content
            "file_type": file_type,
        }

    def _initialize_minio_client(self):
        """
        Initialize the Minio client.

        Returns:
        - Minio: An instance of the Minio client.
        """
        minio_access_key = os.getenv("MINIO_ACCESS_KEY")
        minio_secret_key = os.getenv("MINIO_SECRET_KEY")
        minio_endpoint = os.getenv("MINIO_ENDPOINT")

        if not minio_access_key or not minio_secret_key or not minio_endpoint:
            raise ValueError(
                "Please set MINIO_ACCESS_KEY, MINIO_SECRET_KEY, and MINIO_ENDPOINT environment variables."
            )

        return Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False,
        )

    @property
    def _bucket_name(self):
        """
        Get the name of the Minio bucket.

        Returns:
        - str: The name of the Minio bucket.
        """
        return "uploads"
