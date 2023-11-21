# main.py
"""
Main script for checking the existence of a specified Minio object in the 'uploads' bucket.
"""

import json
import sys

from loguru import logger

from minio_client import InspectObject


def main():
    """
    Check the existence of a specified Minio object in the 'uploads' bucket.

    Usage:
    $ python main.py <object_name>

    Parameters:
    - object_name (str): The name of the object to check in the Minio bucket.

    Returns:
    - None
    """
    # Configure the logger to write logs to a file
    logger.add("app.log", rotation="5 MB", level="DEBUG")

    if len(sys.argv) != 2:
        logger.error("Invalid number of arguments. Usage: python main.py <object_name>")
        sys.exit(1)

    object_name = sys.argv[1]

    try:
        inspect_object = InspectObject(object_name)
        result = inspect_object.inspect()

        if result["content"] is not None:
            logger.info(
                f"Object inspection for '{object_name}' completed successfully. Result: {result}"
            )
        else:
            logger.warning(f"Object '{object_name}' not found in 'uploads' bucket.")
    except Exception as e:
        logger.error(f"Error inspecting object '{object_name}': {e}")


if __name__ == "__main__":
    main()
