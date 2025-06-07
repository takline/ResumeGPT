"""
Configuration management for the ResumeGPT application.

This module defines various project-wide configurations, including paths,
API settings, default model parameters, and utility settings. It also handles
the retrieval of the OpenAI API key, prioritizing environment variables and
prompting the user if necessary.
"""
import logging
import os
import configparser
from langchain_openai import ChatOpenAI

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- Customizable User Settings ---
# Specifies the default filename for the user's resume within the DATA_PATH.
YOUR_RESUME_NAME = "sample_resume.yaml"

# --- Core Path Definitions ---
# Absolute path to the project's root directory.
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Path to the directory for storing data like resumes, job postings, logs.
DATA_PATH = os.path.join(PROJECT_PATH, "data")
# Path to test data files.
TESTS_DATA_PATH = os.path.join(PROJECT_PATH, "tests", "test_data")
# Default path to the user's resume file.
DEFAULT_RESUME_PATH = os.path.join(DATA_PATH, YOUR_RESUME_NAME)
# Path for logging background task activities.
BACKGROUND_TASKS_LOG = os.path.join(DATA_PATH, "background_tasks", "tasks.log")
# Path to static resources like fonts.
RESOURCES_PATH = os.path.join(PROJECT_PATH, "resources")
# Path to prompt template configurations.
PROMPTS_PATH = os.path.join(PROJECT_PATH, "prompts")
# Path to the configuration directory itself.
CONFIG_PATH = os.path.join(PROJECT_PATH, "config") # Current directory

# --- Prompt Configuration Files ---
PROMPTS_YAML = os.path.join(PROMPTS_PATH, "prompts.yaml")
DESCRIPTIONS_YAML = os.path.join(PROMPTS_PATH, "extractor_descriptions.yaml")

# --- Network Request Settings ---
# Default headers for HTTP requests to mimic a browser.
REQUESTS_HEADERS = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
}
# Default timeout for network requests in seconds.
REQUEST_TIMEOUT = 10 # Added a default request timeout

# --- LLM Model Configuration ---
# Default LangChain chat model class to use.
CHAT_MODEL = ChatOpenAI
# Default OpenAI model name.
MODEL_NAME = "gpt-4o"
# Default temperature for LLM responses (creativity vs. determinism).
TEMPERATURE = 0.3

# --- Utility Settings ---
# Command used to open files (e.g., generated resumes) automatically.
# Example for VS Code: "code -r"
# Example for Cursor: "cursor -r"
# Example for Linux (default): "xdg-open"
# Example for macOS (default): "open"
OPEN_FILE_COMMAND = "cursor -r"
# Maximum number of concurrent worker threads for background tasks.
MAX_CONCURRENT_WORKERS = 4
# Maximum number of retries for operations like downloading.
MAX_RETRIES = 3
# Backoff factor for retry attempts (e.g., delay = factor * (2 ** (attempt - 1))).
BACKOFF_FACTOR = 5


# --- API Key Management ---
def ensure_openai_api_key():
    """
    Ensures the OpenAI API key is available as an environment variable.

    It first checks if 'OPENAI_API_KEY' is already set in the environment.
    If not found, it prompts the user to enter their API key via standard input
    and then sets this key as an environment variable for the current session.
    This prevents the key from being hardcoded or written to disk by this application.
    """
    if "OPENAI_API_KEY" not in os.environ:
        logger.info(
            "OPENAI_API_KEY not found in environment. User will be prompted to enter their key."
        )
        # It's generally better for the application to fail or guide the user to set the env var
        # rather than inputting it directly if this is a library.
        # However, for a CLI tool, this input can be acceptable.
        api_key_input = input("Please enter your OpenAI API key: ")
        if api_key_input:
            os.environ["OPENAI_API_KEY"] = api_key_input
            logger.info("OPENAI_API_KEY has been set for the current session.")
        else:
            logger.error("No OpenAI API key provided. Application may not function correctly.")
            # Consider raising an error or exiting if the key is essential for all operations.
            # raise ValueError("OpenAI API key is required to run the application.")


# Ensure the API key is checked/set when this module is imported.
ensure_openai_api_key()

