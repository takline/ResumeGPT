import unittest
from ..models.job_post import JobDescription, JobSkills, JobPost
from ..models.resume import ResumeSectionHighlight, ResumeSectionHighlighterOutput, ResumeSkills, ResumeSkillsMatcherOutput, ResumeSummarizerOutput, ResumeImprovements, ResumeImproverOutput

class TestJobDescription(unittest.TestCase):
    def test_job_description_fields(self):
        job_description = JobDescription(company="Example Corp", job_title="Software Engineer")
        self.assertEqual(job_description.company, "Example Corp")
        self.assertEqual(job_description.job_title, "Software Engineer")

class TestJobSkills(unittest.TestCase):
    def test_job_skills_fields(self):
        job_skills = JobSkills(technical_skills=["Python"], non_technical_skills=["Communication"])
        self.assertIn("Python", job_skills.technical_skills)
        self.assertIn("Communication", job_skills.non_technical_skills)

class TestResumeModels(unittest.TestCase):
    def test_resume_section_highlight(self):
        highlight = ResumeSectionHighlight(highlight="Led a team", relevance=5)
        self.assertEqual(highlight.highlight, "Led a team")
        self.assertEqual(highlight.relevance, 5)

    def test_resume_skills(self):
        skills = ResumeSkills(technical_skills=["Python"], non_technical_skills=["Communication"])
        self.assertIn("Python", skills.technical_skills)
        self.assertIn("Communication", skills.non_technical_skills)

if __name__ == "__main__":
    unittest.main()
