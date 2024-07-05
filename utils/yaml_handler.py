import yaml
from ruamel.yaml.error import YAMLError
from io import StringIO
from typing import Optional
from .. import config


def read_yaml(yaml_text: str = "", filename: str = "") -> Optional[dict]:
    """
    Reads YAML content from a string or a file.

    Args:
        yaml_text (str): YAML content as a string.
        filename (str): Path to the YAML file.

    Returns:
        dict: Parsed YAML content as a dictionary.
    """
    if not yaml_text and not filename:
        config.logger.warning("Neither yaml text nor filename have been provided.")
        return None
    if yaml_text:
        try:
            return yaml.load(yaml_text)
        except YAMLError as e:
            config.logger.error(f"The text could not be read.")
            raise e
    try:
        with open(filename, "r") as data:
            return yaml.safe_load(data)
    except YAMLError as e:
        config.logger.error(f"The {filename} could not be read.")
        raise e
    except Exception as e:
        config.logger.error(
            f"The {filename} could not be written due to an unknown error."
        )
        raise e


def write_yaml(data: dict, filename: str = None) -> None:
    """
    Writes a dictionary to a YAML file or prints it to stdout.

    Args:
        data (dict): Data to be written to YAML.
        filename (str): Path to the YAML file.
    """
    yaml.allow_unicode = True
    try:
        if filename:
            with open(filename, "w") as stream:
                yaml.dump(data, stream)
        else:
            yaml.dump(data, sys.stdout)
    except YAMLError as e:
        config.logger.error(f"The {filename} could not be written.")
        raise e
    except Exception as e:
        config.logger.error(
            f"The {filename} could not be written due to an unknown error."
        )
        raise e


def dict_to_yaml_string(data: dict) -> str:
    """
    Converts a dictionary to a YAML-formatted string.

    Args:
        data (dict): Data to be converted to YAML string.

    Returns:
        str: YAML-formatted string.
    """
    yaml.allow_unicode = True
    try:
        yaml.allow_unicode = True
        stream = StringIO()
        yaml.dump(data, stream=stream)
        return stream.getvalue()
    except YAMLError as e:
        config.logger.error("Failed to convert dict to YAML string.")
        raise e
