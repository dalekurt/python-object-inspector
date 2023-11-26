# objects.py
"""
Module defining classes for Minio objects.
"""


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
