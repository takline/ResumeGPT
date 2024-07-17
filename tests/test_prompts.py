import unittest
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from ..prompts.prompts import Prompts

PROMPT_GROUPS = ["IMPROVER", "SECTION_HIGHLIGHTER", "SKILLS_MATCHER", "OBJECTIVE_WRITER"]

PROMPT_DESCRIPTIONS = [
    "JOB_DESCRIPTION",
    "JOB_SKILLS",
    "RESUME_IMPROVEMENTS",
    "RESUME_IMPROVER_OUTPUT",
    "RESUME_SECTION_HIGHLIGHT",
    "RESUME_SECTION_HIGHLIGHTER_OUTPUT",
    "RESUME_SKILLS",
    "RESUME_SKILLS_MATCHER_OUTPUT",
    "RESUME_OBJECTIVE_OUTPUT",
]


class TestPrompts(unittest.TestCase):
    def setUp(self):
        Prompts.initialize()

    def test_load_prompts(self):
        for prompt_group in PROMPT_GROUPS:
            self.assertIn(prompt_group, Prompts.lookup)
            self.assertIsInstance(Prompts.lookup[prompt_group], list)
            self.assertGreater(len(Prompts.lookup[prompt_group]), 0)

    def test_load_descriptions(self):
        for description in PROMPT_DESCRIPTIONS:
            self.assertIn(description, Prompts.descriptions)
            self.assertIsInstance(Prompts.descriptions[description], dict)
            self.assertGreater(len(Prompts.descriptions[description]), 0)


if __name__ == "__main__":
    unittest.main()
