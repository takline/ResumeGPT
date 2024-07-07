import unittest
from ..pdf_generation.resume_pdf_generator import ResumePDFGenerator
from ..config import config
import os


class TestResumePDFGenerator(unittest.TestCase):
    def setUp(self):
        self.pdf_generator = ResumePDFGenerator()

    def test_generate_resume(self):
        data = {
            "education": [
                {"degree": "B.S. Economics", "university": "State University"}
            ],
            "objective": "A Product Manager with over 10 years of experience...",
            "experience": [
                {
                    "title": "Vice President",
                    "company": "Major Financial Institution",
                    "location": "Anytown, USA",
                    "duration": "2023-2024",
                    "description": ["Led the development..."],
                }
            ],
            "skills": ["Technical: Python, SQL", "Soft Skills: Leadership"],
        }
        file_path = os.path.join(PROJECT_PATH, "test/test_data/resume.pdf")
        self.pdf_generator.generate_resume(file_path, data)
        self.assertTrue(os.path.exists(file_path))


if __name__ == "__main__":
    unittest.main()
