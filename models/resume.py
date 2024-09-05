from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from ..prompts.prompts import Prompts

Prompts.initialize()

class ResumeSectionHighlight(BaseModel):
    """Pydantic class that defines each highlight to be returned by the LLM."""

    highlight: str = Field(
        ..., description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHT"]["highlight"]
    )
    relevance: int = Field(
        ...,
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHT"]["relevance"],
        enum=[1, 2, 3, 4, 5],
    )

class ResumeSectionHighlighterOutput(BaseModel):
    """Pydantic class that defines a list of highlights to be returned by the LLM."""

    plan: List[str] = Field(
        ...,
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHTER_OUTPUT"]["plan"],
    )
    additional_steps: List[str] = Field(
        ...,
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHTER_OUTPUT"]["additional_steps"],
    )
    work: List[str] = Field(
        ...,
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHTER_OUTPUT"]["work"],
    )
    final_answer: List[ResumeSectionHighlight] = Field(
        ...,
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHTER_OUTPUT"]["final_answer"],
    )

class ResumeSkills(BaseModel):
    """Pydantic class that defines a list of skills to be returned by the LLM."""

    technical_skills: List[str] = Field(
        ..., description=Prompts.descriptions["RESUME_SKILLS"]["technical_skills"]
    )
    non_technical_skills: List[str] = Field(
        ..., description=Prompts.descriptions["RESUME_SKILLS"]["non_technical_skills"]
    )

class ResumeSkillsMatcherOutput(BaseModel):
    """Pydantic class that defines a list of skills to be returned by the LLM."""

    plan: List[str] = Field(
        ..., description=Prompts.descriptions["RESUME_SKILLS_MATCHER_OUTPUT"]["plan"]
    )
    additional_steps: List[str] = Field(
        ...,
        description=Prompts.descriptions["RESUME_SKILLS_MATCHER_OUTPUT"]["additional_steps"],
    )
    work: List[str] = Field(
        ..., description=Prompts.descriptions["RESUME_SKILLS_MATCHER_OUTPUT"]["work"]
    )
    final_answer: ResumeSkills = Field(
        ...,
        description=Prompts.descriptions["RESUME_SKILLS_MATCHER_OUTPUT"]["final_answer"],
    )

class ResumeSummarizerOutput(BaseModel):
    """Pydantic class that defines a list of skills to be returned by the LLM."""

    plan: List[str] = Field(
        ..., description=Prompts.descriptions["RESUME_OBJECTIVE_OUTPUT"]["plan"]
    )
    additional_steps: List[str] = Field(
        ...,
        description=Prompts.descriptions["RESUME_OBJECTIVE_OUTPUT"]["additional_steps"],
    )
    work: List[str] = Field(
        ..., description=Prompts.descriptions["RESUME_OBJECTIVE_OUTPUT"]["work"]
    )
    final_answer: str = Field(
        ...,
        description=Prompts.descriptions["RESUME_OBJECTIVE_OUTPUT"]["final_answer"],
    )

class ResumeImprovements(BaseModel):
    """Pydantic class that defines a list of improvements to be returned by the LLM."""

    section: str = Field(
        ...,
        enum=[
            "objective",
            "education",
            "experiences",
            "projects",
            "skills",
            "spelling and grammar",
            "other",
        ],
    )
    improvements: List[str] = Field(
        ..., description=Prompts.descriptions["RESUME_IMPROVEMENTS"]["improvements"]
    )

class ResumeImproverOutput(BaseModel):
    """Pydantic class that defines a list of improvements to be returned by the LLM."""

    plan: List[str] = Field(
        ..., description=Prompts.descriptions["RESUME_IMPROVER_OUTPUT"]["plan"]
    )
    additional_steps: List[str] = Field(
        ...,
        description=Prompts.descriptions["RESUME_IMPROVER_OUTPUT"]["additional_steps"],
    )
    work: List[str] = Field(
        ..., description=Prompts.descriptions["RESUME_IMPROVER_OUTPUT"]["work"]
    )
    final_answer: List[ResumeImprovements] = Field(
        ..., description=Prompts.descriptions["RESUME_IMPROVER_OUTPUT"]["final_answer"]
    )