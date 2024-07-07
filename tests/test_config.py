import unittest
from ..config import config

class TestConfig(unittest.TestCase):
    def test_logger_initialization(self):
        self.assertIsNotNone(config.logger)

    def test_project_paths(self):
        self.assertTrue(config.PROJECT_PATH)
        self.assertTrue(config.DATA_PATH)
        self.assertTrue(config.RESOURCES_PATH)
        self.assertTrue(config.DEFAULT_RESUME_PATH)

    def test_requests_headers(self):
        self.assertIn("User-Agent", config.REQUESTS_HEADERS)

    def test_model_configuration(self):
        self.assertEqual(config.CHAT_MODEL.__name__, "ChatOpenAI")
        self.assertEqual(config.MODEL_NAME, "gpt-4o")
        self.assertEqual(config.TEMPERATURE, 0.3)

    def test_openai_api_key(self):
        self.assertIn("OPENAI_API_KEY", config.os.environ)

    def test_load_config(self):
        self.assertIn("author", config.CONFIG_INI)
        self.assertIn("email", config.CONFIG_INI)

if __name__ == "__main__":
    unittest.main()
