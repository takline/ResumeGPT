# Utils

The `./utils` folder contains utility functions and classes that support various operations in the ResumeGPT project. These utilities are essential for handling YAML files, generating PDFs, and performing other common tasks.

## yaml_handler.py

### YamlHandler Class
The `YamlHandler` class provides methods to read and write YAML files.

#### Key Methods

- `read_yaml(yaml_text: str = "", filename: str = "") -> Optional[dict]`: Reads YAML content from a string or a file.
- `write_yaml(data: dict, filename: str = None) -> None`: Writes a dictionary to a YAML file or prints it to stdout.
- `dict_to_yaml_string(data: dict) -> str`: Converts a dictionary to a YAML-formatted string.

### Usage

