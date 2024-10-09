import logging
import os
from langchain_openai import ChatOpenAI
import shutil


# Your resume filename here:
YOUR_RESUME_NAME = "sample_resume.yaml"

# Define project paths
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_PATH, "data")
TESTS_DATA_PATH = os.path.join(PROJECT_PATH, "tests/test_data/")
DEFAULT_RESUME_PATH = os.path.join(DATA_PATH, YOUR_RESUME_NAME)
BACKGROUND_TASKS_LOG = os.path.join(DATA_PATH, "background_tasks", "tasks.log")
RESOURCES_PATH = os.path.join(PROJECT_PATH, "resources")
PROMPTS_PATH = os.path.join(PROJECT_PATH, "prompts")
CONFIG_PATH = os.path.join(PROJECT_PATH, "config")
PROMPTS_YAML = os.path.join(PROMPTS_PATH, "prompts.yaml")
DESCRIPTIONS_YAML = os.path.join(PROMPTS_PATH, "extractor_descriptions.yaml")
REQUESTS_HEADERS = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
}

# Define model configuration
CHAT_MODEL = ChatOpenAI
MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.3
MAX_CONCURRENT_WORKERS = 4
MAX_RETRIES = 3
BACKOFF_FACTOR = 5


# Confirm presence of OpenAI API key
def ensure_openai_api_key():
    if "OPENAI_API_KEY" not in os.environ:
        logger.info(
            "OPENAI_API_KEY not found in environment. User will be prompted to enter their key."
        )
        os.environ["OPENAI_API_KEY"] = input("Enter your OpenAI API key:")


ensure_openai_api_key()


def command_exists(command):
    """Check if a command exists on the system."""
    return shutil.which(command) is not None


def get_open_file_command():
    """Determine the appropriate command to open files."""
    preferred_commands = [
        ("cursor", "cursor -r"),
        ("code", "code -r"),
        ("subl", "subl"),  # Sublime Text
        ("atom", "atom"),  # Atom
        ("notepad++", "notepad++"),  # Notepad++ (Windows)
        ("open", "open"),  # Default macOS opener
    ]

    for cmd, full_cmd in preferred_commands:
        if command_exists(cmd):
            return full_cmd
    return ""


OPEN_FILE_COMMAND = get_open_file_command()


def setup_logger(
    name: str,
    level: int = logging.DEBUG,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Set up a logger with specified logging level and handlers.

    Args:
        name (str): The name of the logger.
        level (int): The logging level (e.g., logging.DEBUG, logging.INFO).
        log_to_file (bool): Whether to log messages to a file.
        log_to_console (bool): Whether to log messages to the console.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Define logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if log_to_file:
        # Create a file handler
        log_file_path = os.path.join(PROJECT_PATH, "resumegpt.log")
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if log_to_console:
        # Create a stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


# Initialize logger with default settings
logger = setup_logger(name=f"ResumeGPT.{__name__}", log_to_console=False)
