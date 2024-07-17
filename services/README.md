# Services

The `services` folder contains the core functionality of the ResumeGPT project. These services are responsible for parsing job postings, improving resumes, generating PDF outputs, and running tasks in the background. This document provides an overview of each service, how to use them, and examples to get you started.

## Overview

The `services` folder includes the following modules:

- `resume_improver.py`: Contains the `ResumeImprover` class, which is responsible for improving resumes based on job postings.
- `langchain_helpers.py`: Provides helper functions for interacting with the LangChain library.
- `pdf_generation`: Contains the `ResumePDFGenerator` class for generating PDF resumes.
- `background_runner.py`: Contains the `BackgroundRunner` class, which allows for running tasks in the background, such as concurrently improving multiple resumes.
