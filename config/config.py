import logging
import os
import configparser
from langchain_openai import ChatOpenAI

# Initialize logger
logger = logging.getLogger(__name__)

# Define project paths
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_PATH, "data")
RESOURCES_PATH = os.path.join(PROJECT_PATH, "resources")
PROMPTS_PATH = os.path.join(PROJECT_PATH, "prompts")
CONFIG_PATH = os.path.join(PROJECT_PATH, "config")
CONFIG_INI_PATH = os.path.join(CONFIG_PATH, "config.ini")
DEFAULT_RESUME_PATH = os.path.join(DATA_PATH, "sample_resume.yaml")
PROMPTS_YAML = os.path.join(PROMPTS_PATH, "prompts.yaml")
DESCRIPTIONS_YAML = os.path.join(PROMPTS_PATH, "extractor_descriptions.yaml")
REQUESTS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}
# Define model configuration
CHAT_MODEL = ChatOpenAI
MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.3
OPEN_FILE_COMMAND = "cursor -r"
# OPEN_FILE_COMMAND = "code -r"


# Confirm presence of OpenAI API key
def ensure_openai_api_key():
    if "OPENAI_API_KEY" not in os.environ:
        logger.info(
            "OPENAI_API_KEY not found in environment. User will be prompted to enter their key."
        )
        os.environ["OPENAI_API_KEY"] = input("Enter your OpenAI API key:")


ensure_openai_api_key()


# Load configuration from config.ini
def load_config():
    parser = configparser.ConfigParser()
    parser.read(CONFIG_INI_PATH)
    return {section: dict(parser.items(section)) for section in parser.sections()}[
        "global"
    ]


CONFIG_INI = load_config()
