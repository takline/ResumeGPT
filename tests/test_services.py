import unittest
from ..services.resume_improver import ResumeImprover
from ..services.langchain_helpers import (
    create_llm,
    parse_date,
    datediff_years,
)
from ..utils import *
from ..config import config


class TestResumeImproverExtractor(unittest.TestCase):
    def setUp(self):
        self.url = (
            "https://takline.github.io/ResumeGPT/tests/test_data/example_job_posting"
        )
        self.resume_improver = ResumeImprover(self.url)

    def test_download_and_parse_job_post(self):
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
        ats_keywords = ", ".join(
            self.resume_improver.parsed_job.get("ats_keywords", [])
        ).lower()
        self.assertTrue(
            "data" in ats_keywords or "python" in ats_keywords,
            "Expected ATS keyword 'data' or 'python' not found",
        )
        technical_skills = ", ".join(
            self.resume_improver.parsed_job.get("technical_skills", [])
        ).lower()
        self.assertTrue(
            "python" in technical_skills or "distributed" in technical_skills,
            "Expected technical skill 'python' or 'distributed' not found",
        )
        non_technical_skills = ", ".join(
            self.resume_improver.parsed_job.get("non_technical_skills", [])
        ).lower()
        self.assertTrue(
            "learn" in non_technical_skills or "communication" in non_technical_skills,
            "Expected non-technical skill 'learn' or 'communication' not found",
        )
        qualifications = ", ".join(
            self.resume_improver.parsed_job.get("qualifications", [])
        ).lower()
        self.assertTrue(
            "4+" in qualifications or "infrastructure engineering" in qualifications,
            "Expected qualification '4+' or 'infrastructure engineering' not found",
        )
        duties = ", ".join(self.resume_improver.parsed_job.get("duties", [])).lower()
        self.assertTrue(
            "design" in duties or "infrastructure" in duties,
            "Expected duty 'design' or 'infrastructure' not found",
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
