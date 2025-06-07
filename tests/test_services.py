import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import os
import tempfile
import shutil
import json
from datetime import datetime, timedelta
import hashlib

from ..services.resume_improver import ResumeImprover, HTML_CACHE_DIR, HTML_CACHE_DURATION_SECONDS, HTML_CACHE_ENABLED
from ..services.langchain_helpers import create_llm # Assuming this is still needed for other tests
from .. import config # For other config values if ResumeImprover uses them directly
from .. import utils # For utils.read_yaml, utils.write_yaml if not mocked elsewhere

# Store original values
ORIG_HTML_CACHE_DIR = HTML_CACHE_DIR
ORIG_HTML_CACHE_ENABLED = HTML_CACHE_ENABLED
ORIG_HTML_CACHE_DURATION_SECONDS = HTML_CACHE_DURATION_SECONDS


class TestResumeImprover(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for caching and job data
        self.test_dir = tempfile.mkdtemp()

        # Override HTML_CACHE_DIR to use the temp directory
        # This requires ResumeImprover to be imported AFTER this patch or use a setter.
        # For simplicity in this environment, we'll assume direct patching of constants if possible,
        # or rely on instance-level patching if the constants are used early.
        # The best way is to make these configurable on the instance or via a global config object
        # that can be easily mocked. Given the current structure, we'll patch them globally for tests.
        # This is done in TestHTMLCaching specifically.

        self.mock_url = "http://example.com/job_posting_test"

        # Basic resume data for tests that need it
        self.sample_resume_data = {
            "basic": {"name": "Test User"},
            "objective": "Old objective",
            "skills": [{"category": "Programming", "skills": ["Python", "Java"]}],
            "experiences": [],
            "projects": []
        }

        # Mock config attributes that ResumeImprover might use (if config.py was available)
        # Since config.py is missing, these might not be used, or ResumeImprover might have defaults.
        # We'll assume config.DEFAULT_RESUME_PATH and config.DATA_PATH are used.
        self.mock_config_patcher = patch.multiple(
            config,
            DEFAULT_RESUME_PATH=os.path.join(self.test_dir, "default_resume.yaml"),
            DATA_PATH=os.path.join(self.test_dir, "job_data"),
            # MAX_RETRIES and BACKOFF_FACTOR are used in _download_job_post_html
            MAX_RETRIES=1,
            BACKOFF_FACTOR=0.1,
            REQUESTS_HEADERS={},
            REQUEST_TIMEOUT=5
        )
        self.mock_config_patcher.start()

        # Create a dummy default resume file
        utils.write_yaml(self.sample_resume_data, config.DEFAULT_RESUME_PATH)
        os.makedirs(config.DATA_PATH, exist_ok=True)

        # Initialize ResumeImprover - this will call _initialize_job_post_data
        # We need to mock dependencies of _initialize_job_post_data for most tests
        with patch.object(ResumeImprover, '_download_job_post_html', return_value=True), \
             patch.object(ResumeImprover, '_extract_text_from_html_content', return_value=None), \
             patch.object(ResumeImprover, '_parse_and_save_job_post_text', return_value=True):
            self.improver = ResumeImprover(url=self.mock_url, resume_location=config.DEFAULT_RESUME_PATH)
            # Setup initial state for the improver after init
            self.improver.job_post_html_data = "<html><body>Mock HTML</body></html>"
            self.improver.job_post_raw = "Mock HTML"
            self.improver.parsed_job = {"job_title": "Test Job", "company": "TestCo"}
            self.improver.job_data_location = os.path.join(config.DATA_PATH, "TestCo_Test_Job")
            os.makedirs(self.improver.job_data_location, exist_ok=True)


    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        self.mock_config_patcher.stop()


class TestHTMLCaching(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mock_url = "http://example.com/job_for_caching"

        # Patch constants directly on the imported module for testing
        self.patches = [
            patch('services.resume_improver.HTML_CACHE_DIR', os.path.join(self.test_dir, "html_cache")),
            patch('services.resume_improver.HTML_CACHE_ENABLED', True),
            patch('services.resume_improver.HTML_CACHE_DURATION_SECONDS', 3600) # 1 hour
        ]
        for p in self.patches:
            p.start()

        # Ensure cache directory exists for tests
        os.makedirs(os.path.join(self.test_dir, "html_cache"), exist_ok=True)

        # Minimal ResumeImprover instance for testing _download_job_post_html
        self.improver = ResumeImprover(url=self.mock_url, resume_location=MagicMock()) # Resume location not used by download

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.test_dir)

    @patch('requests.get')
    def test_download_html_cache_miss_and_save(self, mock_requests_get):
        """Test cache miss: first download, then save to cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test Job Content</body></html>"
        mock_requests_get.return_value = mock_response

        # First call - should download and save to cache
        result = self.improver._download_job_post_html()
        self.assertTrue(result)
        self.assertEqual(self.improver.job_post_html_data, mock_response.text)
        mock_requests_get.assert_called_once_with(
            self.mock_url, headers=config.REQUESTS_HEADERS, proxies=None, timeout=config.REQUEST_TIMEOUT
        )

        # Verify cache files were created
        url_hash = hashlib.md5(self.mock_url.encode('utf-8')).hexdigest()
        html_file_path = os.path.join(os.path.join(self.test_dir, "html_cache"), f"{url_hash}.html")
        meta_file_path = os.path.join(os.path.join(self.test_dir, "html_cache"), f"{url_hash}.meta.json")
        self.assertTrue(os.path.exists(html_file_path))
        self.assertTrue(os.path.exists(meta_file_path))
        with open(meta_file_path, 'r') as f:
            meta = json.load(f)
        self.assertEqual(meta["url"], self.mock_url)

    @patch('requests.get')
    def test_download_html_cache_hit(self, mock_requests_get):
        """Test cache hit: content is loaded from existing fresh cache."""
        mock_html_content = "<html><body>Cached Content</body></html>"
        url_hash = hashlib.md5(self.mock_url.encode('utf-8')).hexdigest()
        cache_base_dir = os.path.join(self.test_dir, "html_cache")
        html_file_path = os.path.join(cache_base_dir, f"{url_hash}.html")
        meta_file_path = os.path.join(cache_base_dir, f"{url_hash}.meta.json")

        # Pre-populate cache
        os.makedirs(cache_base_dir, exist_ok=True)
        with open(html_file_path, 'w') as f:
            f.write(mock_html_content)
        with open(meta_file_path, 'w') as f:
            json.dump({"url": self.mock_url, "timestamp": datetime.now().isoformat()}, f)

        result = self.improver._download_job_post_html()
        self.assertTrue(result)
        self.assertEqual(self.improver.job_post_html_data, mock_html_content)
        mock_requests_get.assert_not_called() # Should not call requests.get

    @patch('requests.get')
    def test_download_html_cache_stale(self, mock_requests_get):
        """Test stale cache: content is downloaded again."""
        mock_html_content_stale = "<html><body>Stale Cache</body></html>"
        mock_html_content_fresh = "<html><body>Freshly Downloaded</body></html>"
        url_hash = hashlib.md5(self.mock_url.encode('utf-8')).hexdigest()
        cache_base_dir = os.path.join(self.test_dir, "html_cache")
        html_file_path = os.path.join(cache_base_dir, f"{url_hash}.html")
        meta_file_path = os.path.join(cache_base_dir, f"{url_hash}.meta.json")

        # Pre-populate stale cache
        os.makedirs(cache_base_dir, exist_ok=True)
        with open(html_file_path, 'w') as f:
            f.write(mock_html_content_stale)
        stale_timestamp = (datetime.now() - timedelta(seconds=7200)).isoformat() # 2 hours > 1 hour cache
        with open(meta_file_path, 'w') as f:
            json.dump({"url": self.mock_url, "timestamp": stale_timestamp}, f)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html_content_fresh
        mock_requests_get.return_value = mock_response

        result = self.improver._download_job_post_html()
        self.assertTrue(result)
        self.assertEqual(self.improver.job_post_html_data, mock_html_content_fresh)
        mock_requests_get.assert_called_once()

    @patch('services.resume_improver.HTML_CACHE_ENABLED', False) # Patch the constant for this test
    @patch('requests.get')
    def test_download_html_cache_disabled(self, mock_requests_get):
        """Test that caching is skipped if HTML_CACHE_ENABLED is False."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Cache Disabled Content</body></html>"
        mock_requests_get.return_value = mock_response

        result = self.improver._download_job_post_html()
        self.assertTrue(result)
        self.assertEqual(self.improver.job_post_html_data, mock_response.text)
        mock_requests_get.assert_called_once()

        # Verify no cache files were created
        url_hash = hashlib.md5(self.mock_url.encode('utf-8')).hexdigest()
        html_file_path = os.path.join(os.path.join(self.test_dir, "html_cache"), f"{url_hash}.html")
        self.assertFalse(os.path.exists(html_file_path))


class TestResumeImproverCoreLogic(TestResumeImprover): # Inherit setUp/tearDown

    @patch.object(ResumeImprover, '_download_job_post_html', return_value=True)
    @patch.object(ResumeImprover, '_extract_text_from_html_content') # To be called
    @patch.object(ResumeImprover, '_parse_and_save_job_post_text', return_value=True) # Assume success
    def test_initialize_job_post_data_success(self, mock_parse_save, mock_extract, mock_download):
        """Test successful orchestration of _initialize_job_post_data."""
        # Reset relevant attributes that might have been set by setUp's ResumeImprover init
        self.improver.job_post_html_data = "Sample HTML for init test"
        self.improver.job_post_raw = None
        self.improver.parsed_job = None

        self.improver._initialize_job_post_data(job_post_url="http://newtest.com")

        mock_download.assert_called_once_with(target_url="http://newtest.com")
        mock_extract.assert_called_once() # Called after successful download
        mock_parse_save.assert_called_once() # Called after successful extraction
        self.assertEqual(self.improver.url, "http://newtest.com")

    @patch.object(ResumeImprover, '_download_job_post_html', return_value=False) # Simulate download failure
    @patch.object(ResumeImprover, '_extract_text_from_html_content')
    @patch.object(ResumeImprover, '_parse_and_save_job_post_text')
    def test_initialize_job_post_data_download_fails(self, mock_parse_save, mock_extract, mock_download):
        """Test _initialize_job_post_data when download fails."""
        self.improver._initialize_job_post_data()
        mock_download.assert_called_once()
        mock_extract.assert_not_called()
        mock_parse_save.assert_not_called()

    @patch.object(ResumeImprover, 'extract_matched_skills', return_value=[{"category":"mock", "skills":["A","B"]}])
    @patch.object(ResumeImprover, 'write_objective', return_value="Mocked Objective")
    @patch.object(ResumeImprover, 'rewrite_unedited_experiences', return_value=[])
    @patch.object(ResumeImprover, 'rewrite_unedited_projects', return_value=[])
    def test_enhance_resume_content_with_llm(self, mock_rewrite_projects, mock_rewrite_experiences, mock_write_objective, mock_extract_skills):
        """Test that _enhance_resume_content_with_llm calls appropriate sub-methods."""
        self.improver._enhance_resume_content_with_llm()
        mock_extract_skills.assert_called_once()
        mock_write_objective.assert_called_once()
        mock_rewrite_experiences.assert_called_once()
        mock_rewrite_projects.assert_called_once()
        self.assertEqual(self.improver.objective, "Mocked Objective")
        self.assertEqual(self.improver.skills, [{"category":"mock", "skills":["A","B"]}])

    @patch('services.resume_improver.utils.write_yaml')
    @patch('services.resume_improver.utils.read_yaml')
    def test_save_tailored_resume_to_yaml(self, mock_read_yaml, mock_write_yaml):
        """Test saving the resume to YAML."""
        # Set up some data on the improver instance
        self.improver.basic_info = {"name": "Test User"}
        self.improver.objective = "Test Objective"
        self.improver.education = []
        self.improver.experiences = []
        self.improver.projects = []
        self.improver.skills = []

        # Expected data to be written
        expected_resume_dict = {
            "editing": True,
            "basic": self.improver.basic_info,
            "objective": self.improver.objective,
            "education": self.improver.education,
            "experiences": self.improver.experiences,
            "projects": self.improver.projects,
            "skills": self.improver.skills,
        }
        mock_read_yaml.return_value = expected_resume_dict # Simulate successful read after write

        result = self.improver._save_tailored_resume_to_yaml()
        self.assertTrue(result)
        expected_yaml_path = os.path.join(self.improver.job_data_location, "resume.yaml")
        mock_write_yaml.assert_called_once_with(expected_resume_dict, filename=expected_yaml_path)
        mock_read_yaml.assert_called_once_with(filename=expected_yaml_path)
        self.assertEqual(self.improver.yaml_location, expected_yaml_path)
        self.assertEqual(self.improver.resume_yaml, expected_resume_dict)

    @patch('services.resume_improver.PDFGenerator')
    @patch('services.resume_improver.utils.read_yaml')
    @patch('services.resume_improver.subprocess.run') # Mock subprocess if auto_open_yaml is True
    def test_handle_resume_yaml_review_and_pdf_creation(self, mock_subprocess_run, mock_read_yaml, MockPDFGenerator):
        """Test the handling of YAML review and PDF creation process."""
        mock_pdf_instance = MockPDFGenerator.return_value
        mock_pdf_instance.create_pdf.return_value = "/fake/path/to/resume.pdf"

        # Simulate manual review: first read 'editing: true', then 'editing: false'
        mock_read_yaml.side_effect = [
            {"editing": True, "content": "version1"},
            {"editing": False, "content": "version2_edited"}
        ]

        self.improver.yaml_location = os.path.join(self.improver.job_data_location, "resume.yaml")
        # Create a dummy yaml_location file for os.path.exists to pass
        with open(self.improver.yaml_location, 'w') as f: json.dump({"editing": True}, f)

        with patch('services.resume_improver.time.sleep', return_value=None): # Speed up review loop
            self.improver._handle_resume_yaml_review_and_pdf_creation(
                auto_open_yaml=True, # This will trigger subprocess.run
                manual_review_yaml=True,
                skip_pdf=False,
                auto_open_pdf=True
            )

        # Check that PDFGenerator was used
        MockPDFGenerator.assert_called_once()
        mock_pdf_instance.create_pdf.assert_called_once_with(
            resume_data={"editing": False, "content": "version2_edited"}, # Data after review
            job_data_location=self.improver.job_data_location,
            auto_open=True
        )
        # Check that YAML was opened
        mock_subprocess_run.assert_called_once()
        # Check that read_yaml was called multiple times for review loop
        self.assertEqual(mock_read_yaml.call_count, 2)


class TestLangchainHelpersExisting(unittest.TestCase): # Renamed to avoid conflict
    def test_create_llm(self):
        """Test if create_llm runs (actual functionality depends on API keys etc)."""
        # This test is minimal as it depends on external factors / config
        with patch('services.langchain_helpers.ChatOpenAI') as mock_chat_openai:
            create_llm(model_name="test_model", temperature=0.5)
            mock_chat_openai.assert_called_with(model_name="test_model", temperature=0.5, cache=True)


if __name__ == "__main__":
    unittest.main()
