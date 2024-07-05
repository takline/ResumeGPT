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

Users provide ResumeGPT with their resume (`./data/sample_resume.yaml`), their personal information (`./config/config.ini`), and a URL of a job posting. Once they do that, they use the sample code below to have ResumeGPT create a tailored resume:

```python
url = "https://careers.mastercard.com/us/en/job/MASRUSR222161EXTERNALENUS/Director-Product-Management-Advanced-Analytics-AI-Solutions?utm_medium=phenom-feeds&source=LINKEDIN&utm_source=linkedin"
resume_improver = ResumeGPT.services.ResumeImprover(url)
resume_improver.create_draft_tailored_resume()
```

ResumeGPT then creates a new resume YAML file in a new folder named after the job posting with a YAML key/value: `editing: true`. ResumeGPT will wait for users to verify the resume updates and allow them to make their own updates until users set `editing=false`. Then ResumeGPT will create a PDF version of their resume.
