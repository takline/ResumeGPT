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
        self.assertTrue(
            any(key.lower() == "user-agent".lower() for key in config.REQUESTS_HEADERS)
        )

    def test_model_configuration_types(self):
        self.assertIsInstance(config.CHAT_MODEL, type)
        self.assertIsInstance(config.MODEL_NAME, str)
        self.assertIsInstance(config.TEMPERATURE, float)

    def test_openai_api_key(self):
        self.assertIn("OPENAI_API_KEY", config.os.environ)


if __name__ == "__main__":
    unittest.main()
