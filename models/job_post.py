"""
Defines the data structures and processing class for job postings.

This module includes:
- JobDescription: A Pydantic model for the structured representation of a job posting's details.
- JobPost: A class responsible for taking raw job posting text and parsing it into
           the JobDescription model using an LLM.
"""
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional, Dict, Any
from ..prompts.prompts import Prompts
from .. import config
from .. import services

Prompts.initialize() # Ensures prompt descriptions are loaded for Field descriptions


class JobDescription(BaseModel):
    """
    Pydantic model representing the structured data extracted from a job posting.

    Fields are described by entries in `Prompts.descriptions["JOB_DESCRIPTION"]`.
    """

    company: Optional[str] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["company"] # Added default=None for clarity
    )
    job_title: Optional[str] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["job_title"]
    )
    team: Optional[str] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["team"]
    )
    job_summary: Optional[str] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["job_summary"]
    )
    salary: Optional[str] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["salary"]
    )
    duties: Optional[List[str]] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["duties"]
    )
    qualifications: Optional[List[str]] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["qualifications"]
    )
    ats_keywords: Optional[List[str]] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["ats_keywords"]
    )
    is_fully_remote: Optional[bool] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["is_fully_remote"]
    )
    technical_skills: Optional[List[str]] = Field(
        default=None, description=Prompts.descriptions["JOB_DESCRIPTION"]["technical_skills"]
    )
    non_technical_skills: Optional[List[str]] = Field(
        default=None,
        description=Prompts.descriptions["JOB_DESCRIPTION"]["non_technical_skills"],
    )


class JobPost:
    """
    Represents a job posting and provides functionality to parse its content.

    This class takes raw job posting text, uses a Language Model (LLM)
    to extract structured information, and stores it as a `JobDescription` object.
    """
    def __init__(self, posting: str):
        """
        Initializes the JobPost instance with the raw job posting text.

        Args:
            posting (str): The raw text content of the job posting.
        """
        self.posting: str = posting
        self.extractor_llm = services.langchain_helpers.create_llm(
            chat_model=config.CHAT_MODEL, # Type of chat model to use
            model_name=config.MODEL_NAME, # Specific model name
            temperature=config.TEMPERATURE, # LLM temperature for controlled randomness
            cache=True, # Enable caching for LLM responses
        )
        self.parsed_job: Optional[Dict[str, Any]] = None # Will store the parsed job data

    def parse_job_post(self, **chain_kwargs) -> Optional[Dict[str, Any]]:
        """
        Parses the raw job posting text using an LLM to extract structured data.

        The method invokes an LLM chain (configured with `self.extractor_llm`)
        that is expected to return data structured according to the `JobDescription`
        Pydantic model. The result is stored in `self.parsed_job` and also returned.

        Args:
            **chain_kwargs: Additional keyword arguments that might be passed to the
                            LLM chain invocation (though not typically used here).

        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the parsed job description
                                      if successful, otherwise None if parsing fails or
                                      the LLM returns unexpected data.

        Raises:
            # This method might raise exceptions from the LLM call (e.g., API errors,
            # authentication issues) if not caught by the LLM client itself.
            # Pydantic validation errors if the LLM output doesn't match JobDescription schema.
        """
        try:
            # Configure the LLM to output data structured as JobDescription
            model_with_parser = self.extractor_llm.with_structured_output(JobDescription)

            # Invoke the LLM with the job posting text
            # The .dict() call converts the Pydantic model instance to a dictionary
            llm_output = model_with_parser.invoke(self.posting)

            if isinstance(llm_output, JobDescription):
                self.parsed_job = llm_output.dict()
                config.logger.info(f"Successfully parsed job post for title: {self.parsed_job.get('job_title', 'N/A')}")
            else:
                config.logger.warning(f"LLM output was not a JobDescription instance. Type: {type(llm_output)}")
                self.parsed_job = None # Ensure it's None if output is not as expected

        except Exception as e:
            config.logger.error(f"Failed to parse job posting: {e}", exc_info=True)
            self.parsed_job = None # Ensure parsed_job is None on error
            # Depending on desired error handling, could re-raise or return None explicitly
            # For now, it will return self.parsed_job which is None

        return self.parsed_job
