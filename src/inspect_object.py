# inspect_object.py
"""
Module defining InspectObject class.
"""

import mimetypes
import os

from loguru import logger

from minio_client import get_bucket_name, initialize_minio_client
from objects import Object


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
        minio_client = initialize_minio_client()

        try:
            data = minio_client.get_object(get_bucket_name(), self.name)
            # Do not read the content as bytes
            return ""

        except Exception as e:
            logger.error(f"Object '{self.name}' not found. Error: {e}")
            return None

    def determine_file_type(self):
        """
        Determine the file type of the object.

        Returns:
        - str: The file type of the object.
        """
        _, file_extension = os.path.splitext(self.name)
        file_extension = file_extension[1:]  # Remove the leading dot
        file_type, _ = mimetypes.guess_type(self.name)

        return file_type or f"Unknown ({file_extension})"

    def inspect(self):
        """
        Inspect the object by determining its file type.

        Returns:
        - dict: A dictionary containing the object's name, content, and file type.
        """
        file_type = self.determine_file_type()
        result = {
            "name": self.name,
            "content": "",  # Return an empty string for content
            "file_type": file_type,
        }

        # Call the appropriate function based on file type
        if file_type.startswith("image"):
            result["message"] = self._inspect_image(result)
        elif file_type.startswith("video"):
            result["message"] = self._inspect_video(result)
        elif file_type.startswith("audio"):
            result["message"] = self._inspect_audio(result)
        elif file_type.startswith("text"):
            result["message"] = self._inspect_text(result)
        else:
            result["message"] = self._inspect_other(result)

        # Log the result message
        logger.info(result["message"])

        return result

    def _inspect_image(self, result):
        return f"This is an image: {result['name']}"

    def _inspect_video(self, result):
        return f"This is a video: {result['name']}"

    def _inspect_audio(self, result):
        return f"This is an audio file: {result['name']}"

    def _inspect_text(self, result):
        return f"This is a text file: {result['name']}"

    def _inspect_other(self, result):
        return f"This is of an unknown type: {result['name']}"
