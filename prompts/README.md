# Prompts

The `./prompts` folder contains the prompt templates used by the ResumeGPT project. These templates are essential for generating structured and contextually relevant prompts for various tasks such as highlighting resume sections, matching skills, writing summaries, and suggesting improvements. This folder includes the following key components:

## prompts.py

### Prompts Class
The `Prompts` class is responsible for loading and managing prompt templates from a YAML configuration file.

#### Key Methods

- `__init__(self, yaml_path: str)`: Initializes the `Prompts` class by loading the YAML file and setting up the lookup dictionary.
  - **Args**:
    - `yaml_path (str)`: Path to the YAML file containing prompt configurations.
  - **Usage**: This method is called when an instance of the `Prompts` class is created. It loads the prompt templates from the specified YAML file and organizes them into a lookup dictionary.

- `_load_prompts(yaml_path: str) -> dict`: Loads prompts from a YAML file and organizes them into a lookup dictionary.
  - **Args**:
    - `yaml_path (str)`: Path to the YAML file containing prompt configurations.
  - **Returns**: A dictionary with prompt types as keys and lists of message templates as values.
  - **Usage**: This method is called internally by the `__init__` method to load the prompt templates from the YAML file and organize them into a lookup dictionary.

## prompts.yaml
Contains the actual prompt templates used by the `Prompts` class. These templates include:

- **System Messages**: Provide context and instructions for the language model.
- **Job Posting Templates**: Define the structure and content of job postings.
- **Resume Templates**: Define the structure and content of resumes.
- **Instruction Messages**: Provide specific instructions for the language model to follow.
- **Criteria Messages**: Define the criteria that the language model must meet.
- **Steps Messages**: Outline the steps that the language model should follow to complete a task.

### Example of a Prompt Template
Here is an example of a prompt template from the `prompts.yaml` file:

```
