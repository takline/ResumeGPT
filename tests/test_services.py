import unittest
from ..services.resume_improver import ResumeImprover
from ..services.langchain_helpers import (
    create_llm,
    format_list_as_string,
    format_prompt_inputs_as_strings,
    parse_date,
    datediff_years,
)
from ..config import config


class TestResumeImproverExtractor(unittest.TestCase):
    def setUp(self):
        self.url = (
            "https://takline.github.io/ResumeGPT/tests/test_data/example_job_posting"
        )
        self.resume_improver = ResumeImprover(self.url)

    def test_download_and_parse_job_post(self):
        #self.resume_improver.download_and_parse_job_post()
        #with open(os.path.join(config.PROJECT_PATH, "tests/test_data/example_job_posting.html"), 'r', encoding='utf-8') as file:
        #    raw_html = file.read()
        #self.resume_improver.parse_raw_job_post(raw_html=raw_html)

        # Check HTML data extraction
        self.assertIn(
            "<title>Data Infrastructure Engineer | OpenAI | OpenAI</title>",
            self.resume_improver.job_post_html_data,
            "HTML title not found in job post data",
        )
        self.assertIn(
            "Data Infrastructure Engineer",
            self.resume_improver.job_post_raw,
            "Job title not found in raw job post data",
        )

        # Check parsed job data
        self.assertIsNotNone(self.resume_improver.parsed_job, "Parsed job data is None")
        self.assertIsInstance(
            self.resume_improver.parsed_job, dict, "Parsed job data is not a dictionary"
        )

        # Check specific fields in parsed job data
        self.assertIsNotNone(
            self.resume_improver.parsed_job.get("job_summary"), "Job summary is None"
        )
        self.assertGreater(
            len(self.resume_improver.parsed_job.get("qualifications", [])),
            0,
            "Qualifications list is empty",
        )
        self.assertGreater(
            len(self.resume_improver.parsed_job.get("duties", [])),
            0,
            "Duties list is empty",
        )
        self.assertGreater(
            len(self.resume_improver.parsed_job.get("ats_keywords", [])),
            0,
            "ATS keywords list is empty",
        )

        # Check specific values in parsed job data
        self.assertNotEqual(
            self.resume_improver.parsed_job.get("is_fully_remote"),
            True,
            "Job is incorrectly marked as fully remote",
        )
        self.assertIn(
            "$200K – $385K",
            self.resume_improver.parsed_job.get("salary", ""),
            "Expected salary range not found",
        )
        self.assertIn(
            "data infrastructure engineer",
            self.resume_improver.parsed_job.get("job_title", "").lower(),
            "Expected job title not found",
        )
        self.assertIn(
            "openai",
            self.resume_improver.parsed_job.get("company", "").lower(),
            "Expected company name not found",
        )
        self.assertIn(
            "python",
            ", ".join(self.resume_improver.parsed_job.get("ats_keywords", [])).lower(),
            "Expected ATS keyword 'python' not found",
        )
        self.assertIn(
            "4+ years in data infrastructure engineering",
            ", ".join(
                self.resume_improver.parsed_job.get("qualifications", [])
            ).lower(),
            "Expected qualification not found",
        )
        self.assertIn(
            "design, build, and maintain data infrastructure systems",
            ", ".join(self.resume_improver.parsed_job.get("duties", [])).lower(),
            "Expected duty not found",
        )

    def test_create_draft_tailored_resume(self):
        self.resume_improver.create_draft_tailored_resume(
            auto_open=False, manual_review=False, skip_pdf_create=True
        )
        self.assertTrue(self.resume_improver.yaml_loc.endswith("resume.yaml"))


class TestLangchainHelpers(unittest.TestCase):
    def test_create_llm(self):
        llm = create_llm()
        self.assertIsNotNone(llm)


if __name__ == "__main__":
    unittest.main()
