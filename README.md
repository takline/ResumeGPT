<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="images/ResumeGPT.png"/>
    <source media="(prefers-color-scheme: light)" srcset="images/ResumeGPT-light.png"/>
    <img width="400" src="images/ResumeGPT.png"/>
 <br />
</h1>

<div align="center">

<p align="center">
  <a href="#installation">
    <b>Install</b>
  </a>
     · 
  <a href="#usage">
    <b>Usage</b>
  </a>
     · 
  <a href="#features">
    <b>Features</b>
  </a>
      · 
  <a href="#discussions">
    <b>Discussions</b>
  </a>
     · 
  <a href="#contributors">
    <b>Contributors</b>
  </a>

</p>

<br>


</div>

<br>

<h3 align="center">Tailor your resume to match any job posting effortlessly with ResumeGPT.
</h3>

<br/>
ResumeGPT allows you to simply provide your resume and a job posting link, and it will produce a formatted ATS friendly PDF resume that is optimized and personalize your resume to align with the specific requirements and keywords of the job. 

## Features
- Extracts relevant skills, qualifications, and keywords from a job posting.
- Tailors your curent resume to match job requirements.
- Generates professional ATS friendly PDF resumes.
- Allows for user verification and customization before finalizing the resume.

## Installation
To install ResumeGPT, clone the repository and install the required dependencies:

```bash
git clone https://github.com/takline/ResumeGPT.git
cd ResumeGPT
pip install -r requirements.txt
```

## Usage

 - Add your resume to ./data/sample_resume.yaml (make sure ResumeGPT.config.YOUR_RESUME_NAME is set to your resume filename in the `.data/` folder)
 - Update `./config/config.ini` with your name and info that will be included in your resume
 - Provide ResumeGPT with the link to a job posting and it will tailot your resume to the job:

```python
url = "https://[link to your job posting]
resume_improver = ResumeGPT.services.ResumeImprover(url)
resume_improver.create_draft_tailored_resume()
```

ResumeGPT then creates a new resume YAML file in a new folder named after the job posting with a YAML key/value: `editing: true`. ResumeGPT will wait for you to update this key to verify the resume updates and allow them to make their own updates until users set `editing=false`. Then ResumeGPT will create a PDF version of their resume. Below is an example PDFs generated by ResumeGPT:

<p align="center">
  <img src="images/example_resume_output.png" alt="Resume Example" width="400"/>
</p>

## Discussions
Feel free to give feedback, ask questions, report a bug, or suggest improvements:

[Discussions](https://github.com/takline/ResumeGPT/discussions)
[Issues](https://github.com/takline/ResumeGPT/issues)

##  Contributors
⭐️  Please star, fork, explore, and contribute to ResumeGPT. There's a lot of work room for improvement so any contributions are appreciated.
