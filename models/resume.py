"""
Defines Pydantic models for structuring resume-related data, particularly for
LLM outputs when analyzing, matching, or improving resumes.

These models are used to ensure that the responses from the Language Models (LLMs)
are in a predictable, parsable format. Descriptions for many fields are dynamically
loaded from `Prompts.descriptions` to centralize descriptive texts.
"""
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional # Optional might be useful for some plan/work fields if not always present
from ..prompts.prompts import Prompts

Prompts.initialize() # Ensures prompt descriptions are loaded

class ResumeSectionHighlight(BaseModel):
    """
    Represents a single highlighted point or statement from a resume section,
    along with its relevance score as determined by an LLM.
    """

    highlight: str = Field(
        ...,
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHT"]["highlight"]
    )
    relevance: int = Field(
        ..., # Indicates this field is required
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHT"]["relevance"],
        ge=1,  # Ensure relevance is at least 1
        le=5,  # Ensure relevance is at most 5
        # enum=[1, 2, 3, 4, 5], # ge/le is more flexible if Prompts.descriptions changes enum
    )

class ResumeSectionHighlighterOutput(BaseModel):
    """
    Defines the structured output when an LLM processes a resume section for highlights.
    Includes planning steps and the final list of highlights.
    """

    plan: List[str] = Field(
        default_factory=list, # Use default_factory for mutable types
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHTER_OUTPUT"]["plan"],
    )
    additional_steps: List[str] = Field(
        default_factory=list,
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHTER_OUTPUT"]["additional_steps"],
    )
    work: List[str] = Field(
        default_factory=list,
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHTER_OUTPUT"]["work"],
    )
    final_answer: List[ResumeSectionHighlight] = Field(
        ..., # Required field
        description=Prompts.descriptions["RESUME_SECTION_HIGHLIGHTER_OUTPUT"]["final_answer"],
    )

class ResumeSkills(BaseModel):
    """
    Structured representation of technical and non-technical skills extracted or
    identified in a resume or job posting.
    """

    technical_skills: List[str] = Field(
        default_factory=list, description=Prompts.descriptions["RESUME_SKILLS"]["technical_skills"]
    )
    non_technical_skills: List[str] = Field(
        default_factory=list, description=Prompts.descriptions["RESUME_SKILLS"]["non_technical_skills"]
    )

class ResumeSkillsMatcherOutput(BaseModel):
    """
    Defines the structured output when an LLM matches skills from a resume against a job description.
    Includes planning steps and the final categorized skills.
    """

    plan: List[str] = Field(
        default_factory=list, description=Prompts.descriptions["RESUME_SKILLS_MATCHER_OUTPUT"]["plan"]
    )
    additional_steps: List[str] = Field(
        default_factory=list,
        description=Prompts.descriptions["RESUME_SKILLS_MATCHER_OUTPUT"]["additional_steps"],
    )
    work: List[str] = Field(
        default_factory=list, description=Prompts.descriptions["RESUME_SKILLS_MATCHER_OUTPUT"]["work"]
    )
    final_answer: ResumeSkills = Field( # The final answer is a ResumeSkills object
        ..., # Required field
        description=Prompts.descriptions["RESUME_SKILLS_MATCHER_OUTPUT"]["final_answer"],
    )

class ResumeSummarizerOutput(BaseModel):
    """
    Defines the structured output for LLM tasks that generate a summary, like an objective statement.
    Includes planning steps and the final summary string.
    """

    plan: List[str] = Field(
        default_factory=list, description=Prompts.descriptions["RESUME_OBJECTIVE_OUTPUT"]["plan"]
    )
    additional_steps: List[str] = Field(
        default_factory=list,
        description=Prompts.descriptions["RESUME_OBJECTIVE_OUTPUT"]["additional_steps"],
    )
    work: List[str] = Field(
        default_factory=list, description=Prompts.descriptions["RESUME_OBJECTIVE_OUTPUT"]["work"]
    )
    final_answer: str = Field( # The final summary (e.g., objective)
        ..., # Required field
        description=Prompts.descriptions["RESUME_OBJECTIVE_OUTPUT"]["final_answer"],
    )

class ResumeImprovements(BaseModel):
    """
    Represents a categorized list of suggested improvements for a resume section.
    """

    section: str = Field(
        ..., # Required field
        description="The resume section to which these improvements apply.",
        # Example enum, actual values might be dynamically determined or broader.
        # Consider if Prompts.descriptions should provide this enum list.
        enum=[
            "objective",
            "education",
            "experiences",
            "projects",
            "skills",
            "formatting",
            "spelling_and_grammar", # Use underscores for enum values if they map to code/keys
            "overall_impact",
            "other",
        ],
    )
    improvements: List[str] = Field(
        ..., # Required field
        description=Prompts.descriptions["RESUME_IMPROVEMENTS"]["improvements"]
    )

class ResumeImproverOutput(BaseModel):
    """
    Defines the structured output when an LLM suggests overall improvements for a resume.
    Includes planning steps and a list of categorized improvement suggestions.
    """

    plan: List[str] = Field(
        default_factory=list, description=Prompts.descriptions["RESUME_IMPROVER_OUTPUT"]["plan"]
    )
    additional_steps: List[str] = Field(
        default_factory=list,
        description=Prompts.descriptions["RESUME_IMPROVER_OUTPUT"]["additional_steps"],
    )
    work: List[str] = Field(
        default_factory=list, description=Prompts.descriptions["RESUME_IMPROVER_OUTPUT"]["work"]
    )
    final_answer: List[ResumeImprovements] = Field( # A list of ResumeImprovements objects
        ..., # Required field
        description=Prompts.descriptions["RESUME_IMPROVER_OUTPUT"]["final_answer"]
    )