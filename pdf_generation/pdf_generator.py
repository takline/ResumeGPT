"""
Provides a simplified interface for PDF generation.

This module defines the `PDFGenerator` class, which acts as a facade or wrapper
around more complex PDF generation engines (like `ReportLabResumePDFGenerator`).
Its main purpose is to offer a straightforward way to create a PDF from resume data
and handle common tasks like auto-opening the generated file.
"""
import os
import subprocess
import logging
from typing import Optional, Dict, Any

from .. import config # For OPEN_FILE_COMMAND
from .. import utils # If any utils are needed, though likely not for this version
from .resume_pdf_generator import ResumePDFGenerator as ReportLabResumePDFGenerator # Alias to avoid confusion

class PDFGenerator:
    """
    A class to orchestrate PDF generation for resumes.
    It acts as a simpler interface, potentially using other specialized PDF generator classes internally.
    """

    def __init__(self):
        """
        Initialize the PDFGenerator.
        Currently, no specific initialization is required.
        """
        pass

    def create_pdf(
        self,
        resume_data: Dict[str, Any],
        job_data_location: str, # Base directory for saving the PDF (e.g., .../CoolCompany_SoftwareEngineer/)
        auto_open: bool = True
    ) -> Optional[str]:
        """
        Creates a PDF version of the resume using the provided data.

        The actual PDF generation is delegated to ReportLabResumePDFGenerator.
        This method handles the instantiation of the generator and the auto-opening of the PDF.

        Args:
            resume_data (Dict[str, Any]): The resume data dictionary, structured as expected by
                                          ReportLabResumePDFGenerator.
            job_data_location (str): The directory path specific to the job, where the PDF
                                     (and its related YAML) are stored. The PDF will be saved
                                     within this directory, typically named based on the resume content.
            auto_open (bool): If True, attempts to automatically open the generated PDF using
                              the system's default application. Defaults to True.

        Returns:
            Optional[str]: The absolute file path to the generated PDF if successful.
                           Returns None if PDF creation fails due to missing data, IOErrors,
                           or errors during PDF generation or opening.
        """
        if not isinstance(resume_data, dict) or not resume_data:
            logging.error("Invalid or empty resume_data provided for PDF generation.")
            return None

        if not job_data_location or not os.path.isdir(job_data_location):
            logging.error(f"Job data location '{job_data_location}' is invalid or not a directory. Cannot save PDF.")
            return None

        try:
            # Instantiate the ReportLab-based generator
            reportlab_generator = ReportLabResumePDFGenerator()

            # The generate_resume method of ReportLabResumePDFGenerator is expected to:
            # 1. Construct the PDF file name (e.g., using 'name' from resume_data['basic']).
            # 2. Save the PDF into the job_data_location directory.
            # 3. Return the full path to the generated PDF.
            pdf_filepath = reportlab_generator.generate_resume(
                job_data_location=job_data_location,
                data=resume_data
            )

            if not pdf_filepath or not os.path.exists(pdf_filepath):
                logging.error(f"PDF generation by ReportLabResumePDFGenerator failed or did not return a valid file path for data in {job_data_location}.")
                return None

            logging.info(f"PDF generated successfully: {pdf_filepath}")

            if auto_open:
                logging.info(f"Attempting to automatically open PDF: {pdf_filepath}")
                try:
                    open_command_parts = config.OPEN_FILE_COMMAND.split() if isinstance(config.OPEN_FILE_COMMAND, str) else config.OPEN_FILE_COMMAND
                    subprocess.run(open_command_parts + [pdf_filepath], check=True)
                except FileNotFoundError: # For OPEN_FILE_COMMAND itself
                    logging.error(f"Error opening PDF: The command '{config.OPEN_FILE_COMMAND}' was not found on the system.")
                except subprocess.CalledProcessError as e: # For errors from the command
                    logging.error(f"Command to open PDF '{pdf_filepath}' failed: {e}", exc_info=True)
                except Exception as e: # Other unexpected errors
                    logging.error(f"An unexpected error occurred while trying to open PDF '{pdf_filepath}': {e}", exc_info=True)

            return pdf_filepath

        except Exception as e: # Catch-all for unexpected errors during ReportLabResumePDFGenerator instantiation or its methods
            logging.error(f"An unexpected error occurred during the PDF creation process for job data at '{job_data_location}': {e}", exc_info=True)
            return None

# Example Usage (for testing or direct use, not part of ResumeImprover integration):
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # This example assumes:
    # 1. Your project root is in PYTHONPATH.
    # 2. 'config.py' exists at the root and defines OPEN_FILE_COMMAND.
    # 3. 'pdf_generation/resume_pdf_generator.py' and 'pdf_generation/resume_pdf_styles.py' exist.
    # 4. You have a sample resume YAML file.

    # Create a dummy config and utils if they don't exist for standalone run
    if not hasattr(config, 'OPEN_FILE_COMMAND'):
        config.OPEN_FILE_COMMAND = "xdg-open" # Example for Linux, adjust for your OS (e.g., "open" for macOS, "start" for Windows)

    sample_resume_data = {
        "basic": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "123-456-7890",
            "address": "123 Main St, Anytown, USA",
            "websites": ["github.com/johndoe", "linkedin.com/in/johndoe"]
        },
        "objective": "To obtain a challenging position in software development.",
        "experiences": [
            {
                "company": "Tech Solutions Inc.",
                "location": "Anytown, USA",
                "skip_name": False,
                "titles": [{"name": "Software Engineer", "startdate": "Jan 2020", "enddate": "Present"}],
                "highlights": ["Developed cool stuff.", "Fixed many bugs."]
            }
        ],
        "projects": [
            {
                "name": "Personal Website",
                "date": "2023",
                "link": "http://johndoe.dev",
                "show_link": True,
                "hyperlink": True,
                "highlights": ["Built with Python and Flask.", "Deployed on Heroku."]
            }
        ],
        "education": [
            {"school": "State University", "degrees": [{"names": ["B.S. in Computer Science"]}]}
        ],
        "skills": [
            {"category": "Programming Languages", "skills": ["Python", "JavaScript", "Java"]},
            {"category": "Frameworks", "skills": ["Flask", "React", "Spring"]}
        ],
        "debug": False
    }

    # Create a temporary directory for the output
    current_dir = os.path.dirname(os.path.abspath(__file__))
    temp_job_data_location = os.path.join(current_dir, "temp_pdf_output", "TestJob_JohnDoe")
    os.makedirs(temp_job_data_location, exist_ok=True)

    print(f"Temporary job data location: {temp_job_data_location}")

    # Test the PDFGenerator
    generator = PDFGenerator()
    pdf_file = generator.create_pdf(
        resume_data=sample_resume_data,
        job_data_location=temp_job_data_location,
        auto_open=False # Set to True to test auto-opening
    )

    if pdf_file:
        print(f"PDF successfully generated at: {pdf_file}")
        # To verify, you would manually open the PDF from the path above.
    else:
        print("PDF generation failed.")

    # Clean up the temporary directory (optional)
    # import shutil
    # shutil.rmtree(os.path.join(current_dir, "temp_pdf_output"))
    # print("Cleaned up temporary output directory.")
