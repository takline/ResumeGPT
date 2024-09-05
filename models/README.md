# Models

The `./models` folder contains Pydantic models that define the structure of various data objects used throughout the ResumeGPT project. These models are essential for ensuring data consistency and validation across different components of the library.

## Job Description and Skills Models

### JobDescription
Defines the structure of a job posting.

**Fields**:
- `company` (Optional[str]): Name of the company that has the job opening.
- `job_title` (Optional[str]): Job title.
- `team` (Optional[str]): Name of the team within the company.
- `job_summary` (Optional[str]): Brief summary of the job.
- `salary` (Optional[str]): Salary amount or range.
- `duties` (Optional[List[str]]): Role, responsibilities, and duties of the job as an itemized list.
- `qualifications` (Optional[List[str]]): Qualifications, skills, and experience required for the job as an itemized list.
- `ats_keywords` (Optional[List[str]]): Keywords for Applicant Tracking Systems (ATS).
- `is_fully_remote` (Optional[bool]): Does the job have an option to work fully (100%) remotely?
- `technical_skills` (Optional[List[str]]): Itemized list of technical skills.
- `non_technical_skills` (Optional[List[str]]): Itemized list of non-technical soft skills.

## Resume Models

### ResumeSectionHighlight
Defines the structure of a highlight in a resume section.

**Fields**:
- `highlight` (str): One highlight.
- `relevance` (int): Relevance of the bullet point (1-5).

### ResumeSectionHighlighterOutput
Defines the structure of the output for the resume section highlighter.

**Fields**:
- `plan` (List[str]): Itemized plan.
- `additional_steps` (List[str]): Itemized additional steps.
- `work` (List[str]): Itemized work.
- `final_answer` (List[ResumeSectionHighlight]): Itemized final answer in the correct format.

### ResumeSkills
Defines the structure of skills in a resume.

**Fields**:
- `technical_skills` (List[str]): Itemized list of technical skills.
- `non_technical_skills` (List[str]): Itemized list of non-technical skills.

### ResumeSkillsMatcherOutput
Defines the structure of the output for the resume skills matcher.

**Fields**:
- `plan` (List[str]): Itemized plan.
- `additional_steps` (List[str]): Itemized additional steps.
- `work` (List[str]): Itemized work.
- `final_answer` (ResumeSkills): Resume skills in the correct format.

### ResumeSummarizerOutput
Defines the structure of the output for the resume summarizer.

**Fields**:
- `plan` (List[str]): Itemized plan.
- `additional_steps` (List[str]): Itemized additional steps.
- `work` (List[str]): Itemized work.
- `final_answer` (str): Final answer in the correct format.

### ResumeImprovements
Defines the structure of improvements suggested for a resume.

**Fields**:
- `section` (str): Section to improve (summary, education, experience, skills, spelling and grammar, other).
- `improvements` (List[str]): Itemized list of suggested improvements.

### ResumeImproverOutput
Defines the structure of the output for the resume improver.

**Fields**:
- `plan` (List[str]): Itemized plan.
- `additional_steps` (List[str]): Itemized additional steps.
- `work` (List[str]): Itemized work.
- `final_answer` (List[ResumeImprovements]): List of resume improvements in the correct format.

## Usage

These models are used by various services in the library to parse job postings, extract relevant information, match skills, and suggest improvements for resumes. They ensure data consistency and validation across different components of the ResumeGPT project.

By using Pydantic models, we can leverage the power of data validation and type checking, making our code more robust and less error-prone. The models also provide a clear and concise way to define the structure of our data, making it easier for developers to understand and work with the library.

We hope you find these models useful and encourage you to contribute to the project by suggesting improvements or adding new features. Happy coding!
