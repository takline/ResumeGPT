from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional
from ..prompts.prompts import Prompts
from .. import config
from .. import services

Prompts.initialize()


class JobDescription(BaseModel):
    """Description of a job posting."""

    company: Optional[str] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["company"]
    )
    job_title: Optional[str] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["job_title"]
    )
    team: Optional[str] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["team"]
    )
    job_summary: Optional[str] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["job_summary"]
    )
    salary: Optional[str] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["salary"]
    )
    duties: Optional[List[str]] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["duties"]
    )
    qualifications: Optional[List[str]] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["qualifications"]
    )
    ats_keywords: Optional[List[str]] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["ats_keywords"]
    )
    is_fully_remote: Optional[bool] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["is_fully_remote"]
    )
    technical_skills: Optional[List[str]] = Field(
        None, description=Prompts.descriptions["JOB_DESCRIPTION"]["technical_skills"]
    )
    non_technical_skills: Optional[List[str]] = Field(
        None,
        description=Prompts.descriptions["JOB_DESCRIPTION"]["non_technical_skills"],
    )


class JobPost:
    def __init__(self, posting: str):
        """Initialize JobPost with the job posting string."""
        self.posting = posting
        self.extractor_llm = services.langchain_helpers.create_llm(
            chat_model=config.CHAT_MODEL,
            model_name=config.MODEL_NAME,
            temperature=config.TEMPERATURE,
            cache=True,
        )
        self.parsed_job = None

    def parse_job_post(self, **chain_kwargs) -> dict:
        """Parse the job posting to extract job description and skills."""
        model = self.extractor_llm.with_structured_output(JobDescription)
        self.parsed_job = model.invoke(self.posting).dict()
        return self.parsed_job
