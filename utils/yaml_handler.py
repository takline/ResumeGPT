"""
Provides utility functions for reading and writing YAML files.

This module centralizes YAML operations, using PyYAML's SafeLoader and SafeDumper
to ensure safer YAML processing. It handles reading from strings or files,
and writing to files or converting data to YAML strings. It also includes
error handling and logging for YAML operations.
"""
import yaml
from io import StringIO # Used for converting dict to YAML string in memory
from typing import Optional, Dict, Any # For type hinting
import sys # Used by write_yaml if filename is None (prints to stdout)
from .. import config # For logger access

# Module-level logger
logger = config.logger # Use the central logger

def read_yaml(yaml_text: str = "", filename: str = "") -> Optional[Dict[str, Any]]:
    """
    Reads YAML content from a text string or a specified file.

    Prioritizes `yaml_text` if provided; otherwise, attempts to read from `filename`.
    Uses `yaml.SafeLoader` for security.

    Args:
        yaml_text (str, optional): YAML content as a string. Defaults to "".
        filename (str, optional): Path to the YAML file. Defaults to "".

    Returns:
        Optional[Dict[str, Any]]: Parsed YAML content as a dictionary if successful,
                                  None if neither `yaml_text` nor `filename` is provided,
                                  or if the YAML content is empty or invalid resulting in None.

    Raises:
        yaml.YAMLError: If there is an error parsing the YAML content.
        FileNotFoundError: If `filename` is provided but the file is not found.
        IOError: For other file reading issues.
        Exception: For other unexpected errors during loading.
    """
    if not yaml_text and not filename:
        logger.warning("read_yaml called with no yaml_text or filename.")
        return None

    loaded_data: Optional[Dict[str, Any]] = None
    source_description = ""

    if yaml_text:
        source_description = "text string"
        try:
            loaded_data = yaml.load(StringIO(yaml_text), Loader=yaml.SafeLoader)
        except yaml.YAMLError as e:
            logger.error(f"Could not parse YAML from text string: {e}", exc_info=True)
            raise
        except Exception as e: # Catch any other unexpected error during string loading
            logger.error(f"Unexpected error loading YAML from text string: {e}", exc_info=True)
            raise
    elif filename:
        source_description = f"file '{filename}'"
        try:
            with open(filename, "r", encoding="utf-8") as data_stream: # Added encoding
                loaded_data = yaml.safe_load(data_stream)
        except FileNotFoundError:
            logger.error(f"YAML file not found: {filename}", exc_info=True)
            raise
        except yaml.YAMLError as e:
            logger.error(f"Could not parse YAML from file {filename}: {e}", exc_info=True)
            raise
        except IOError as e:
            logger.error(f"IOError reading YAML file {filename}: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading YAML file {filename}: {e}", exc_info=True)
            raise

    if loaded_data is None:
        logger.warning(f"YAML content from {source_description} resulted in None (empty or invalid).")

    return loaded_data


def write_yaml(data: Dict[str, Any], filename: Optional[str] = None) -> None:
    """
    Writes a dictionary to a YAML file or prints it to stdout if no filename is given.

    Uses `yaml.SafeDumper` for safer YAML generation and preserves key order from Python 3.7+ dicts.
    Sets `allow_unicode=True` for better handling of non-ASCII characters.

    Args:
        data (Dict[str, Any]): Data (dictionary) to be written to YAML.
        filename (Optional[str]): Path to the output YAML file. If None, YAML is printed to stdout.
                                 Defaults to None.

    Raises:
        yaml.YAMLError: If there is an error during YAML dumping.
        IOError: If `filename` is provided and there's an error writing to the file.
        Exception: For other unexpected errors.
    """
    # PyYAML's Dumper by default may not preserve insertion order for dicts in older Python versions.
    # Modern Python dicts (3.7+) preserve insertion order, and SafeDumper should respect this.
    # `sort_keys=False` is used to ensure insertion order is maintained in the output.
    try:
        if filename:
            with open(filename, "w", encoding="utf-8") as stream: # Added encoding
                yaml.dump(data, stream, Dumper=yaml.SafeDumper, sort_keys=False, allow_unicode=True)
            logger.debug(f"Data successfully written to YAML file: {filename}")
        else:
            # Output to stdout if no filename provided
            yaml.dump(data, sys.stdout, Dumper=yaml.SafeDumper, sort_keys=False, allow_unicode=True)
    except yaml.YAMLError as e:
        log_target = f"'{filename}'" if filename else "stdout"
        logger.error(f"Error writing YAML to {log_target}: {e}", exc_info=True)
        raise
    except IOError as e:
        if filename: # IOError is more relevant if a filename was specified
            logger.error(f"IOError writing YAML to file {filename}: {e}", exc_info=True)
            raise
        else: # Should be rare for stdout
            logger.error(f"IOError writing YAML to stdout: {e}", exc_info=True)
            raise
    except Exception as e:
        log_target = f"'{filename}'" if filename else "stdout"
        logger.error(f"Unexpected error writing YAML to {log_target}: {e}", exc_info=True)
        raise


def dict_to_yaml_string(data: Dict[str, Any]) -> str:
    """
    Converts a dictionary to a YAML-formatted string.

    Uses `yaml.SafeDumper` and preserves key order. `allow_unicode=True`.

    Args:
        data (Dict[str, Any]): Data (dictionary) to be converted to YAML string.

    Returns:
        str: YAML-formatted string.

    Raises:
        yaml.YAMLError: If there is an error during YAML dumping.
        Exception: For other unexpected errors.
    """
    try:
        stream = StringIO()
        yaml.dump(data, stream=stream, Dumper=yaml.SafeDumper, sort_keys=False, allow_unicode=True)
        return stream.getvalue()
    except yaml.YAMLError as e:
        logger.error(f"Failed to convert dict to YAML string: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error converting dict to YAML string: {e}", exc_info=True)
        raise
