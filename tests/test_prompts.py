import unittest
from ..prompts.prompts import Prompts

class TestPrompts(unittest.TestCase):
    def setUp(self):
        Prompts.initialize()

    def test_load_prompts(self):
        self.assertIn("SECTION_HIGHLIGHTER", Prompts.lookup)

    def test_load_descriptions(self):
        self.assertIn("JOB_DESCRIPTION", Prompts.descriptions)

if __name__ == "__main__":
    unittest.main()
