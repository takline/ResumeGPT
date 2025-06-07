"""
Utility functions for file and dictionary operations.

This module provides helpers for:
- Reading file content.
- Searching for keys within nested dictionary structures.
- Safely retrieving fields from dictionaries.
"""
import os
from typing import Union, List, Generator, Optional, Dict, Any
from .. import config
# from .. import utils # Self-reference here, direct call for recursive functions


def read_jobfile(filename: str) -> str:
    """
    Reads the entire content of a specified file and returns it as a stripped string.

    Typically used for reading job posting text files or similar data.

    Args:
        filename (str): The path to the file to be read.

    Returns:
        str: The content of the file, with leading/trailing whitespace removed.

    Raises:
        FileNotFoundError: If the file is not found.
        IOError: If there are other issues reading the file.
    """
    try:
        with open(filename, "r", encoding="utf-8") as stream: # Added encoding
            return stream.read().strip()
    except FileNotFoundError:
        config.logger.error(f"File not found: {filename}", exc_info=True)
        raise
    except IOError as e: # Catch other IO errors
        config.logger.error(f"Error reading file {filename}: {e}", exc_info=True)
        raise # Re-raise after logging


def generator_key_in_nested_dict(
    keys_to_find: Union[str, List[str]], nested_structure: Any
) -> Generator[Any, None, None]:
    """
    Recursively searches for and yields values associated with specified key(s)
    within a nested structure (dictionaries and lists).

    Args:
        keys_to_find (Union[str, List[str]]): A single key (string) or a list of keys
                                             to search for.
        nested_structure (Any): The nested dictionary or list to search within.

    Yields:
        Generator[Any, None, None]: Values corresponding to the found keys.
    """
    if isinstance(nested_structure, dict):
        for key, value in nested_structure.items():
            if (isinstance(keys_to_find, list) and key in keys_to_find) or \
               (isinstance(keys_to_find, str) and key == keys_to_find):
                yield value
            # Recursively search in value if it's a dict or list
            yield from generator_key_in_nested_dict(keys_to_find, value)
    elif isinstance(nested_structure, list):
        for item in nested_structure:
            # Recursively search in each item of the list
            yield from generator_key_in_nested_dict(keys_to_find, item)


def get_dict_field(field: str, data_dict: Dict[str, Any], default_value: Optional[Any] = None) -> Optional[Any]:
    """
    Safely retrieves a field from a dictionary.

    If the field (key) is present in the dictionary, its value is returned.
    If the field is missing, a debug log message is recorded, and `default_value` (None by default) is returned.

    Args:
        field (str): The key of the field to retrieve.
        data_dict (Dict[str, Any]): The dictionary to search.
        default_value (Optional[Any]): The value to return if the field is not found.
                                       Defaults to None.

    Returns:
        Optional[Any]: The value of the field if found, otherwise `default_value`.
    """
    if not isinstance(data_dict, dict):
        config.logger.debug(f"Attempted to get field '{field}' from a non-dictionary type: {type(data_dict)}. Returning default value.")
        return default_value

    try:
        return data_dict[field]
    except KeyError:
        # Log a debug message as this might be an expected case for optional fields.
        config.logger.debug(f"Field '{field}' is missing in the provided dictionary. Returning default value.")
    return default_value
