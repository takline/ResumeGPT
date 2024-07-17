import unittest
from ..pdf_generation.resume_pdf_generator import ResumePDFGenerator
from ..config import config
from ..utils import utils
import os


class TestResumePDFGenerator(unittest.TestCase):
    def setUp(self):
        self.pdf_generator = ResumePDFGenerator()

    def test_generate_resume(self):
        data = utils.read_yaml(filename=config.DEFAULT_RESUME_PATH)
        file_path = os.path.join(config.PROJECT_PATH, "tests/test_data/")
        self.pdf_generator.generate_resume(job_data_location=file_path, data=data)
        self.assertTrue(os.path.exists(file_path))


if __name__ == "__main__":
    unittest.main()
