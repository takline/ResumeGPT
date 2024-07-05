# Configuration

The `./config` folder contains configuration settings and utilities that are essential for the proper functioning of the ResumeGPT project. This folder includes the following key components:

### Logger Initialization
Sets up a logger for the project to handle logging throughout the application.

### Project Paths
Defines various paths used in the project:
- `PROJECT_PATH`: The root directory of the project.
- `DATA_PATH`: Directory for storing data files.
- `RESOURCES_PATH`: Directory for storing resource files.
- `DEFAULT_RESUME_PATH`: Default path for the resume YAML file.

### Open File Command
- `OPEN_FILE_COMMAND`: tells ResumeGPT how to open a file from the command line

### Model Configuration
Specifies the configuration for the language model:
- `CHAT_MODEL`: The chat model class to be used.
- `MODEL_NAME`: The name of the model (e.g., "gpt-4o").
- `TEMPERATURE`: The temperature setting for the model, which controls the randomness of the output.

### OpenAI API Key
Ensures the presence of the OpenAI API key in the environment. If the key is not found, the user is prompted to enter it.

## config.ini

The `config.ini` file is where users provide their resume information and other personal details. This file includes the following sections:

### [global]
- `author`: The author's name.
- `email`: The author's email address.
- `address`: The author's physical address.
- `phone`: The author's phone number.
- `github`: The author's GitHub profile URL.
- `linkedin`: The author's LinkedIn profile URL.
- `debug`: A flag to enable or disable debug mode.
