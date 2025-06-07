"""
Manages loading and accessing prompt templates and descriptions from YAML files.

This module provides a centralized way to handle prompt configurations,
making it easier to manage and update the prompts used by Language Models (LLMs)
throughout the application. It loads system messages, human message templates,
and other instructional components for constructing detailed prompts.
It also loads descriptive texts used, for example, in Pydantic model fields.
"""
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage # SystemMessage is used directly
import yaml
from .. import config


class Prompts:
    """
    A class to load and manage prompt templates and extractor descriptions from a YAML configuration file.
    """

    lookup: Optional[dict] = None  # Stores structured prompt templates, keyed by prompt type.
    descriptions: Optional[dict] = None  # Stores descriptions, often for Pydantic model fields.

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
        :return: A dictionary where keys are prompt type names (e.g., "SECTION_HIGHLIGHTER")
                 and values are lists of LangChain message objects (SystemMessage, HumanMessagePromptTemplate).
        """
        try:
            with open(yaml_path, "r", encoding="utf-8") as file: # Added encoding
                prompts_data = yaml.safe_load(file)
            if not isinstance(prompts_data, dict):
                config.logger.error(f"Prompts YAML file {yaml_path} did not load as a dictionary.")
                return {}
        except FileNotFoundError:
            config.logger.error(f"Prompts YAML file not found at {yaml_path}.")
            return {}
        except yaml.YAMLError as e:
            config.logger.error(f"Error parsing prompts YAML file {yaml_path}: {e}", exc_info=True)
            return {}
        except Exception as e:
            config.logger.error(f"Unexpected error loading prompts YAML {yaml_path}: {e}", exc_info=True)
            return {}


        loaded_prompts = {}
        for prompt_type, sub_data in prompts_data.items():
            if not isinstance(sub_data, dict):
                config.logger.warning(f"Skipping malformed prompt type '{prompt_type}' in {yaml_path}: Expected a dictionary.")
                continue

            # Ensure all required keys are present before creating messages
            required_keys = ["system_message", "job_posting_template", "instruction_message", "criteria_message", "steps_message"]
            if not all(key in sub_data for key in required_keys):
                config.logger.warning(f"Skipping prompt type '{prompt_type}' due to missing one or more required keys: {required_keys}")
                continue

            message_list = [
                SystemMessage(content=sub_data["system_message"]),
                HumanMessagePromptTemplate.from_template(sub_data["job_posting_template"]),
                # resume_template is optional, handle its absence gracefully
                HumanMessagePromptTemplate.from_template(sub_data.get("resume_template", "")),
                HumanMessage(content=sub_data["instruction_message"]),
                HumanMessage(content=sub_data["criteria_message"]),
                HumanMessage(content=sub_data["steps_message"]),
            ]
            loaded_prompts[prompt_type] = message_list

        if not loaded_prompts:
            config.logger.warning(f"No valid prompts were loaded from {yaml_path}.")

        return loaded_prompts

    @staticmethod
    def _load_descriptions(yaml_path: str) -> dict:
        """
        Load descriptions from a YAML file, typically used for Pydantic model field descriptions.

        Args:
            yaml_path (str): Path to the YAML file containing descriptions.

        Returns:
            dict: A dictionary containing the loaded descriptions. Returns an empty dict on failure.
        """
        try:
            with open(yaml_path, "r", encoding="utf-8") as file: # Added encoding
                descriptions_data = yaml.safe_load(file)
            if not isinstance(descriptions_data, dict):
                config.logger.error(f"Descriptions YAML file {yaml_path} did not load as a dictionary.")
                return {}
            return descriptions_data
        except FileNotFoundError:
            config.logger.error(f"Descriptions YAML file not found at {yaml_path}.")
            return {}
        except yaml.YAMLError as e:
            config.logger.error(f"Error parsing descriptions YAML file {yaml_path}: {e}", exc_info=True)
            return {}
        except Exception as e:
            config.logger.error(f"Unexpected error loading descriptions YAML {yaml_path}: {e}", exc_info=True)
            return {}
