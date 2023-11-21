# main.py
"""
Main script for checking the existence of a specified Minio object in the 'uploads' bucket.
"""

import sys

from minio_client import access_minio_objects


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
    if len(sys.argv) != 2:
        print("Usage: python main.py <object_name>")
        sys.exit(1)

    object_name = sys.argv[1]
    access_minio_objects(object_name)


if __name__ == "__main__":
    main()
