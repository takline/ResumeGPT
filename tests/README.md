#  ResumeGPT - Tests

ResumeGPT tests are structured as follows:

- `tests/__init__.py`: Initializes the tests package.
- `tests/test_config.py`: Contains tests for the `config` module.
- `tests/test_services.py`: Contains tests for the `services` module.
- `tests/test_pdf_generation.py`: Contains tests for the `pdf_generation` module.
- `tests/test_prompts.py`: Contains tests for the `prompts` module.
- `tests/test_models.py`: Contains tests for the `models` module.
- `tests/test_utils.py`: Contains tests for the `utils` module.

## Tests Included in Each File

### tests/test_config.py
- Tests for logger initialization.
- Tests for project paths.
- Tests for requests headers.
- Tests for model configuration.
- Tests for OpenAI API key.
- Tests for loading configuration from `config.ini`.

### tests/test_services.py
- Tests for `ResumeImprover` class methods:
  - `download_and_parse_job_post`
  - `create_draft_tailored_resume`
- Tests for `langchain_helpers` functions:
  - `create_llm`
  - `format_list_as_string`
  - `format_prompt_inputs_as_strings`
  - `parse_date`
  - `datediff_years`

### tests/test_pdf_generation.py
- Tests for `ResumePDFGenerator` class methods:
  - `generate_resume`

### tests/test_prompts.py
- Tests for `Prompts` class methods:
  - `initialize`
  - `load_prompts`
  - `load_descriptions`

### tests/test_models.py
- Tests for `JobDescription` model fields.
- Tests for `JobSkills` model fields.
- Tests for `ResumeSectionHighlight` model fields.
- Tests for `ResumeSkills` model fields.

### tests/test_utils.py
- Tests for `yaml_handler` functions:
  - `read_yaml`
  - `write_yaml`
  - `dict_to_yaml_string`
- Tests for `file_handler` functions:
  - `read_jobfile`
  - `generator_key_in_nested_dict`
  - `get_dict_field`

## Running the Tests

To run the tests, use the following command:

```
pytest
```

