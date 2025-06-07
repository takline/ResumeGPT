import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil

# Assuming config and utils might be needed by the module itself, or for test data setup
from .. import config
from .. import utils

# Class to be tested
from ..pdf_generation.pdf_generator import PDFGenerator
# The actual ReportLab generator that PDFGenerator wraps
from ..pdf_generation.resume_pdf_generator import ResumePDFGenerator as ReportLabResumePDFGenerator


class TestExistingResumePDFGenerator(unittest.TestCase): # Renamed to avoid name clash
    def setUp(self):
        # This tests the original ReportLabResumePDFGenerator
        self.pdf_generator = ReportLabResumePDFGenerator()
        self.test_dir = tempfile.mkdtemp()

        # Mock config attributes that ReportLabResumePDFGenerator might use internally if any
        # For example, if FONT_PATHS or generate_doc_template relies on config
        self.mock_config_patcher = patch.multiple(
            config,
            PROJECT_PATH=self.test_dir # Assuming this might be used for resolving paths
        )
        self.mock_config_patcher.start()

        self.sample_resume_data = {
            "basic": {"name": "John Doe", "email": "j@d.com", "phone": "123", "address": "addr", "websites": []},
            "objective": "Test objective", "experiences": [], "projects": [],
            "education": [], "skills": [], "debug": False
        }
        # Create a dummy default resume file if needed by tests, or ensure data is passed directly
        self.default_resume_path = os.path.join(self.test_dir, "default_resume.yaml")
        utils.write_yaml(self.sample_resume_data, self.default_resume_path)


    def tearDown(self):
        shutil.rmtree(self.test_dir)
        self.mock_config_patcher.stop()

    def test_generate_resume_original_generator(self):
        """Test the original ReportLabResumePDFGenerator's generate_resume method directly."""
        # This test assumes ReportLabResumePDFGenerator.generate_resume saves a file
        # and returns its path.
        job_data_loc = os.path.join(self.test_dir, "TestJob")
        os.makedirs(job_data_loc, exist_ok=True)

        # The generate_resume method in ReportLabResumePDFGenerator creates a filename like "John_Doe_Resume.pdf"
        # inside job_data_loc.
        expected_pdf_filename = "John_Doe_Resume.pdf" # Based on sample_resume_data name
        expected_pdf_path = os.path.join(job_data_loc, expected_pdf_filename)

        # Patch resume_pdf_styles.generate_doc_template if it has complex dependencies
        with patch('pdf_generation.resume_pdf_styles.generate_doc_template') as mock_gen_doc_template:
            # Configure the mock to return a mock doc and the expected PDF path
            mock_doc = MagicMock()
            mock_gen_doc_template.return_value = (mock_doc, expected_pdf_path)

            generated_path = self.pdf_generator.generate_resume(
                job_data_location=job_data_loc,
                data=self.sample_resume_data
            )

            self.assertEqual(generated_path, expected_pdf_path)
            # Check that build was called on the mock_doc
            mock_doc.build.assert_called_once()
            # In a real scenario, you might check if the file os.path.exists(generated_path)
            # but since we mocked generate_doc_template which creates the file, this is enough.


class TestPDFGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.job_data_location = os.path.join(self.test_dir, "TestJob_TestCandidate")
        os.makedirs(self.job_data_location, exist_ok=True)

        self.resume_data = {
            "basic": {"name": "Test Candidate", "email": "test@example.com", "phone": "123-456-7890", "address": "123 Test St", "websites":[]},
            "objective": "A test objective.",
            "experiences": [], "projects": [], "education": [], "skills": []
        }
        self.pdf_generator_instance = PDFGenerator()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('pdf_generation.pdf_generator.ReportLabResumePDFGenerator') # Mock the class being instantiated
    @patch('pdf_generation.pdf_generator.subprocess.run')
    @patch('pdf_generation.pdf_generator.os.path.exists', return_value=True) # Assume PDF exists after generation
    def test_create_pdf_success_auto_open_true(self, mock_os_path_exists, mock_subprocess_run, MockReportLabGenerator):
        """Test successful PDF creation with auto_open=True."""
        mock_inner_generator_instance = MockReportLabGenerator.return_value
        expected_pdf_path = os.path.join(self.job_data_location, "Test_Candidate_Resume.pdf")
        mock_inner_generator_instance.generate_resume.return_value = expected_pdf_path

        # Mock config.OPEN_FILE_COMMAND
        with patch('pdf_generation.pdf_generator.config.OPEN_FILE_COMMAND', "test_open_cmd"):
            returned_path = self.pdf_generator_instance.create_pdf(
                resume_data=self.resume_data,
                job_data_location=self.job_data_location,
                auto_open=True
            )

        self.assertEqual(returned_path, expected_pdf_path)
        MockReportLabGenerator.assert_called_once() # Check ReportLabResumePDFGenerator was instantiated
        mock_inner_generator_instance.generate_resume.assert_called_once_with(
            job_data_location=self.job_data_location,
            data=self.resume_data
        )
        mock_os_path_exists.assert_called_with(expected_pdf_path)
        mock_subprocess_run.assert_called_once_with(["test_open_cmd", expected_pdf_path], check=True)

    @patch('pdf_generation.pdf_generator.ReportLabResumePDFGenerator')
    @patch('pdf_generation.pdf_generator.subprocess.run')
    @patch('pdf_generation.pdf_generator.os.path.exists', return_value=True)
    def test_create_pdf_success_auto_open_false(self, mock_os_path_exists, mock_subprocess_run, MockReportLabGenerator):
        """Test successful PDF creation with auto_open=False."""
        mock_inner_generator_instance = MockReportLabGenerator.return_value
        expected_pdf_path = os.path.join(self.job_data_location, "Test_Candidate_Resume.pdf")
        mock_inner_generator_instance.generate_resume.return_value = expected_pdf_path

        returned_path = self.pdf_generator_instance.create_pdf(
            resume_data=self.resume_data,
            job_data_location=self.job_data_location,
            auto_open=False
        )

        self.assertEqual(returned_path, expected_pdf_path)
        mock_inner_generator_instance.generate_resume.assert_called_once()
        mock_os_path_exists.assert_called_with(expected_pdf_path)
        mock_subprocess_run.assert_not_called()

    @patch('pdf_generation.pdf_generator.ReportLabResumePDFGenerator')
    def test_create_pdf_generation_fails_returns_none(self, MockReportLabGenerator):
        """Test when ReportLabResumePDFGenerator.generate_resume returns None."""
        mock_inner_generator_instance = MockReportLabGenerator.return_value
        mock_inner_generator_instance.generate_resume.return_value = None # Simulate failure

        returned_path = self.pdf_generator_instance.create_pdf(
            resume_data=self.resume_data,
            job_data_location=self.job_data_location
        )
        self.assertIsNone(returned_path)

    @patch('pdf_generation.pdf_generator.ReportLabResumePDFGenerator')
    @patch('pdf_generation.pdf_generator.os.path.exists', return_value=False) # Simulate PDF not existing after call
    def test_create_pdf_file_not_exists_after_generation(self, mock_os_path_exists, MockReportLabGenerator):
        """Test when PDF file does not exist after generation call."""
        mock_inner_generator_instance = MockReportLabGenerator.return_value
        # It returns a path, but os.path.exists will say it's not there
        mock_inner_generator_instance.generate_resume.return_value = "/fake/path.pdf"

        returned_path = self.pdf_generator_instance.create_pdf(
            resume_data=self.resume_data,
            job_data_location=self.job_data_location
        )
        self.assertIsNone(returned_path)

    def test_create_pdf_invalid_resume_data(self):
        """Test with invalid resume_data (e.g., empty dict or None)."""
        returned_path_empty = self.pdf_generator_instance.create_pdf(
            resume_data={},
            job_data_location=self.job_data_location
        )
        self.assertIsNone(returned_path_empty)

        returned_path_none = self.pdf_generator_instance.create_pdf(
            resume_data=None,
            job_data_location=self.job_data_location
        )
        self.assertIsNone(returned_path_none)

    def test_create_pdf_invalid_job_data_location(self):
        """Test with invalid job_data_location."""
        returned_path = self.pdf_generator_instance.create_pdf(
            resume_data=self.resume_data,
            job_data_location="/non/existent/path_for_sure" # Does not exist and is not a dir
        )
        self.assertIsNone(returned_path)

        # Test with a file path instead of a directory
        file_path_loc = os.path.join(self.test_dir, "a_file.txt")
        with open(file_path_loc, "w") as f:
            f.write("hello")
        returned_path_file = self.pdf_generator_instance.create_pdf(
            resume_data=self.resume_data,
            job_data_location=file_path_loc
        )
        self.assertIsNone(returned_path_file)


if __name__ == "__main__":
    unittest.main()
