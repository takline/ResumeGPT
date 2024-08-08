# ResumeGPT - Tests

ResumeGPT tests are structured as follows:

- `tests/__init__.py`: Initializes the tests package.
- `tests/test_config.py`: Contains tests for the `config` module.
- `tests/test_services.py`: Contains tests for the `services` module.
- `tests/test_pdf_generation.py`: Contains tests for the `pdf_generation` module.
- `tests/test_prompts.py`: Contains tests for the `prompts` module.
- `tests/test_models.py`: Contains tests for the `models` module.
- `tests/test_utils.py`: Contains tests for the `utils` module.


## Running the Tests

```python
To run the tests, use the following command:```python
pytest tests/ --junitxml=tests/test-results.xml --tb=long -vv --cov=./ --cov-report=xml:tests/coverage.xml
```

or:


```python
pytest
```



or:

```python
pytest tests/test_services.py
```


<br>

## Continuous Integration and Deployment

The CI/CD workflow is defined in [`.github/workflows/publish-to-pypi.yaml`](https://github.com/takline/ResumeGPT/blob/main/.github/workflows/publish-to-pypi.yaml).

### Workflow Overview

1. **Test Job**:
    - **Checkout code**: Retrieves the latest code from the repository.
    - **Set up Python**: Configures the Python environment.
    - **Install dependencies**: Installs the required dependencies from `requirements.txt`.
    - **Run tests with pytest**: Executes the tests and generates test results and coverage reports.
    - **Upload test results**: Uploads the test results as an artifact.
    - **Upload coverage results**: Uploads the coverage report as an artifact.
    - **Annotate the test results**: Adds annotations to the test results for easier debugging.

2. **Build Job**:
    - **Build distribution**: Creates a binary wheel and a source tarball of the package.
    - **Store the distribution packages**: Uploads the built distributions as artifacts.

3. **GitHub Release Job**:
    - **Sign the distributions**: Uses Sigstore to sign the distribution packages.
    - **Create GitHub Release**: Creates a new release on GitHub.
    - **Upload artifact signatures**: Uploads the signed artifacts to the GitHub release.

4. **Publish to PyPI Job**:
    - **Publish distribution to PyPI**: Publishes the signed distribution packages to PyPI.

### Artifacts

- **Test Results**: Stored as `tests/test-results.xml`.
- **Coverage Report**: Stored as `tests/coverage.xml`.
- **Distribution Packages**: Stored in the `dist/` directory and uploaded to GitHub and PyPI.

