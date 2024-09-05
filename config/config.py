import logging
import os
import configparser
from langchain_openai import ChatOpenAI

# Initialize logger
logger = logging.getLogger(__name__)

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
OPEN_FILE_COMMAND = "cursor -r"
#OPEN_FILE_COMMAND = "code -r"
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

