"""
Core service for resume improvement and tailoring.

This module defines the `ResumeImprover` class, which is the primary engine for
processing job postings, comparing them against a user's resume, leveraging
Language Models (LLMs) to generate improvements and tailored content, and
orchestrating the creation of a new resume in YAML and PDF formats.

Key functionalities include:
- Downloading and parsing job posting URLs or raw HTML.
- Caching downloaded HTML content to improve efficiency.
- Extracting structured information from job postings.
- Utilizing LLMs to:
    - Match skills between the resume and job posting.
    - Generate a tailored resume objective.
    - Rewrite experience and project highlights to align with the job.
    - Suggest overall improvements.
- Saving the tailored resume content to a YAML file for user review.
- Managing a manual review process where users can edit the YAML.
- Generating a final PDF resume from the reviewed YAML data.
- Supporting concurrent processing of multiple job postings in the background.
"""
import os
import time
import subprocess
import logging
from datetime import datetime, timedelta
import json
import hashlib
from typing import List, Optional, Union, Dict, Any, Type # Added Type for _chain_updater
from bs4 import BeautifulSoup
# import uuid # uuid seems unused, consider removing if confirmed
import requests
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
# from langchain_core.output_parsers import StrOutputParser # Unused, can be removed
from ..models.resume import (
    ResumeImproverOutput,
    ResumeSkillsMatcherOutput,
    ResumeSummarizerOutput,
    ResumeSectionHighlighterOutput,
    ResumeSkills, # For type hinting in extract_matched_skills
    ResumeSectionHighlight, # For type hinting in rewrite_section
    ResumeImprovements # For type hinting in suggest_improvements
)
from .. import utils
from .. import config # Imports config object directly
from .langchain_helpers import create_llm, chain_formatter # Specific imports
from ..prompts.prompts import Prompts
from ..models.job_post import JobPost
from ..pdf_generation.pdf_generator import PDFGenerator
# import concurrent.futures # Unused directly in this file, but used by BackgroundRunner
from fp.fp import FreeProxy # For web scraping proxies
# from ..config import config # Redundant import of config

# --- Constants for HTML Caching ---
# HTML_CACHE_ENABLED: Toggle for the HTML caching feature. If False, caching is bypassed.
HTML_CACHE_ENABLED = True
# HTML_CACHE_DIR: Directory where cached HTML files and their metadata are stored.
# Defaults to a 'cache/html_cache' directory relative to the project root.
HTML_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache", "html_cache")
# HTML_CACHE_DURATION_SECONDS: How long cached HTML content is considered fresh (e.g., 24 hours).
HTML_CACHE_DURATION_SECONDS = 24 * 60 * 60
# --- End Constants ---


class ResumeImprover:
    """
    Orchestrates the process of tailoring a resume to a specific job posting.

    This class handles fetching job posting data, parsing it, loading a base resume,
    using LLMs to enhance various resume sections (objective, skills, experiences, projects),
    saving the result to a YAML file for user review, and finally generating a PDF.
    It also supports processing multiple job postings concurrently in the background.

    Attributes:
        url (str): The URL of the job posting currently being processed.
        resume_location (str): Filesystem path to the base resume YAML file.
        llm_kwargs (Dict[str, Any]): Keyword arguments to pass to the LLM constructor.
        job_post_html_data (Optional[str]): Raw HTML content of the fetched job posting.
        job_post_raw (Optional[str]): Plain text extracted from `job_post_html_data`.
        resume (Optional[Dict[str, Any]]): The loaded base resume data.
        resume_yaml (Optional[Dict[str, Any]]): The tailored resume data, loaded/reloaded from `yaml_location`.
        job_post (Optional[JobPost]): An instance of the `JobPost` model.
        parsed_job (Optional[Dict[str, Any]]): Structured data extracted from the job posting.
        clean_url (Optional[str]): A sanitized version of the job posting URL, used for directory naming.
        job_data_location (Optional[str]): Path to the directory where job-specific data
                                           (job.yaml, resume.yaml, PDF) is stored.
        yaml_location (Optional[str]): Full path to the tailored resume YAML file.
        basic_info (Optional[Dict[str, Any]]): Basic information section of the resume.
        objective (Optional[str]): Resume objective statement.
        education (Optional[List[Dict[str, Any]]]): Education section of the resume.
        experiences (Optional[List[Dict[str, Any]]]): Experience entries from the resume.
        projects (Optional[List[Dict[str, Any]]]): Project entries from the resume.
        skills (Optional[List[Dict[str, Any]]]): Skills section of the resume.
        degrees (Optional[List[str]]): List of degree names extracted from the resume.
    """

    def __init__(self, url: str, resume_location: Optional[str] = None, llm_kwargs: Optional[Dict[str, Any]] = None):
        """
        Initializes the ResumeImprover instance.

        This involves setting up initial attributes, processing the provided job post URL
        (including downloading, parsing, and caching HTML), and loading the base resume data.

        Args:
            url (str): The URL of the job posting to process.
            resume_location (Optional[str]): The file path to the base resume YAML file.
                                           If None, uses `config.DEFAULT_RESUME_PATH`.
            llm_kwargs (Optional[Dict[str, Any]]): Additional keyword arguments to pass to the
                                                 Language Model constructor. Defaults to an empty dict.
        """
        super().__init__()

        # Attributes related to the job posting
        self.url: str = url
        self.job_post_html_data: Optional[str] = None
        self.job_post_raw: Optional[str] = None
        self.job_post: Optional[JobPost] = None
        self.parsed_job: Optional[Dict[str, Any]] = None
        self.clean_url: Optional[str] = None
        self.job_data_location: Optional[str] = None

        # Attributes related to the resume
        self.resume_location: str = resume_location or config.DEFAULT_RESUME_PATH
        self.resume: Optional[Dict[str, Any]] = None
        self.resume_yaml: Optional[Dict[str, Any]] = None
        self.yaml_location: Optional[str] = None

        # Extracted resume sections
        self.basic_info: Optional[Dict[str, Any]] = {}
        self.objective: Optional[str] = ""
        self.education: Optional[List[Dict[str, Any]]] = []
        self.experiences: Optional[List[Dict[str, Any]]] = []
        self.projects: Optional[List[Dict[str, Any]]] = []
        self.skills: Optional[List[Dict[str, Any]]] = []
        self.degrees: Optional[List[str]] = []

        self.llm_kwargs: Dict[str, Any] = llm_kwargs or {}

        # Initial processing steps
        self._initialize_job_post_data(job_post_url=self.url)
        self._update_resume_fields()

    def _update_resume_fields(self) -> None:
        """
        Loads resume data from `self.resume_location` and populates instance attributes.

        Reads the YAML file specified by `self.resume_location`, checks its format,
        and then extracts various sections (basic info, education, experiences, etc.)
        into corresponding instance attributes (e.g., `self.basic_info`, `self.education`).
        Also extracts degree information.

        Raises:
            FileNotFoundError: If the resume file at `self.resume_location` is not found.
            IOError: If there is an error reading the resume file.
            ValueError: If the resume content is invalid, cannot be parsed as YAML,
                        or if essential fields are missing after parsing.
        """
        try:
            utils.check_resume_format(self.resume_location)
            raw_resume_data = utils.read_yaml(filename=self.resume_location)
            if not isinstance(raw_resume_data, dict):
                logging.warning(f"Resume file {self.resume_location} is empty or not valid YAML dictionary.")
                self.resume, self.degrees, self.basic_info, self.education, self.experiences, self.projects, self.skills, self.objective = {}, [], {}, [], [], [], [], ""
                return
            self.resume = raw_resume_data
        except FileNotFoundError:
            logging.error(f"Resume file not found: {self.resume_location}", exc_info=True)
            raise
        except IOError as e:
            logging.error(f"IOError reading resume file {self.resume_location}: {e}", exc_info=True)
            raise
        except Exception as e:
            logging.error(f"Unexpected error processing resume file {self.resume_location}: {e}", exc_info=True)
            self.resume, self.degrees, self.basic_info, self.education, self.experiences, self.projects, self.skills, self.objective = {}, [], {}, [], [], [], [], ""
            raise ValueError(f"Failed to process resume file {self.resume_location} due to: {e}")

        self.degrees = self._get_degrees(self.resume or {})
        self.basic_info = utils.get_dict_field(field="basic", data_dict=self.resume or {})
        self.education = utils.get_dict_field(field="education", data_dict=self.resume or []) # type: ignore
        self.experiences = utils.get_dict_field(field="experiences", data_dict=self.resume or []) # type: ignore
        self.projects = utils.get_dict_field(field="projects", data_dict=self.resume or []) # type: ignore
        self.skills = utils.get_dict_field(field="skills", data_dict=self.resume or []) # type: ignore
        self.objective = utils.get_dict_field(field="objective", data_dict=self.resume or "") # type: ignore

    def update_resume(self, new_resume_location: str) -> None:
        """
        Updates the resume source file and reloads resume fields.

        Args:
            new_resume_location (str): The new file path to the resume YAML file.
        """
        self.resume_location = new_resume_location
        self._update_resume_fields()

    def _extract_text_from_html_content(self) -> None:
        """
        Extracts plain text from `self.job_post_html_data` using BeautifulSoup.

        The extracted text is stored in `self.job_post_raw`. If `self.job_post_html_data`
        is None or empty, `self.job_post_raw` is set to None.

        Raises:
            TypeError: If `self.job_post_html_data` is not suitable for BeautifulSoup.
            Exception: Catches other exceptions from BeautifulSoup during parsing, logs them,
                       and re-raises to indicate failure.
        """
        if not self.job_post_html_data:
            logging.warning(f"No HTML data to extract text from for URL: {self.url}. `self.job_post_raw` will be None.")
            self.job_post_raw = None
            return

        try:
            soup = BeautifulSoup(self.job_post_html_data, "html.parser")
            self.job_post_raw = soup.get_text(separator=" ", strip=True)
            logging.info(f"Successfully extracted text from HTML for URL: {self.url}")
        except TypeError as e:
            logging.error(f"TypeError during HTML parsing for {self.url}. HTML data might be invalid: {e}", exc_info=True)
            self.job_post_raw = None
            raise
        except Exception as e:
            logging.error(f"BeautifulSoup failed to parse HTML for URL {self.url}: {e}", exc_info=True)
            self.job_post_raw = None
            raise

    def _download_job_post_html(self, target_url: Optional[str] = None) -> bool:
        """
        Downloads HTML content of a job post URL, with caching and retries.

        Sets `self.job_post_html_data` on success. Checks local cache first.
        If not cached or stale, downloads the content. Retries on failures
        with exponential backoff and can use a proxy.

        Args:
            target_url (Optional[str]): The URL to download. If None, uses `self.url`.

        Returns:
            bool: True if HTML content was successfully obtained, False otherwise.
        """
        current_url_to_download = target_url or self.url
        if not current_url_to_download:
            logging.error("No URL available for downloading job post HTML.")
            return False
        self.url = current_url_to_download

        if HTML_CACHE_ENABLED:
            url_hash = hashlib.md5(self.url.encode('utf-8')).hexdigest()
            cache_file_name = f"{url_hash}.html"
            cache_meta_name = f"{url_hash}.meta.json"
            html_cache_file_path = os.path.join(HTML_CACHE_DIR, cache_file_name)
            meta_cache_file_path = os.path.join(HTML_CACHE_DIR, cache_meta_name)

            if os.path.exists(meta_cache_file_path) and os.path.exists(html_cache_file_path):
                try:
                    with open(meta_cache_file_path, 'r', encoding='utf-8') as f_meta:
                        metadata = json.load(f_meta)
                    cached_timestamp_str = metadata.get("timestamp")
                    cached_url = metadata.get("url")

                    if cached_timestamp_str and cached_url == self.url:
                        cached_timestamp = datetime.fromisoformat(cached_timestamp_str)
                        if datetime.now() - cached_timestamp < timedelta(seconds=HTML_CACHE_DURATION_SECONDS):
                            logging.info(f"Using cached HTML for {self.url} from {html_cache_file_path}")
                            with open(html_cache_file_path, 'r', encoding='utf-8') as f_html:
                                self.job_post_html_data = f_html.read()
                            if self.job_post_html_data:
                                return True
                            else:
                                logging.warning(f"Cached HTML file {html_cache_file_path} for {self.url} was empty. Will re-download.")
                        else:
                            logging.info(f"Cache stale for {self.url}. Last updated: {cached_timestamp_str}. Will re-download.")
                    else:
                        logging.warning(f"Cache metadata for {self.url} (hash: {url_hash}) mismatch or incomplete. Ignoring. Cached URL: {cached_url}")
                except Exception as e:
                    logging.warning(f"Error reading from cache for {self.url}: {e}. Proceeding to download.", exc_info=True)

        logging.info(f"Cache miss or stale for {self.url}. Proceeding with download.")
        max_retries = config.MAX_RETRIES
        backoff_factor = config.BACKOFF_FACTOR
        should_use_proxy = False
        download_successful = False

        for attempt in range(max_retries):
            actual_attempt_number = attempt + 1
            try:
                proxies = None
                if should_use_proxy:
                    logging.info(f"Attempt {actual_attempt_number}/{max_retries} using proxy for {self.url}.")
                    try:
                        proxy_url = FreeProxy(rand=True, timeout=0.5).get()
                        if proxy_url:
                            proxies = {"http": proxy_url, "https": proxy_url}
                        else:
                            logging.warning("Failed to fetch a proxy. Proceeding without proxy.")
                            should_use_proxy = False
                    except Exception as proxy_e:
                        logging.warning(f"Error fetching proxy: {proxy_e}. Proceeding without proxy.", exc_info=True)
                        should_use_proxy = False
                else:
                    logging.info(f"Attempt {actual_attempt_number}/{max_retries} to download URL: {self.url}")

                response = requests.get(
                    self.url, headers=config.REQUESTS_HEADERS, proxies=proxies, timeout=config.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                self.job_post_html_data = response.text
                logging.info(f"Successfully downloaded HTML from URL: {self.url}")
                download_successful = True
                break
            except requests.exceptions.Timeout:
                logging.warning(f"Timeout for {self.url}. Attempt {actual_attempt_number}/{max_retries}.", exc_info=True)
                should_use_proxy = True
                time.sleep(backoff_factor * (2 ** attempt))
            except requests.exceptions.HTTPError as e:
                logging.warning(f"HTTP error {e.response.status_code} for {self.url}. Attempt {actual_attempt_number}/{max_retries}.", exc_info=True)
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", backoff_factor * (2 ** attempt)))
                    logging.warning(f"Rate limit. Retrying in {retry_after}s...")
                    time.sleep(retry_after)
                    should_use_proxy = True
                elif e.response.status_code >= 500:
                    time.sleep(backoff_factor * (2 ** attempt))
                    should_use_proxy = True
                else:
                    logging.error(f"Client error {e.response.status_code} for {self.url}. Not retrying.", exc_info=True)
                    self.job_post_html_data = None
                    return False
            except requests.exceptions.RequestException as e:
                logging.warning(f"Network error for {self.url}. Attempt {actual_attempt_number}/{max_retries}: {e}", exc_info=True)
                time.sleep(backoff_factor * (2 ** attempt))
                should_use_proxy = True
            except Exception as e:
                logging.error(f"Unexpected download error for {self.url}. Attempt {actual_attempt_number}/{max_retries}: {e}", exc_info=True)
                time.sleep(backoff_factor * (2 ** attempt))
                should_use_proxy = True

        if download_successful and self.job_post_html_data and HTML_CACHE_ENABLED:
            try:
                os.makedirs(HTML_CACHE_DIR, exist_ok=True)
                url_hash = hashlib.md5(self.url.encode('utf-8')).hexdigest() # Re-ensure hash is available
                html_cache_file_path = os.path.join(HTML_CACHE_DIR, f"{url_hash}.html")
                meta_cache_file_path = os.path.join(HTML_CACHE_DIR, f"{url_hash}.meta.json")
                with open(html_cache_file_path, 'w', encoding='utf-8') as f_html:
                    f_html.write(self.job_post_html_data)
                metadata_to_save = {"url": self.url, "timestamp": datetime.now().isoformat()}
                with open(meta_cache_file_path, 'w', encoding='utf-8') as f_meta:
                    json.dump(metadata_to_save, f_meta)
                logging.info(f"Saved downloaded HTML for {self.url} to cache: {html_cache_file_path}")
            except Exception as e:
                logging.error(f"Error saving HTML to cache for {self.url}: {e}", exc_info=True)

        if not download_successful:
            logging.error(f"Exceeded max retries for URL {self.url}. Download failed.")
            self.job_post_html_data = None

        return download_successful

    def _parse_and_save_job_post_text(self) -> bool:
        """
        Parses raw job post text, generates a directory/filename, and saves parsed data to YAML.

        Assumes `self.job_post_raw` is populated. It populates `self.job_post` (JobPost model instance),
        `self.parsed_job` (dict from JobPost model), `self.clean_url` (sanitized name for directory),
        and `self.job_data_location` (path to this directory). The parsed job data is saved as `job.yaml`
        within this directory.

        Returns:
            bool: True if parsing and saving were successful, False otherwise.
        """
        if not self.job_post_raw:
            logging.error(f"No raw job post text available to parse (URL: {self.url}). Cannot proceed.")
            return False

        try:
            self.job_post = JobPost(self.job_post_raw)
            self.parsed_job = self.job_post.parse_job_post(verbose=False)
            if not self.parsed_job:
                 logging.warning(f"Parsing job post text for {self.url} yielded no structured data. Saving empty job data.")
                 self.parsed_job = {}
        except Exception as e:
            logging.error(f"Error during JobPost initialization or parsing for {self.url}: {e}", exc_info=True)
            self.parsed_job = {}

        job_title = self.parsed_job.get("job_title", "unknown_job_title") if isinstance(self.parsed_job, dict) else "unknown_job_title"
        company_name = self.parsed_job.get("company", "unknown_company") if isinstance(self.parsed_job, dict) else "unknown_company"
        base_dir_name = f"{company_name}_{job_title}".replace(" ", "_").replace("/", "-").replace("\\", "-")
        base_dir_name = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in base_dir_name)
        base_dir_name = base_dir_name[:100]

        generic_names = {"unknown_company_unknown_job_title", "unknown_job_title", "unknown_company", "_"}
        if not base_dir_name or base_dir_name in generic_names: # Check if name is too generic
            logging.info(f"Using URL-based fallback for directory name for {self.url} due to generic job details.")
            if "://" in self.url:
                url_part = self.url.split("://")[1]
            else:
                url_part = self.url
            url_part_sanitized = "".join(c if c.isalnum() or c in ['_', '.', '-'] else '_' for c in url_part)
            base_dir_name = url_part_sanitized[:100]

        self.clean_url = base_dir_name
        self.job_data_location = os.path.join(config.DATA_PATH, self.clean_url)

        try:
            os.makedirs(self.job_data_location, exist_ok=True)
            logging.info(f"Ensured data directory exists: {self.job_data_location}")
            yaml_file_path = os.path.join(self.job_data_location, "job.yaml")
            utils.write_yaml(self.parsed_job if isinstance(self.parsed_job, dict) else {}, filename=yaml_file_path)
            logging.info(f"Successfully wrote job data to YAML: {yaml_file_path}")
            return True
        except IOError as e:
            logging.error(f"File IO error creating directory or writing YAML for {self.url} at {self.job_data_location}: {e}", exc_info=True)
            return False
        except Exception as e:
            logging.error(f"Unexpected error in file operations for job post {self.url} at {self.job_data_location}: {e}", exc_info=True)
            return False

    def _initialize_job_post_data(self, job_post_url: Optional[str] = None) -> None:
        """
        Orchestrates the initial fetching, parsing, and saving of job post data.

        Args:
            job_post_url (Optional[str]): The URL of the job post. Uses `self.url` if None.
        """
        current_url = job_post_url or self.url
        if not current_url:
            logging.critical("No URL for job post data initialization.")
            return
        self.url = current_url

        if not self._download_job_post_html(target_url=self.url):
            logging.error(f"Failed to download job post HTML for {self.url}. Aborting.")
            return
        try:
            self._extract_text_from_html_content()
        except Exception as e:
            logging.error(f"Failed to extract text from HTML for {self.url}: {e}. Aborting.", exc_info=True)
            return
        if not self.job_post_raw:
            logging.error(f"HTML text extraction resulted in no data for {self.url}. Aborting.")
            return
        if not self._parse_and_save_job_post_text():
            logging.error(f"Failed to parse/save job post text for {self.url}. Data may be incomplete.")
            return
        logging.info(f"Job post data initialization completed for URL: {self.url}")

    def download_and_parse_job_post(self, url: Optional[str] = None) -> None:
        """
        Public method to (re-)download, parse, and save a job post from a URL.

        Args:
            url (Optional[str]): The job post URL. Uses instance's `self.url` if None.
        """
        target_url = url or self.url
        if not target_url:
            logging.error("No URL specified for download_and_parse_job_post.")
            return
        logging.info(f"Processing job post for URL: {target_url}")
        self._initialize_job_post_data(job_post_url=target_url)

    def parse_raw_job_post(self, raw_html_content: str) -> None:
        """
        Parses a job post from a raw HTML string and saves the extracted data.

        Args:
            raw_html_content (str): Raw HTML content of the job post.
        """
        if not raw_html_content or not isinstance(raw_html_content, str):
            logging.error("Invalid or empty raw HTML provided.")
            return
        self.job_post_html_data = raw_html_content
        try:
            self._extract_text_from_html_content()
        except Exception as e:
            logging.error(f"Failed to extract text from raw HTML: {e}", exc_info=True)
            return
        if not self.job_post_raw:
            logging.error("No raw text extracted from provided HTML. Cannot parse.")
            return
        if not self.url: # If URL wasn't set (e.g. direct call after empty init)
            self.url = f"raw_html_input_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            logging.info(f"Generated placeholder URL for raw HTML: {self.url}")
        if not self._parse_and_save_job_post_text():
            logging.error(f"Failed to parse/save job post from raw HTML (source: {self.url}).")
            return
        logging.info(f"Successfully parsed/saved job post from raw HTML (source: {self.url}).")

    def create_draft_tailored_resume(
        self,
        auto_open: bool = True,
        manual_review: bool = True,
        skip_pdf_create: bool = False
    ) -> None:
        """
        Orchestrates the full process of creating a tailored resume.

        Args:
            auto_open (bool): Auto-open generated resume YAML and PDF. Defaults to True.
            manual_review (bool): Pause for manual YAML review. Defaults to True.
            skip_pdf_create (bool): If True, skips PDF creation. Defaults to False.
        """
        if not self.job_data_location:
            logging.error("Job data location not set. Run job post processing first.")
            return
        if not self.resume:
            logging.error("Base resume data not loaded. Update resume location first.")
            return

        logging.info(f"Starting resume tailoring for job: {self.clean_url or self.url}")
        self._enhance_resume_content_with_llm()
        if not self._save_tailored_resume_to_yaml():
            logging.error("Failed to save tailored resume to YAML. Aborting.")
            return
        self._handle_resume_yaml_review_and_pdf_creation(
            auto_open_yaml=auto_open,
            manual_review_yaml=manual_review,
            skip_pdf=skip_pdf_create,
            auto_open_pdf=auto_open
        )
        logging.info(f"Draft tailored resume process completed for job: {self.clean_url or self.url}")

    def _enhance_resume_content_with_llm(self) -> None:
        """
        Uses LLMs to update resume sections (skills, objective, experiences, projects).
        Updates instance attributes (e.g., `self.skills`, `self.objective`).
        Assumes `self.resume` and `self.parsed_job` are populated.
        """
        logging.info(f"Starting LLM enhancements for job: {self.clean_url or self.url}...")
        logging.info("Attempting to enhance skills with LLM...")
        updated_skills = self.extract_matched_skills(verbose=False)
        if updated_skills is not None:
            self.skills = updated_skills
            logging.info("Skills enhancement processed.")
        else:
            logging.warning("Skills enhancement failed or no new data. Original skills retained.")

        logging.info("Attempting to enhance objective with LLM...")
        updated_objective = self.write_objective(verbose=False)
        if updated_objective is not None:
            self.objective = updated_objective
            logging.info("Objective enhancement processed.")
        else:
            logging.warning("Objective enhancement failed or no new data. Original objective retained.")

        logging.info("Attempting to enhance experiences with LLM...")
        if self.experiences:
            updated_experiences = self.rewrite_unedited_experiences(verbose=False)
            self.experiences = updated_experiences
            logging.info("Experiences enhancement processed.")
        else:
            logging.info("No experiences to enhance.")

        logging.info("Attempting to enhance projects with LLM...")
        if self.projects:
            updated_projects = self.rewrite_unedited_projects(verbose=False)
            self.projects = updated_projects
            logging.info("Projects enhancement processed.")
        else:
            logging.info("No projects to enhance.")
        logging.info(f"LLM content enhancement completed for job: {self.clean_url or self.url}.")

    def _save_tailored_resume_to_yaml(self) -> bool:
        """
        Saves current resume data to 'resume.yaml' in `self.job_data_location`.
        Sets `self.yaml_location` and updates `self.resume_yaml` by reloading.

        Returns:
            bool: True if saving and reloading YAML was successful, False otherwise.
        """
        if not self.job_data_location:
            logging.error("Job data location not set. Cannot save resume YAML.")
            return False
        self.yaml_location = os.path.join(self.job_data_location, "resume.yaml")
        resume_content_to_save = dict(
            editing=True, basic=self.basic_info or {}, objective=self.objective or "",
            education=self.education or [], experiences=self.experiences or [],
            projects=self.projects or [], skills=self.skills or [],
        )
        try:
            utils.write_yaml(resume_content_to_save, filename=self.yaml_location)
            logging.info(f"Tailored resume YAML saved to: {self.yaml_location}")
            self.resume_yaml = utils.read_yaml(filename=self.yaml_location)
            if self.resume_yaml is None:
                logging.error(f"Failed to reload {self.yaml_location} after saving. File empty/corrupt.")
                return False
            logging.info(f"Reloaded resume YAML from {self.yaml_location}")
            return True
        except FileNotFoundError:
            logging.error(f"Error saving resume YAML: {self.yaml_location} not found (directory issue?).", exc_info=True)
            return False
        except IOError as e:
            logging.error(f"IOError saving/reloading resume YAML at {self.yaml_location}: {e}", exc_info=True)
            return False
        except Exception as e:
            logging.error(f"Unexpected error during YAML save/reload at {self.yaml_location}: {e}", exc_info=True)
            return False

    def _handle_resume_yaml_review_and_pdf_creation(
        self, auto_open_yaml: bool, manual_review_yaml: bool,
        skip_pdf: bool, auto_open_pdf: bool
    ) -> None:
        """
        Manages YAML opening, manual review loop, and PDF generation.

        Args:
            auto_open_yaml (bool): Auto-open generated YAML.
            manual_review_yaml (bool): Wait for 'editing: false' in YAML.
            skip_pdf (bool): If True, skip PDF steps.
            auto_open_pdf (bool): Auto-open generated PDF.
        """
        if not self.yaml_location or not os.path.exists(self.yaml_location):
            logging.error(f"Resume YAML not found at {self.yaml_location}. Cannot review or create PDF.")
            return

        if auto_open_yaml:
            try:
                logging.info(f"Attempting to open resume YAML for review: {self.yaml_location}")
                command_parts = config.OPEN_FILE_COMMAND.split() if isinstance(config.OPEN_FILE_COMMAND, str) else config.OPEN_FILE_COMMAND
                subprocess.run(command_parts + [self.yaml_location], check=True)
            except FileNotFoundError:
                logging.error(f"Open command '{config.OPEN_FILE_COMMAND}' not found.")
            except subprocess.CalledProcessError as e:
                logging.error(f"Command to open YAML '{self.yaml_location}' failed: {e}", exc_info=True)
            except Exception as e:
                logging.error(f"Unexpected error opening YAML {self.yaml_location}: {e}", exc_info=True)

        if manual_review_yaml:
            logging.info(f"Manual review for {self.yaml_location}. Waiting for 'editing: false'.")
            try:
                current_yaml_data = utils.read_yaml(filename=self.yaml_location)
                while isinstance(current_yaml_data, dict) and current_yaml_data.get("editing", False):
                    logging.info(f"Resume at {self.yaml_location} 'editing: true'. Waiting for manual changes (set 'editing: false' to proceed).")
                    time.sleep(10)
                    current_yaml_data = utils.read_yaml(filename=self.yaml_location)
                    if current_yaml_data is None:
                        logging.error(f"{self.yaml_location} unreadable/empty during review. Aborting.")
                        return
                self.resume_yaml = current_yaml_data
                logging.info(f"Manual review of {self.yaml_location} complete.")
            except FileNotFoundError:
                logging.error(f"Resume YAML {self.yaml_location} disappeared during review.", exc_info=True)
                return
            except IOError as e:
                logging.error(f"IOError reading {self.yaml_location} during review: {e}", exc_info=True)
                return
            except Exception as e:
                logging.error(f"Unexpected error with {self.yaml_location} during review: {e}", exc_info=True)
                return

        if skip_pdf:
            logging.info("PDF creation skipped by configuration.")
        else:
            logging.info("Proceeding with PDF creation...")
            pdf_gen_instance = PDFGenerator()
            current_data_for_pdf = self.resume_yaml
            if not isinstance(current_data_for_pdf, dict) or not current_data_for_pdf:
                logging.warning(f"self.resume_yaml invalid/empty. Reloading from {self.yaml_location} for PDF.")
                current_data_for_pdf = utils.read_yaml(filename=self.yaml_location)
            if not isinstance(current_data_for_pdf, dict) or not current_data_for_pdf:
                logging.error(f"Failed to load valid data from {self.yaml_location} for PDF. Skipping PDF.")
                return
            generated_pdf_filepath = pdf_gen_instance.create_pdf(
                resume_data=current_data_for_pdf,
                job_data_location=self.job_data_location,
                auto_open=auto_open_pdf
            )
            if generated_pdf_filepath:
                logging.info(f"PDFGenerator done. PDF at: {generated_pdf_filepath}")
            else:
                logging.warning(f"PDFGenerator failed for resume at {self.yaml_location}.")

    def _create_tailored_resume_in_background(
        self, background_runner: Optional['BackgroundRunner'] = None
    ) -> None:
        """
        Internal: creates tailored resume in background (LLM enhancements, YAML save).
        No manual review or PDF generation. Called by static background method.

        Args:
            background_runner (Optional[BackgroundRunner]): BackgroundRunner instance for logging.
                                                        Uses global `logging` if None.
        """
        from .background_runner import BackgroundRunner # Ensure local scope for type if needed
        logger = background_runner.logger if background_runner and hasattr(background_runner, 'logger') else logging
        if not self.job_data_location:
            logger.error(f"Job data location not set for URL '{self.url}'. Cannot run background tailoring.")
            return
        if not self.resume:
            logger.error(f"Base resume data not loaded for URL '{self.url}'. Cannot run background tailoring.")
            return
        logger.info(f"Starting background resume enhancement for URL: {self.url}...")
        self._enhance_resume_content_with_llm()
        if self._save_tailored_resume_to_yaml():
            logger.info(f"Tailored resume YAML saved for {self.url} at {self.yaml_location} in background.")
        else:
            logger.error(f"Failed to save resume YAML for {self.url} in background at {self.yaml_location}.")

    @staticmethod
    def create_draft_tailored_resumes_in_background(background_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Creates and runs `ResumeImprover` instances for multiple job configs in background.

        Each config initializes a `ResumeImprover` (downloads/parses job post), then its
        `_create_tailored_resume_in_background` method is queued for async LLM enhancements
        and YAML saving.

        Args:
            background_configs (List[Dict[str, Any]]): List of job configs. Required keys:
                "url" (str), "resume_location" (str). Optional: "llm_kwargs" (dict).

        Returns:
            Dict[str, Any]: {"ResumeImprovers": List[ResumeImprover], "background_runner": BackgroundRunner}
        """
        from .background_runner import BackgroundRunner # Local import to avoid circular if used at top level
        output_results: Dict[str, Any] = {"ResumeImprovers": [], "background_runner": BackgroundRunner()}
        runner = output_results["background_runner"]

        def task_function_for_background(
            config_dict: Dict[str, Any], improver_instance: "ResumeImprover",
            bg_runner_logger: logging.Logger
            ) -> None:
            """Wrapper for background execution."""
            try:
                if not improver_instance.job_data_location or not improver_instance.resume:
                    bg_runner_logger.error(f"Skipping background task for {improver_instance.url} due to incomplete init.")
                    return
                # Pass the runner instance itself for logging context if its methods expect it
                improver_instance._create_tailored_resume_in_background(background_runner=runner) # type: ignore
                bg_runner_logger.info(f"Background task for {improver_instance.url} completed processing.")
            except Exception as e:
                bg_runner_logger.error(f"Error in background task for URL {config_dict.get('url', 'N/A')}: {e}", exc_info=True)

        for i, job_config in enumerate(background_configs):
            url = job_config.get("url")
            resume_loc = job_config.get("resume_location")
            llm_kwargs_for_instance = job_config.get("llm_kwargs", {})
            if not url or not resume_loc:
                runner.logger.error(f"Skipping config index {i}: missing 'url' or 'resume_location'. {job_config}")
                continue
            runner.logger.info(f"Initializing ResumeImprover for background: URL {url}, Resume {resume_loc}")
            try:
                improver_instance = ResumeImprover(url=url, resume_location=resume_loc, llm_kwargs=llm_kwargs_for_instance)
                output_results["ResumeImprovers"].append(improver_instance)
                runner.run_in_background(task_function_for_background, job_config, improver_instance, runner.logger)
                runner.logger.info(f"Queued background task for URL: {url}")
            except Exception as e:
                runner.logger.error(f"Failed to init/queue ResumeImprover for config {i} (URL: {url}): {e}", exc_info=True)
        return output_results

    def _get_formatted_chain_inputs(self, chain: RunnableSequence, section: Optional[Union[Dict[str, Any], str]] = None) -> Dict[str, Any]:
        """
        Prepares input dictionary for a LangChain runnable based on its schema.

        Aggregates data from instance attributes (`self.__dict__`), `self.parsed_job`,
        and the optional `section` argument. Uses `chain_formatter` for final formatting.

        Args:
            chain (RunnableSequence): The LangChain runnable.
            section (Optional[Union[Dict[str, Any], str]]): Specific data section for context.

        Returns:
            Dict[str, Any]: Inputs for the chain. Empty if schema lookup fails.

        Raises:
            AttributeError: If chain or its schema is malformed.
        """
        input_data_pool: Dict[str, Any] = {}
        if self.parsed_job and isinstance(self.parsed_job, dict):
            input_data_pool.update(self.parsed_job)
        input_data_pool.update(self.__dict__)
        if section is not None:
            input_data_pool["section_content_for_llm"] = section

        formatted_inputs: Dict[str, Any] = {}
        try:
            if not hasattr(chain, "get_input_schema") or not callable(chain.get_input_schema):
                raise AttributeError("Chain missing 'get_input_schema' method.")
            input_schema_obj = chain.get_input_schema()
            if not hasattr(input_schema_obj, "schema") or not callable(input_schema_obj.schema):
                raise AttributeError("Chain's input_schema missing 'schema' method.")
            schema_dict = input_schema_obj.schema()
            if not isinstance(schema_dict, dict):
                raise AttributeError(f"Chain's schema() returned {type(schema_dict)}, not dict.")
            required_input_keys = schema_dict.get("required", [])
            if not required_input_keys:
                logging.warning("Chain's input schema has no 'required' keys.")

            for key in required_input_keys:
                value_to_format = input_data_pool.get(key)
                # Prioritize section_content_for_llm if the key is 'section'
                if key == "section" and "section_content_for_llm" in input_data_pool:
                    value_to_format = input_data_pool["section_content_for_llm"]
                formatted_inputs[key] = chain_formatter(key, value_to_format)
        except AttributeError as e:
            logging.error(f"Critical error with chain schema: {e}.", exc_info=True)
            raise
        except Exception as e:
            key_in_error = locals().get('key', "unknown")
            logging.error(f"Error formatting chain inputs for key '{key_in_error}': {e}", exc_info=True)
            return {}
        return formatted_inputs

    def _chain_updater(
        self, prompt_template_messages: List[Any],
        output_pydantic_object: Type[Any], # Expects a Pydantic BaseModel class
        **llm_specific_kwargs: Any
    ) -> RunnableSequence:
        """
        Creates a LangChain RunnableSequence with structured Pydantic output.

        Args:
            prompt_template_messages (List[Any]): Messages for ChatPromptTemplate.
            output_pydantic_object (Type[Any]): Pydantic model for output parsing.
            **llm_specific_kwargs: Args for `create_llm`, merged with `self.llm_kwargs`.

        Returns:
            RunnableSequence: The constructed LangChain runnable.

        Raises:
            Exception: From `create_llm` or LangChain component instantiation.
        """
        try:
            chat_prompt = ChatPromptTemplate(messages=prompt_template_messages)
            final_llm_args = {**self.llm_kwargs, **llm_specific_kwargs}
            llm_instance = create_llm(**final_llm_args)
            langchain_runnable = chat_prompt | llm_instance.with_structured_output(schema=output_pydantic_object)
            return langchain_runnable
        except Exception as e:
            logging.error(f"Failed to create LLM chain for {output_pydantic_object.__name__}: {e}", exc_info=True)
            raise

    def _get_degrees(self, resume_data_dict: Dict[str, Any]) -> List[str]:
        """
        Extracts a flat list of degree names from the 'education' section of resume data.

        Args:
            resume_data_dict (Dict[str, Any]): Resume data (e.g., `self.resume`).

        Returns:
            List[str]: Flat list of degree names. Empty if none found or data malformed.
        """
        if not isinstance(resume_data_dict, dict) or "education" not in resume_data_dict:
            logging.debug("Resume data invalid or 'education' missing for degree extraction.")
            return []
        all_found_degree_names: List[str] = []
        education_entries = resume_data_dict.get("education", [])
        if not isinstance(education_entries, list):
            logging.warning("'education' section is not a list. Cannot extract degrees.")
            return []
        for edu_entry in education_entries:
            if isinstance(edu_entry, dict) and "degrees" in edu_entry:
                degrees_list_in_entry = edu_entry["degrees"]
                if isinstance(degrees_list_in_entry, list):
                    for degree_item in degrees_list_in_entry:
                        if isinstance(degree_item, dict) and "names" in degree_item:
                            names_field = degree_item["names"]
                            if isinstance(names_field, list):
                                all_found_degree_names.extend(str(n) for n in names_field if isinstance(n, str))
                            elif isinstance(names_field, str):
                                all_found_degree_names.append(names_field)
                            else:
                                logging.debug(f"Degree 'names' not str/list: {names_field} in {edu_entry.get('institution', 'N/A')}")
                        else:
                            logging.debug(f"Degree item not dict or no 'names': {degree_item} in {edu_entry.get('institution', 'N/A')}")
                else:
                     logging.debug(f"'degrees' not list: {degrees_list_in_entry} in {edu_entry.get('institution', 'N/A')}")
            else:
                logging.debug(f"Education entry not dict or no 'degrees': {edu_entry}")
        if not all_found_degree_names:
            logging.info("No degree names found in resume education.")
        return all_found_degree_names

    def _combine_skills_in_category(self, target_skill_list: List[str], skills_to_add: List[str]) -> None:
        """
        Combines `skills_to_add` into `target_skill_list` (in-place), case-insensitively.

        Args:
            target_skill_list (List[str]): List to extend. Modified in-place.
            skills_to_add (List[str]): Skills to add.
        """
        existing_lowercase = {skill.lower() for skill in target_skill_list if isinstance(skill, str)}
        for new_skill in skills_to_add:
            if isinstance(new_skill, str) and new_skill.strip():
                if new_skill.lower() not in existing_lowercase:
                    target_skill_list.append(new_skill)
                    existing_lowercase.add(new_skill.lower())

    def _combine_skill_lists(self, master_skills_list: List[Dict[str, Any]], new_skills_data: List[Dict[str, Any]]) -> None:
        """
        Merges `new_skills_data` into `master_skills_list` (in-place).
        Combines skills under same category (case-insensitive) and adds new categories.

        Args:
            master_skills_list (List[Dict[str, Any]]): Primary list of skill categories.
            new_skills_data (List[Dict[str, Any]]): New skill categories to merge.
        """
        if not isinstance(new_skills_data, list) or not new_skills_data:
            logging.debug("No new skills data to combine.")
            return
        category_map: Dict[str, int] = {}
        for i, entry in enumerate(master_skills_list):
            if isinstance(entry, dict) and isinstance(entry.get("category"), str) and isinstance(entry.get("skills"), list):
                category_map[entry["category"].lower()] = i
            else:
                logging.warning(f"Malformed master skill entry at index {i}: {entry}")
        for new_entry in new_skills_data:
            if not (isinstance(new_entry, dict) and isinstance(new_entry.get("category"), str) and isinstance(new_entry.get("skills"), list)):
                logging.warning(f"Skipping malformed new skill entry: {new_entry}")
                continue
            cat_name_lower = new_entry["category"].lower()
            new_skills = [s for s in new_entry["skills"] if isinstance(s, str) and s.strip()]
            if not new_skills: continue
            if cat_name_lower in category_map:
                idx = category_map[cat_name_lower]
                if isinstance(master_skills_list[idx].get("skills"), list):
                    self._combine_skills_in_category(master_skills_list[idx]["skills"], new_skills)
                else: # Should not happen if master_skills_list items are well-formed
                    logging.warning(f"Master skill category '{master_skills_list[idx]['category']}' missing 'skills' list. Overwriting.")
                    master_skills_list[idx]["skills"] = new_skills
            else:
                master_skills_list.append({"category": new_entry["category"], "skills": new_skills})
                category_map[cat_name_lower] = len(master_skills_list) - 1

    def rewrite_section(self, section_data_to_rewrite: Union[Dict[str, Any], str], **llm_chain_kwargs: Any) -> List[str]:
        """
        Rewrites a resume section using an LLM to get highlighted bullet points.

        Args:
            section_data_to_rewrite (Union[Dict[str, Any], str]): Section content (dict or string).
            **llm_chain_kwargs: Args for LLM chain setup.

        Returns:
            List[str]: Rewritten highlights. Empty list on failure or empty input.
        """
        if not section_data_to_rewrite:
            logging.warning("Empty section data for rewrite. Returning empty list.")
            return []
        try:
            llm_chain = self._chain_updater(Prompts.lookup["SECTION_HIGHLIGHTER"], ResumeSectionHighlighterOutput, **llm_chain_kwargs)
            chain_inputs = self._get_formatted_chain_inputs(chain=llm_chain, section=section_data_to_rewrite)
            if not chain_inputs:
                 logging.warning(f"Inputs for section rewrite failed: {str(section_data_to_rewrite)[:100]}... Returning empty.")
                 return []
            llm_response = llm_chain.invoke(chain_input_dict)
            if not isinstance(llm_response, ResumeSectionHighlighterOutput) or not isinstance(llm_response.final_answer, list):
                logging.warning(f"LLM section rewrite output unexpected: {str(section_data_to_rewrite)[:100]}...")
                return []
            highlights: List[Dict[str, Any]] = []
            for item in llm_response.final_answer: # item can be ResumeSectionHighlight or dict
                if isinstance(item, ResumeSectionHighlight):
                    highlights.append({'highlight': item.highlight, 'relevance': item.relevance})
                elif isinstance(item, dict) and 'relevance' in item and isinstance(item.get('highlight'), str):
                    highlights.append(item)
                else:
                    logging.warning(f"Malformed item in LLM final_answer for section rewrite: {item}.")
            sorted_highlights = sorted(highlights, key=lambda d: d.get("relevance", 0) * -1)
            return [str(h["highlight"]) for h in sorted_highlights if h.get("highlight")]
        except AttributeError as e:
            logging.error(f"AttributeError in rewrite_section (bad chain?): {e}", exc_info=True)
        except Exception as e:
            logging.error(f"Error rewriting section '{str(section_data_to_rewrite)[:100]}...': {e}", exc_info=True)
        return []

    def rewrite_unedited_experiences(self, **llm_chain_kwargs: Any) -> List[Dict[str, Any]]:
        """
        Rewrites 'highlights' for each experience in `self.experiences` via LLM.

        Args:
            **llm_chain_kwargs: Args for LLM chain, passed to `rewrite_section`.

        Returns:
            List[Dict[str, Any]]: Experiences with potentially updated 'highlights'.
                                  Original highlights retained on failure for an item.
        """
        if not self.experiences or not isinstance(self.experiences, list):
            logging.info("No experiences or invalid format; skipping rewrite.")
            return self.experiences if isinstance(self.experiences, list) else []
        updated_list: List[Dict[str, Any]] = []
        for i, exp in enumerate(self.experiences):
            if not isinstance(exp, dict):
                logging.warning(f"Skipping non-dict experience at index {i}: {exp}")
                updated_list.append(exp)
                continue
            exp_copy = exp.copy()
            original_highlights = list(exp_copy.get("highlights", []))
            new_highlights = self.rewrite_section(section_data_to_rewrite=exp_copy, **llm_chain_kwargs)
            exp_name = exp_copy.get('titles', [{'name': f'Entry {i}'}])[0].get('name', f'Entry {i}')
            if new_highlights:
                exp_copy["highlights"] = new_highlights
                logging.info(f"Rewrote highlights for experience: {exp_name}")
            else:
                logging.warning(f"Rewrite for experience '{exp_name}' failed/empty. Keeping original highlights.")
                exp_copy["highlights"] = original_highlights
            updated_list.append(exp_copy)
        return updated_list

    def rewrite_unedited_projects(self, **llm_chain_kwargs: Any) -> List[Dict[str, Any]]:
        """
        Rewrites 'highlights' for each project in `self.projects` via LLM.

        Args:
            **llm_chain_kwargs: Args for LLM chain, passed to `rewrite_section`.

        Returns:
            List[Dict[str, Any]]: Projects with potentially updated 'highlights'.
                                  Original highlights retained on failure for an item.
        """
        if not self.projects or not isinstance(self.projects, list):
            logging.info("No projects or invalid format; skipping rewrite.")
            return self.projects if isinstance(self.projects, list) else []
        updated_list: List[Dict[str, Any]] = []
        for i, proj in enumerate(self.projects):
            if not isinstance(proj, dict):
                logging.warning(f"Skipping non-dict project at index {i}: {proj}")
                updated_list.append(proj)
                continue
            proj_copy = proj.copy()
            original_highlights = list(proj_copy.get("highlights", []))
            new_highlights = self.rewrite_section(section_data_to_rewrite=proj_copy, **llm_chain_kwargs)
            proj_name = proj_copy.get('name', f'Entry {i}')
            if new_highlights:
                proj_copy["highlights"] = new_highlights
                logging.info(f"Rewrote highlights for project: {proj_name}")
            else:
                logging.warning(f"Rewrite for project '{proj_name}' failed/empty. Keeping original highlights.")
                proj_copy["highlights"] = original_highlights
            updated_list.append(proj_copy)
        return updated_list

    def extract_matched_skills(self, **llm_chain_kwargs: Any) -> Optional[List[Dict[str, Any]]]:
        """
        Extracts skills from job post, matches with resume via LLM, combines with `self.skills`.

        Args:
            **llm_chain_kwargs: Args for LLM chain setup.

        Returns:
            Optional[List[Dict[str, Any]]]: New list of skill categories.
                                  Returns copy of `self.skills` or empty list on failure/no new skills.
                                  None if `self.skills` was None and critical error occurs.
        """
        try:
            llm_chain = self._chain_updater(Prompts.lookup["SKILLS_MATCHER"], ResumeSkillsMatcherOutput, **llm_chain_kwargs)
            chain_inputs = self._get_formatted_chain_inputs(chain=llm_chain)
            if not chain_inputs:
                 logging.warning("Inputs for skill matching LLM failed. Using existing skills.")
                 return [s.copy() for s in self.skills] if isinstance(self.skills, list) else ([] if self.skills is None else []) # type: ignore
            llm_response = llm_chain.invoke(chain_inputs)
            if not isinstance(llm_response, ResumeSkillsMatcherOutput) or not isinstance(llm_response.final_answer, ResumeSkills):
                logging.warning("LLM skill matching output unexpected. Using existing skills.")
                return [s.copy() for s in self.skills] if isinstance(self.skills, list) else ([] if self.skills is None else []) # type: ignore

            llm_skills_data = llm_response.final_answer
            formatted_llm_skills: List[Dict[str, Any]] = []
            if llm_skills_data.technical_skills:
                formatted_llm_skills.append({"category": "Technical", "skills": [str(s) for s in llm_skills_data.technical_skills if isinstance(s,str) and s.strip()]})
            if llm_skills_data.non_technical_skills:
                formatted_llm_skills.append({"category": "Non-technical", "skills": [str(s) for s in llm_skills_data.non_technical_skills if isinstance(s,str) and s.strip()]})
            formatted_llm_skills = [cat for cat in formatted_llm_skills if cat.get("skills")]

            if not formatted_llm_skills:
                logging.info("LLM found no new skills. Returning original skills.")
                return [s.copy() for s in self.skills] if isinstance(self.skills, list) else ([] if self.skills is None else []) # type: ignore

            current_skills_copy: List[Dict[str, Any]] = []
            if isinstance(self.skills, list):
                for cat in self.skills:
                    if isinstance(cat, dict) and "category" in cat and "skills" in cat and isinstance(cat["skills"], list):
                        current_skills_copy.append({"category": cat["category"], "skills": list(cat["skills"])})
                    else: logging.warning(f"Malformed skill category in self.skills: {cat}")
            self._combine_skill_lists(current_skills_copy, formatted_llm_skills)
            logging.info("Combined LLM-extracted skills with existing skills.")
            return current_skills_copy
        except AttributeError as e:
            logging.error(f"AttributeError in skill extraction (bad chain?): {e}", exc_info=True)
        except Exception as e:
            logging.error(f"Error extracting skills with LLM: {e}", exc_info=True)
        return [s.copy() for s in self.skills] if isinstance(self.skills, list) else ([] if self.skills is None else []) # type: ignore

    def write_objective(self, **llm_chain_kwargs: Any) -> Optional[str]:
        """
        Generates a resume objective statement using an LLM.

        Args:
            **llm_chain_kwargs: Args for LLM chain setup.

        Returns:
            Optional[str]: Generated objective. Original `self.objective` on failure/empty output.
                           None if original was None and LLM fails.
        """
        try:
            llm_chain = self._chain_updater(Prompts.lookup["OBJECTIVE_WRITER"], ResumeSummarizerOutput, **llm_chain_kwargs)
            chain_inputs = self._get_formatted_chain_inputs(chain=llm_chain)
            if not chain_inputs:
                 logging.warning("Inputs for objective LLM failed. Using original objective.")
                 return str(self.objective) if self.objective is not None else None
            llm_response = llm_chain.invoke(chain_inputs)
            if not isinstance(llm_response, ResumeSummarizerOutput) or not isinstance(llm_response.final_answer, str):
                logging.warning("LLM objective output unexpected. Using original objective.")
                return str(self.objective) if self.objective is not None else None
            new_objective = llm_response.final_answer.strip()
            if not new_objective:
                logging.info("LLM returned empty objective. Keeping original.")
                return str(self.objective) if self.objective is not None else None
            logging.info("Generated new objective with LLM.")
            return new_objective
        except AttributeError as e:
            logging.error(f"AttributeError in objective writing (bad chain?): {e}", exc_info=True)
        except Exception as e:
            logging.error(f"Error writing objective with LLM: {e}", exc_info=True)
        return str(self.objective) if self.objective is not None else None

    def suggest_improvements(self, **llm_chain_kwargs: Any) -> Optional[List[str]]:
        """
        Generates a list of overall resume improvement suggestions using an LLM.

        Args:
            **llm_chain_kwargs: Args for LLM chain setup.

        Returns:
            Optional[List[str]]: Improvement suggestions. None on failure or no valid suggestions.
        """
        try:
            llm_chain = self._chain_updater(Prompts.lookup["IMPROVER"], ResumeImproverOutput, **llm_chain_kwargs)
            chain_inputs = self._get_formatted_chain_inputs(chain=llm_chain)
            if not chain_inputs:
                 logging.warning("Inputs for improvements LLM failed. No suggestions.")
                 return None
            llm_response = llm_chain.invoke(chain_inputs)
            if not isinstance(llm_response, ResumeImproverOutput) or not isinstance(llm_response.final_answer, list):
                logging.warning("LLM improvements output unexpected. No suggestions.")
                return None
            suggestions: List[str] = []
            for section_improvement in llm_response.final_answer: # final_answer is List[ResumeImprovements]
                if isinstance(section_improvement, ResumeImprovements) and section_improvement.improvements:
                    for text in section_improvement.improvements:
                        if isinstance(text, str) and text.strip():
                            suggestions.append(f"[{section_improvement.section.upper()}]: {text.strip()}")
            if not suggestions:
                logging.info("LLM returned no actionable improvement suggestions.")
                return None
            logging.info(f"Generated {len(suggestions)} improvement suggestions.")
            return suggestions
        except AttributeError as e:
            logging.error(f"AttributeError in suggest_improvements (bad chain?): {e}", exc_info=True)
        except Exception as e:
            logging.error(f"Error suggesting improvements with LLM: {e}", exc_info=True)
        return None

    def finalize_resume_data(self) -> Dict[str, Any]:
        """
        Constructs the final resume data dictionary from current instance attributes.

        Returns:
            Dict[str, Any]: Dictionary of all resume sections, with defaults for missing parts.
        """
        final_data = {
            "basic": self.basic_info if isinstance(self.basic_info, dict) else {},
            "objective": self.objective if isinstance(self.objective, str) else "",
            "education": self.education if isinstance(self.education, list) else [],
            "experiences": self.experiences if isinstance(self.experiences, list) else [],
            "projects": self.projects if isinstance(self.projects, list) else [],
            "skills": self.skills if isinstance(self.skills, list) else [],
        }
        return final_data

    # The create_pdf method was moved to pdf_generation.pdf_generator.PDFGenerator.
    # ResumeImprover calls PDFGenerator().create_pdf(...) in
    # _handle_resume_yaml_review_and_pdf_creation.
```
