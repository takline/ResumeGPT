# ResumeGPT

ResumeGPT is a tool for tailoring your resume to a specific job posting. It uses Langchain to extract relevant information from job postings and tailor resumes to match the job requirements, then produces a formatted ATS friendly PDF resume.

## Features
- Extracts relevant skills and qualifications from job postings.
- Suggests improvements to resumes to match job requirements.
- Generates professional PDF resumes.
- Allows for user verification and customization before finalizing the resume.

## Installation
To install ResumeGPT, clone the repository and install the required dependencies:

```bash
git clone https://github.com/takline/ResumeGPT.git
cd ResumeGPT
pip install -r requirements.txt
```

## Usage

 - Add your resume to `./data/sample_resume.yaml`
 - Update `./config/config.ini` with your name and info
 - Provide ResumeGPT with the link to a job posting and it will tailot your resume to the job:

```python
url = "https://[link to a job posting]"
resume_improver = ResumeGPT.services.ResumeImprover(url)
resume_improver.create_draft_tailored_resume()
```

ResumeGPT then creates a new resume YAML file in a new folder named after the job posting with a YAML key/value: `editing: true`. ResumeGPT will wait for you to verify the updates + make your own updates until you set `editing=false` in the yaml file. Then ResumeGPT will create a PDF version of their resume.
