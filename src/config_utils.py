# src/config_utils.py
"""
Configuration Utility Module
"""

import os

from dotenv import load_dotenv

load_dotenv()


def get_env_variable(env_name, default=None, cast_func=None):
    """
    Get the value of an environment variable.

    Parameters:
    - env_name (str): The name of the environment variable.
    - default: Default value if the environment variable is not set.
    - cast_func (callable): Optional function to cast the environment variable value.

    Returns:
    - The value of the environment variable.
    """
    value = os.getenv(env_name, default)
    return cast_func(value) if cast_func is not None else value
