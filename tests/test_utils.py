import unittest
from ..utils.yaml_handler import read_yaml, write_yaml, dict_to_yaml_string
from ..utils.file_handler import (
    read_jobfile,
    generator_key_in_nested_dict,
    get_dict_field,
)
import os
from ..config import config


class TestYamlHandler(unittest.TestCase):
    def test_read_yaml(self):
        data = read_yaml(filename=os.path.join(config.DATA_PATH, "sample_resume.yaml"))
        self.assertIsInstance(data, dict)

    def test_write_yaml(self):
        data = {"key": "value"}
        write_yaml(
            data,
            filename=os.path.join(config.DATA_PATH, "tests_example/test_output.yaml"),
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(config.DATA_PATH, "tests_example/test_output.yaml")
            )
        )

    def test_dict_to_yaml_string(self):
        data = {"key": "value"}
        yaml_string = dict_to_yaml_string(data)
        self.assertIn("key: value", yaml_string)


class TestFileHandler(unittest.TestCase):
    def test_read_jobfile(self):
        content = read_jobfile(os.path.join(config.DATA_PATH, "tests_example/job.yaml"))
        self.assertIsInstance(content, str)

    def test_generator_key_in_nested_dict(self):
        nested_dict = {"key1": {"key2": "value"}}
        result = list(generator_key_in_nested_dict("key2", nested_dict))
        self.assertIn("value", result)

    def test_get_dict_field(self):
        data_dict = {"field": "value"}
        result = get_dict_field("field", data_dict)
        self.assertEqual(result, "value")


if __name__ == "__main__":
    unittest.main()
