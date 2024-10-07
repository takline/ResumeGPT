from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import yaml
from .. import config


class Prompts:
    """
    A class to load and manage prompt templates and extractor descriptions from a YAML configuration file.
    """

    lookup = None
    descriptions = None

    @classmethod
    def initialize(cls):
        """
        Initialize the Prompts class by loading the YAML files and setting up the lookup dictionary.
        """
        cls.lookup = cls._load_prompts(config.PROMPTS_YAML)
        cls.descriptions = cls._load_descriptions(config.DESCRIPTIONS_YAML)

    @staticmethod
    def _load_prompts(yaml_path: str) -> dict:
        """
        Load prompts from a YAML file and organize them into a lookup dictionary.

        :param yaml_path: Path to the YAML file containing prompt configurations.
        :return: A dictionary with prompt types as keys and lists of message templates as values.
        """
        with open(yaml_path, "r") as file:
            prompts_data = yaml.safe_load(file)

        lookup = {}
        for prompt_type, sub_data in prompts_data.items():
            sub_lookup = [
                SystemMessage(content=sub_data["system_message"]),
                HumanMessagePromptTemplate.from_template(
                    sub_data["job_posting_template"]
                ),
                HumanMessagePromptTemplate.from_template(
                    sub_data.get("resume_template", "")
                ),
                HumanMessage(content=sub_data["instruction_message"]),
                HumanMessage(content=sub_data["criteria_message"]),
                HumanMessage(content=sub_data["steps_message"]),
            ]
            lookup[prompt_type] = sub_lookup

        return lookup

    @staticmethod
    def _load_descriptions(yaml_path: str) -> dict:
        """
        Load descriptions from a YAML file.

        :param yaml_path: Path to the YAML file containing descriptions.
        :return: A dictionary with descriptions.
        """
        with open(yaml_path, "r") as file:
            descriptions_data = yaml.safe_load(file)
        return descriptions_data
