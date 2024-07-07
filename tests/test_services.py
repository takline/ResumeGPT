import unittest
from ..services.resume_improver import ResumeImprover
from ..services.langchain_helpers import create_llm, format_list_as_string, format_prompt_inputs_as_strings, parse_date, datediff_years

class TestResumeImprover(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.com/job-posting"
        self.resume_improver = ResumeImprover(self.url)

    def test_download_and_parse_job_post(self):
        self.resume_improver.download_and_parse_job_post()
        self.assertIsNotNone(self.resume_improver.job_post_html_data)
        self.assertIsNotNone(self.resume_improver.job_post_raw)

    def test_create_draft_tailored_resume(self):
        self.resume_improver.create_draft_tailored_resume()
        self.assertTrue(self.resume_improver.yaml_loc.endswith("resume.yaml"))

class TestLangchainHelpers(unittest.TestCase):
    def test_create_llm(self):
        llm = create_llm()
        self.assertIsNotNone(llm)

    def test_format_list_as_string(self):
        result = format_list_as_string(["item1", "item2"])
        self.assertEqual(result, "\n- item1\n- item2")

    def test_format_prompt_inputs_as_strings(self):
        result = format_prompt_inputs_as_strings(["key1", "key2"], key1="value1", key2="value2")
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_parse_date(self):
        date = parse_date("2023-01-01")
        self.assertEqual(date.year, 2023)

    def test_datediff_years(self):
        diff = datediff_years("2020-01-01", "2023-01-01")
        self.assertEqual(diff, 3.0)

if __name__ == "__main__":
    unittest.main()
