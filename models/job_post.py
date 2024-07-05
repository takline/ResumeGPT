from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional
from ..prompts.prompts import Prompts
from ..services.extractor import ExtractorLLM

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

class JobSkills(BaseModel):
    """Skills from a job posting."""

    technical_skills: Optional[List[str]] = Field(
        None, description=Prompts.descriptions["JOB_SKILLS"]["technical_skills"]
    )
    non_technical_skills: Optional[List[str]] = Field(
        None, description=Prompts.descriptions["JOB_SKILLS"]["non_technical_skills"]
    )

class JobPost(ExtractorLLM):
    def __init__(self, posting: str):
        """Initialize JobPost with the job posting string."""
        super().__init__()
        self.posting = posting
        self.parsed_job = None

    def parse_job_post(self, **chain_kwargs) -> dict:
        """Parse the job posting to extract job description and skills."""
        parsed_job = self.extract_from_input(
            pydantic_object=JobDescription, input=self.posting, **chain_kwargs
        )
        job_skills = self.extract_from_input(
            pydantic_object=JobSkills, input=self.posting, **chain_kwargs
        )
        self.parsed_job = {**parsed_job, **job_skills}
        return self.parsed_job
