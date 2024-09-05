import yaml
from .. import config

def check_resume_format(yaml_file_path: str) -> bool:
    """Check if the resume format is correct and provide suggestions for corrections.

    Args:
        yaml_file_path (str): The path to the resume YAML file.

    Returns:
        bool: True if the format is correct, False otherwise.
    """
    expected_format = {
        "editing": bool,
        "debug": bool,
        "basic": {
            "name": str,
            "address": str,
            "email": str,
            "phone": str,
            "websites": [str],
        },
        "objective": str,
        "education": [{"school": str, "degrees": [{"names": [str]}]}],
        "experiences": [
            {
                "company": str,
                "skip_name": bool,
                "location": str,
                "titles": [
                    {
                        "name": str,
                        "startdate": (int, str),  # startdate can be int or str
                        "enddate": (int, str),  # enddate can be int or str
                    }
                ],
                "highlights": [str],
            }
        ],
        "projects": [
            {
                "name": str,
                "hyperlink": bool,
                "show_link": bool,
                "date": str,
                "link": str,
                "highlights": [str],
            }
        ],
        "skills": [{"category": str, "skills": [str]}],
    }
    
    example_snippets = {
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
        startdate: 2022
        enddate: 2024
    highlights:
      - Led the development of a cloud-based platform, increasing user engagement by 50%.
      - Implemented a microservices architecture, reducing system downtime by 30%.
      - Mentored a team of junior developers, fostering a culture of continuous learning and improvement.
      - Spearheaded the integration of AI-driven features, enhancing product capabilities and user satisfaction.""",
      "projects":"""projects:
- name: Example Github Project
  link: https://www.github.com/username/project
  date: Jan 2024
  hyperlink: false
  show_link: false
  highlights:
      - Developed a full-stack web application using React and Node.js, showcasing a dynamic portfolio with real-time updates.
      - Implemented CI/CD pipelines using GitHub Actions, ensuring seamless deployment and integration.
      - Integrated third-party APIs for enhanced functionality, including payment processing and social media sharing.
      - Wrote comprehensive documentation and unit tests, ensuring code quality and ease of collaboration.
      - Conducted code reviews and collaborated with open-source contributors, fostering a community-driven development process.
      - Achieved over 1,000 stars on GitHub, demonstrating the project's popularity and utility within the developer community.""",
        "skills": """skills:
  - category: Technical
    skills:
      - JavaScript
      - Python
      - AWS
      - Docker
      - Kubernetes
      - React
      - Node.js
      - Microservices
      - CI/CD
      - SQL
      - NoSQL
      - REST APIs
  - category: Non-technical
    skills:
      - Strong problem-solving skills
      - Excellent communication
      - Team leadership
      - Project management
      - Agile methodologies"""
    }
    
    def validate_format(actual, expected, path=""):
        """Recursively validate the format of the actual YAML content against the expected format.

        Args:
            actual (Any): The actual content from the YAML file.
            expected (Any): The expected format to validate against.
            path (str, optional): The current path in the YAML structure. Defaults to "".

        Returns:
            list: A list of errors found during validation.
        """
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return [(path, "dict", type(actual).__name__)]
            errors = []
            for key, expected_type in expected.items():
                if key not in actual:
                    errors.append((f"{path}/{key}", expected_type, "missing"))
                else:
                    errors.extend(validate_format(actual[key], expected_type, f"{path}/{key}"))
            return errors
        elif isinstance(expected, list):
            if not isinstance(actual, list):
                return [(path, "list", type(actual).__name__)]
            if len(expected) == 0:
                return []  # No specific type to check against
            errors = []
            for index, item in enumerate(actual):
                errors.extend(validate_format(item, expected[0], f"{path}[{index}]"))
            return errors
        else:
            if not isinstance(actual, expected):
                return [(path, expected.__name__, type(actual).__name__)]
            return []

    with open(yaml_file_path, "r") as file:
        actual_yaml_dict = yaml.safe_load(file)

    errors = validate_format(actual_yaml_dict, expected_format)

    def get_example_snippet(path):
        """Retrieve an example snippet for a given path.

        Args:
            path (str): The path in the YAML structure.

        Returns:
            str: An example snippet corresponding to the path.
        """
        key = path.split('/')[1]
        key = key.split('[')[0]
        return example_snippets.get(key, None)

    consolidated_errors = {}

    for error in errors:
        path, expected, actual = error
        main_key = path.split('/')[1]
        sub_key = path.split('/')[-1]
        if main_key not in consolidated_errors:
            consolidated_errors[main_key] = {"missing": [], "incorrect": [], "entries": []}
        
        if main_key == "experiences":
            entry_index = path.split('/')[2].split('[')[-1][:-1]
            consolidated_errors[main_key]["entries"].append(f"experiences[{entry_index}]")
            
        if main_key == "projects":
            entry_index = path.split('/')[2].split('[')[-1][:-1]
            consolidated_errors[main_key]["entries"].append(f"projects[{entry_index}]")
        
        if actual == "missing":
            consolidated_errors[main_key]["missing"].append(sub_key)
        elif isinstance(expected, str):
            consolidated_errors[main_key]["incorrect"].append((sub_key, actual, expected))
        else:
            consolidated_errors[main_key]["incorrect"].append((sub_key, actual, expected.__name__))
    logger_error = ""
    if consolidated_errors:
        for main_key, issues in consolidated_errors.items():
            example_snippet = get_example_snippet(f"/{main_key}")
            if main_key == "experiences" and issues["entries"]:
                entries = ", ".join(set(issues["entries"]))
                logger_error+=f"\nYou have formatting errors in these experiences entries: '{entries}'. Make sure they are formatted like this example:\n\n```yaml\n{example_snippet}\n```"
            if main_key == "projects" and issues["entries"]:
                entries = ", ".join(set(issues["entries"]))
                logger_error+=f"\nYou have formatting errors in these projects entries: '{entries}'. Make sure they are formatted like this example:\n\n```yaml\n{example_snippet}\n```"
            if issues["missing"]:
                missing_keys = ", ".join(issues["missing"])
                if main_key=="projects":
                    logger_error+="The 'Projects' section is currently empty. This is not an issue, but just an FYI for your awareness."
                else:
                    logger_error+=f"\nYou are missing these keys: '{missing_keys}' in the '{main_key}' section. Make sure it is formatted like this example:\n\n```yaml\n{example_snippet}\n```"
            if issues["incorrect"]:
                for sub_key, actual_type, expected_type in issues["incorrect"]:
                    logger_error+=f"The value for '{sub_key}' in the '{main_key}' section is of type '{actual_type}'. \nExpected type: '{expected_type}'. Make sure it is formatted like this example:\n\n```yaml\n{example_snippet}\n```"
        config.logger.error(logger_error)
        return False
    else:
        return True
