"""
Provides functionality to validate the structure and data types of a resume YAML file.

This module defines `check_resume_format`, which compares a given resume YAML
against a predefined schema. It identifies discrepancies such as missing keys,
incorrect data types, or structural mismatches, and logs detailed error messages
with example snippets to guide the user in correcting their resume format.
"""
import yaml
from typing import Any, Dict, List, Tuple, Union # Ensure all necessary types are imported
from .. import config

# Logger for this module
logger = config.logger # Use the central logger from config

def check_resume_format(yaml_file_path: str) -> bool:
    """
    Checks if the resume YAML file at `yaml_file_path` conforms to an expected format.

    The function validates the presence of required keys and the types of their values
    against a predefined schema. If discrepancies are found, it logs detailed error
    messages, including example snippets for guidance, and returns False.

    Args:
        yaml_file_path (str): The path to the resume YAML file to be validated.

    Returns:
        bool: True if the resume format is correct according to the schema, False otherwise.
              Detailed errors are logged via `config.logger`.
    """
    # Defines the expected structure and types for the resume YAML.
    # This schema is used by the recursive `validate_format` function.
    expected_format: Dict[str, Any] = {
        "editing": bool,  # Flag to indicate if user is still editing
        "debug": bool,    # Debug mode flag
        "basic": {        # Basic personal information
            "name": str,
            "address": str,
            "email": str,
            "phone": str,
            "websites": [str], # List of website URLs
        },
        "objective": str, # Career objective statement
        "education": [    # List of educational qualifications
            {
                "school": str,
                "degrees": [{"names": [str]}] # Each degree can have multiple names (e.g., "M.S.", "Master of Science")
            }
        ],
        "experiences": [  # List of work experiences
            {
                "company": str,
                "skip_name": bool, # If true, company name might be omitted in some PDF layouts if title is primary
                "location": str,
                "titles": [       # Each experience can have multiple roles/titles
                    {
                        "name": str,       # Title name
                        "startdate": (int, str),  # Start date (year as int or string like "Month YYYY")
                        "enddate": (int, str),    # End date (similar to startdate, or "Present")
                    }
                ],
                "highlights": [str], # List of achievements/responsibilities
            }
        ],
        "projects": [     # List of personal or academic projects
            {
                "name": str,
                "hyperlink": bool,   # Whether the link should be an active hyperlink in the PDF
                "show_link": bool,   # Whether to display the link text in the PDF
                "date": str,         # Project completion date or duration
                "link": str,         # URL to the project
                "highlights": [str], # List of project details/achievements
            }
        ],
        "skills": [       # List of skill categories
            {
                "category": str,   # e.g., "Programming Languages", "Software"
                "skills": [str]    # List of skills in that category
            }
        ],
    }
    
    # Provides example YAML snippets for error messages to guide the user.
    example_snippets: Dict[str, str] = {
        "editing": "editing: true",
        "debug": "debug: false",
        "basic": """basic:
  name: John Doe
  address: Los Angeles, CA
  email: johndoe@example.com
  phone: 555-123-4567
  websites:
      - https://linkedin.com/johndoe
      - https://github.com/johndoe""",
        "objective": "objective: A Software Engineer with over 8 years of experience...",
        "education": """education:
  - school: University of California, Berkeley
    degrees:
      - names:
          - B.S. Computer Science
  - school: Stanford University
    degrees:
      - names:
          - M.S. Computer Science""",
        "experiences": """experiences:
  - company: Tech Innovators Inc.
    skip_name: false
    location: San Francisco, CA
    titles:
      - name: Lead Software Engineer
        startdate: 2022 # Can be integer for year
        enddate: "Present" # Or string for "Month YYYY" or "Present"
    highlights:
      - Led the development of a cloud-based platform, increasing user engagement by 50%.
      - Implemented a microservices architecture, reducing system downtime by 30%.""",
      "projects":"""projects:
- name: Example Github Project
  link: https://www.github.com/username/project
  date: "Jan 2024 - Mar 2024" # Or just "2023"
  hyperlink: true
  show_link: true
  highlights:
      - Developed a full-stack web application using React and Node.js.""",
        "skills": """skills:
  - category: Technical
    skills:
      - JavaScript
      - Python
  - category: Non-technical
    skills:
      - Strong problem-solving skills"""
    }
    
    def validate_format(actual_data: Any, expected_data_format: Any, current_path: str = "") -> List[Tuple[str, str, str]]:
        """
        Recursively validates the format of `actual_data` against `expected_data_format`.

        Args:
            actual_data (Any): The data segment from the user's YAML to validate.
            expected_data_format (Any): The corresponding segment from the `expected_format` schema.
            current_path (str, optional): The current dot-separated path in the YAML structure, for error reporting.

        Returns:
            List[Tuple[str, str, str]]: A list of error tuples. Each tuple contains:
                                        (path_to_error, expected_type_name, actual_type_name_or_status)
                                        Status can be "missing" if a key is absent.
        """
        errors_found: List[Tuple[str, str, str]] = []

        if isinstance(expected_data_format, dict): # If schema expects a dictionary
            if not isinstance(actual_data, dict):
                return [(current_path, "dictionary", type(actual_data).__name__)]

            for key, expected_type_for_key in expected_data_format.items():
                new_path = f"{current_path}/{key}" if current_path else key
                if key not in actual_data:
                    # Key is missing in the user's YAML
                    errors_found.append((new_path, str(expected_type_for_key), "missing"))
                else:
                    # Key exists, validate its content recursively
                    errors_found.extend(validate_format(actual_data[key], expected_type_for_key, new_path))
            return errors_found

        elif isinstance(expected_data_format, list): # If schema expects a list
            if not isinstance(actual_data, list):
                return [(current_path, "list", type(actual_data).__name__)]
            if not expected_data_format: # If schema expects an empty list (e.g. "websites": [])
                return [] # No specific type to check for items, an empty list is valid

            # Validate each item in the actual list against the first item in the expected format list (schema for list items)
            expected_item_format = expected_data_format[0]
            for index, item_in_actual_list in enumerate(actual_data):
                errors_found.extend(validate_format(item_in_actual_list, expected_item_format, f"{current_path}[{index}]"))
            return errors_found

        elif isinstance(expected_data_format, tuple): # If schema expects one of multiple types (e.g., (int, str) for dates)
             if not isinstance(actual_data, expected_data_format):
                expected_type_names = ", ".join([t.__name__ for t in expected_data_format])
                return [(current_path, f"one of ({expected_type_names})", type(actual_data).__name__)]
             return []

        else: # If schema expects a single specific type (e.g., str, bool)
            if not isinstance(actual_data, expected_data_format): # type: ignore
                return [(current_path, expected_data_format.__name__, type(actual_data).__name__)]
            return []

    try:
        with open(yaml_file_path, "r", encoding="utf-8") as file: # Added encoding
            actual_yaml_dict = yaml.safe_load(file)
        if not actual_yaml_dict: # Handle empty YAML file
             logger.error(f"Resume YAML file is empty or invalid: {yaml_file_path}")
             return False
    except FileNotFoundError:
        logger.error(f"Resume YAML file not found: {yaml_file_path}", exc_info=True)
        return False # Or re-raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing resume YAML file {yaml_file_path}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error reading resume YAML file {yaml_file_path}: {e}", exc_info=True)
        return False


    validation_errors = validate_format(actual_yaml_dict, expected_format)

    def get_example_snippet(path_key: str) -> Optional[str]:
        """Retrieve an example snippet for a given top-level or nested key."""
        # Try direct match first (e.g. "basic/name")
        if path_key in example_snippets:
            return example_snippets[path_key]
        # Try top-level key if nested path_key not found
        top_level_key = path_key.split('/')[0].split('[')[0]
        return example_snippets.get(top_level_key)

    # Consolidate errors for more user-friendly logging
    if validation_errors:
        error_log_messages = ["Resume format validation failed with the following issues:"]
        # Group errors by the main section (first part of the path)
        grouped_errors: Dict[str, List[str]] = {}
        for path, expected, actual_or_status in validation_errors:
            main_section_key = path.split('/')[0].split('[')[0] # e.g., "experiences" from "experiences[0]/company"

            error_detail = ""
            if actual_or_status == "missing":
                error_detail = f"  - Key '{path}' is missing. Expected type: {expected}."
            else:
                error_detail = f"  - Key '{path}' has incorrect type. Expected: {expected}, Got: {actual_or_status}."
            
            if main_section_key not in grouped_errors:
                grouped_errors[main_section_key] = []
            grouped_errors[main_section_key].append(error_detail)

        for section, section_errors in grouped_errors.items():
            error_log_messages.append(f"\nIn section '{section}':")
            error_log_messages.extend(section_errors)
            snippet = get_example_snippet(section)
            if snippet:
                error_log_messages.append(f"  Example format for '{section}':\n```yaml\n{snippet}\n```")
        
        logger.error("\n".join(error_log_messages))
        return False
    else:
        logger.info(f"Resume format check passed for {yaml_file_path}.")
        return True

[end of utils/resume_format_checker.py]
