import os
import time
import subprocess
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
import uuid
import requests
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_core.output_parsers import StrOutputParser
from ..models.resume import (
    ResumeImproverOutput,
    ResumeSkillsMatcherOutput,
    ResumeSummarizerOutput,
    ResumeSectionHighlighterOutput,
)
from .. import utils
from .. import config
from .langchain_helpers import *
from ..prompts import Prompts
from ..models.job_post import JobPost
from ..pdf_generation import ResumePDFGenerator
import concurrent.futures
from fp.fp import FreeProxy
import time
from ..config import config
from .background_runner import BackgroundRunner


class ResumeImprover:

    def __init__(self, url, resume_location=None, llm_kwargs: dict = None):
        """Initialize ResumeImprover with the job post URL and optional resume location.

        Args:
            url (str): The URL of the job post.
            resume_location (str, optional): The file path to the resume. Defaults to None.
            llm_kwargs (dict, optional): Additional keyword arguments for the language model. Defaults to None.
        """
        super().__init__()
        self.job_post_html_data = None
        self.job_post_raw = None
        self.resume = None
        self.resume_yaml = None
        self.job_post = None
        self.parsed_job = None
        self.llm_kwargs = llm_kwargs or {}
        self.editing = False
        self.clean_url = None
        self.job_data_location = None
        self.yaml_loc = None
        self.url = url
        self.download_and_parse_job_post()
        self.resume_location = resume_location or config.DEFAULT_RESUME_PATH
        self._update_resume_fields()

    def _update_resume_fields(self):
        """Update the resume fields based on the current resume location."""
        utils.check_resume_format(self.resume_location)
        self.resume = utils.read_yaml(filename=self.resume_location)
        self.degrees = self._get_degrees(self.resume)
        self.basic_info = utils.get_dict_field(field="basic", data_dict=self.resume)
        self.education = utils.get_dict_field(field="education", data_dict=self.resume)
        self.experiences = utils.get_dict_field(
            field="experiences", data_dict=self.resume
        )
        self.projects = utils.get_dict_field(field="projects", data_dict=self.resume)
        self.skills = utils.get_dict_field(field="skills", data_dict=self.resume)
        self.objective = utils.get_dict_field(field="objective", data_dict=self.resume)

    def update_resume(self, new_resume_location):
        """Update the resume location and refresh the dependent fields.

        Args:
            new_resume_location (str): The new file path to the resume.
        """
        self.resume_location = new_resume_location
        self._update_resume_fields()

    def _extract_html_data(self):
        """Extract text content from HTML, removing all HTML tags.

        Raises:
            Exception: If HTML data extraction fails.
        """
        try:
            soup = BeautifulSoup(self.job_post_html_data, "html.parser")
            self.job_post_raw = soup.get_text(separator=" ", strip=True)
        except Exception as e:
            config.logger.error(f"Failed to extract HTML data: {e}")
            raise

    def _download_url(self, url=None):
        """Download the content of the URL and return it as a string.

        Args:
            url (str, optional): The URL to download. Defaults to None.

        Returns:
            bool: True if download was successful, False otherwise.
        """
        if url:
            self.url = url

        max_retries = config.MAX_RETRIES
        backoff_factor = config.BACKOFF_FACTOR
        use_proxy = False

        for attempt in range(max_retries):
            try:
                proxies = None
                if use_proxy:
                    proxy = FreeProxy(rand=True).get()
                    proxies = {"http": proxy, "https": proxy}

                response = requests.get(
                    self.url, headers=config.REQUESTS_HEADERS, proxies=proxies
                )
                response.raise_for_status()
                self.job_post_html_data = response.text
                return True

            except requests.RequestException as e:
                if response.status_code == 429:
                    config.logger.warning(
                        f"Rate limit exceeded. Retrying in {backoff_factor * 2 ** attempt} seconds..."
                    )
                    time.sleep(backoff_factor * 2**attempt)
                    use_proxy = True
                else:
                    config.logger.error(f"Failed to download URL {self.url}: {e}")
                    return False

        config.logger.error(f"Exceeded maximum retries for URL {self.url}")
        return False

    def download_and_parse_job_post(self, url=None):
        """Download and parse the job post from the provided URL.

        Args:
            url (str, optional): The URL of the job post. Defaults to None.
        """
        if url:
            self.url = url
        self._download_url()
        self._extract_html_data()
        self.job_post = JobPost(self.job_post_raw)
        self.parsed_job = self.job_post.parse_job_post(verbose=False)
        try:
            filename = self.parsed_job["company"] + "_" + self.parsed_job["job_title"]
            filename = filename.replace(" ", "_")
        except KeyError:
            if "://" in self.url:
                filename = self.url.split("://")[1]
            else:
                filename = self.url
            url_paths = filename.split("/")
            filename = url_paths[0]
            if len(url_paths) > 1:
                filename = filename + "." + url_paths[-1]
        self.clean_url = filename
        filepath = os.path.join(config.DATA_PATH, self.clean_url)
        self.job_data_location = filepath
        os.makedirs(self.job_data_location, exist_ok=True)
        utils.write_yaml(
            self.parsed_job, filename=os.path.join(self.job_data_location, "job.yaml")
        )

    def parse_raw_job_post(self, raw_html):
        """Download and parse the job post from the provided URL.

        Args:
            url (str, optional): The URL of the job post. Defaults to None.
        """
        self.job_post_html_data = raw_html
        self._extract_html_data()
        self.job_post = JobPost(self.job_post_raw)
        self.parsed_job = self.job_post.parse_job_post(verbose=False)
        try:
            filename = self.parsed_job["company"] + "_" + self.parsed_job["job_title"]
            filename = filename.replace(" ", "_")
        except KeyError:
            if "://" in self.url:
                filename = self.url.split("://")[1]
            else:
                filename = self.url
            url_paths = filename.split("/")
            filename = url_paths[0]
            if len(url_paths) > 1:
                filename = filename + "." + url_paths[-1]
        self.clean_url = filename
        filepath = os.path.join(config.DATA_PATH, self.clean_url)
        self.job_data_location = filepath
        os.makedirs(self.job_data_location, exist_ok=True)
        utils.write_yaml(
            self.parsed_job, filename=os.path.join(self.job_data_location, "job.yaml")
        )

    def create_draft_tailored_resume(
        self, auto_open=True, manual_review=True, skip_pdf_create=False
    ):
        """Run a full review of the resume against the job post.

        Args:
            auto_open (bool, optional): Whether to automatically open the generated resume. Defaults to True.
            manual_review (bool, optional): Whether to wait for manual review. Defaults to True.
        """
        config.logger.info("Extracting matched skills...")
        self.skills = self.extract_matched_skills(verbose=False)
        config.logger.info("Writing objective...")
        self.objective = self.write_objective(verbose=False)
        config.logger.info("Updating bullet points...")
        self.experiences = self.rewrite_unedited_experiences(verbose=False)
        config.logger.info("Updating projects...")
        self.projects = self.rewrite_unedited_projects(verbose=False)
        config.logger.info("Done updating...")
        self.yaml_loc = os.path.join(self.job_data_location, "resume.yaml")
        resume_dict = dict(
            editing=True,
            basic=self.basic_info,
            objective=self.objective,
            education=self.education,
            experiences=self.experiences,
            projects=self.projects,
            skills=self.skills,
        )
        utils.write_yaml(resume_dict, filename=self.yaml_loc)
        self.resume_yaml = utils.read_yaml(filename=self.yaml_loc)
        if auto_open:
            subprocess.run(config.OPEN_FILE_COMMAND.split(" ") + [self.yaml_loc])
        while manual_review and utils.read_yaml(filename=self.yaml_loc)["editing"]:
            time.sleep(5)
        config.logger.info("Saving PDF")
        if not skip_pdf_create:
            self.create_pdf(auto_open=auto_open)

    pass

    def _create_tailored_resume_in_background(
        self, auto_open=True, manual_review=True, background_runner=None
    ):
        """Run a full review of the resume against the job post.

        Args:
            auto_open (bool, optional): Whether to automatically open the generated resume. Defaults to True.
            manual_review (bool, optional): Whether to wait for manual review. Defaults to True.
        """
        if background_runner is not None:
            logger = background_runner.logger
        else:
            logger = config.logger
        logger.info("Extracting matched skills...")
        self.skills = self.extract_matched_skills(verbose=False)
        logger.info("Writing objective...")
        self.objective = self.write_objective(verbose=False)
        logger.info("Updating bullet points...")
        self.experiences = self.rewrite_unedited_experiences(verbose=False)
        logger.info("Updating projects...")
        self.projects = self.rewrite_unedited_projects(verbose=False)
        logger.info("Done updating...")
        self.yaml_loc = os.path.join(self.job_data_location, "resume.yaml")
        resume_dict = dict(
            editing=True,
            basic=self.basic_info,
            objective=self.objective,
            education=self.education,
            experiences=self.experiences,
            projects=self.projects,
            skills=self.skills,
        )
        utils.write_yaml(resume_dict, filename=self.yaml_loc)
        self.resume_yaml = utils.read_yaml(filename=self.yaml_loc)

    def create_draft_tailored_resumes_in_background(background_configs: List[dict]):
        """Run 'create_draft_tailored_resume' for multiple configurations in the background.

        Args:
            background_configs (List[dict]): List of configurations for creating draft tailored resumes.
                Each configuration dictionary should have the following keys:
                - url (str): The URL of the job posting.
                - resume_location (str): The file path to the resume to be tailored.
                - auto_open (bool, optional): Whether to automatically open the generated resume. Defaults to True.
                - manual_review (bool, optional): Whether to wait for manual review. Defaults to True.
        """
        output = {}
        output["ResumeImprovers"] = []
        output["background_runner"] = BackgroundRunner()

        def run_config(background_config, resume_improver):
            try:
                resume_improver.download_and_parse_job_post()
                resume_improver._create_tailored_resume_in_background(
                    auto_open=background_config.get("auto_open", True),
                    manual_review=background_config.get("manual_review", True),
                )
            except Exception as e:
                output["background_runner"].logger.error(
                    f"An error occurred with config {config}: {e}"
                )

        for background_config in background_configs:
            output["ResumeImprovers"].append(
                ResumeImprover(
                    url=background_config["url"],
                    resume_location=background_config.get("resume_location"),
                )
            )
            output["background_runner"].run_in_background(
                run_config, background_config, output["ResumeImprovers"][-1]
            )
        return output

    def _get_formatted_chain_inputs(self, chain, section=None):
        output_dict = {}
        raw_self_data = self.__dict__
        if section is not None:
            raw_self_data = raw_self_data.copy()
            raw_self_data["section"] = section
        for key in chain.get_input_schema().schema()["required"]:
            output_dict[key] = chain_formatter(
                key, raw_self_data.get(key) or self.parsed_job.get(key)
            )
        return output_dict

    def _chain_updater(
        self, prompt_msgs, pydantic_object, **chain_kwargs
    ) -> RunnableSequence:
        """Create a chain based on the prompt messages.

        Returns:
            RunnableSequence: The chain for highlighting resume sections, matching skills, or improving resume content.
        """
        prompt = ChatPromptTemplate(messages=prompt_msgs)
        llm = create_llm(**self.llm_kwargs)
        runnable = prompt | llm.with_structured_output(schema=pydantic_object)
        return runnable

    def _get_degrees(self, resume: dict):
        """Extract degrees from the resume.

        Args:
            resume (dict): The resume data.

        Returns:
            list: A list of degree names.
        """
        result = []
        for degrees in utils.generator_key_in_nested_dict("degrees", resume):
            for degree in degrees:
                if isinstance(degree["names"], list):
                    result.extend(degree["names"])
                elif isinstance(degree["names"], str):
                    result.append(degree["names"])
        return result

    def _combine_skills_in_category(self, l1: list[str], l2: list[str]):
        """Combine two lists of skills without duplicating lowercase entries.

        Args:
            l1 (list[str]): The first list of skills.
            l2 (list[str]): The second list of skills.
        """
        l1_lower = {i.lower() for i in l1}
        for i in l2:
            if i.lower() not in l1_lower:
                l1.append(i)

    def _combine_skill_lists(self, l1: list[dict], l2: list[dict]):
        """Combine two lists of skill categories without duplicating lowercase entries.

        Args:
            l1 (list[dict]): The first list of skill categories.
            l2 (list[dict]): The second list of skill categories.
        """
        l1_categories_lowercase = {s["category"].lower(): i for i, s in enumerate(l1)}
        for s in l2:
            if s["category"].lower() in l1_categories_lowercase:
                self._combine_skills_in_category(
                    l1[l1_categories_lowercase[s["category"].lower()]]["skills"],
                    s["skills"],
                )
            else:
                l1.append(s)

    def rewrite_section(self, section: list | str, **chain_kwargs) -> dict:
        """Rewrite a section of the resume.

        Args:
            section (list | str): The section to rewrite.
            **chain_kwargs: Additional keyword arguments for the chain.

        Returns:
            dict: The rewritten section.
        """
        chain = self._chain_updater(
            Prompts.lookup["SECTION_HIGHLIGHTER"],
            ResumeSectionHighlighterOutput,
            **chain_kwargs,
        )
        chain_inputs = self._get_formatted_chain_inputs(chain=chain, section=section)
        section_revised = chain.invoke(chain_inputs).dict()
        section_revised = sorted(
            section_revised["final_answer"], key=lambda d: d["relevance"] * -1
        )
        return [s["highlight"] for s in section_revised]

    def rewrite_unedited_experiences(self, **chain_kwargs) -> dict:
        """Rewrite unedited experiences in the resume.

        Args:
            **chain_kwargs: Additional keyword arguments for the chain.

        Returns:
            dict: The rewritten experiences.
        """
        result = []
        for exp in self.experiences:
            exp = dict(exp)
            exp["highlights"] = self.rewrite_section(section=exp, **chain_kwargs)
            result.append(exp)
        return result

    def rewrite_unedited_projects(self, **chain_kwargs) -> dict:
        """Rewrite unedited projects in the resume.

        Args:
            **chain_kwargs: Additional keyword arguments for the chain.

        Returns:
            dict: The rewritten projects.
        """
        result = []
        for exp in self.projects:
            exp = dict(exp)
            exp["highlights"] = self.rewrite_section(section=exp, **chain_kwargs)
            result.append(exp)
        return result

    def extract_matched_skills(self, **chain_kwargs) -> dict:
        """Extract matched skills from the resume and job post.

        Args:
            **chain_kwargs: Additional keyword arguments for the chain.

        Returns:
            dict: The extracted skills.
        """

        chain = self._chain_updater(
            Prompts.lookup["SKILLS_MATCHER"], ResumeSkillsMatcherOutput, **chain_kwargs
        )
        chain_inputs = self._get_formatted_chain_inputs(chain=chain)
        extracted_skills = chain.invoke(chain_inputs).dict()
        if not extracted_skills or "final_answer" not in extracted_skills:
            return None
        extracted_skills = extracted_skills["final_answer"]
        result = []
        if "technical_skills" in extracted_skills:
            result.append(
                dict(category="Technical", skills=extracted_skills["technical_skills"])
            )
        if "non_technical_skills" in extracted_skills:
            result.append(
                dict(
                    category="Non-technical",
                    skills=extracted_skills["non_technical_skills"],
                )
            )
        self._combine_skill_lists(result, self.skills)
        return result

    def write_objective(self, **chain_kwargs) -> dict:
        """Write a objective for the resume.

        Args:
            **chain_kwargs: Additional keyword arguments for the chain.

        Returns:
            dict: The written objective.
        """
        chain = self._chain_updater(
            Prompts.lookup["OBJECTIVE_WRITER"], ResumeSummarizerOutput, **chain_kwargs
        )

        chain_inputs = self._get_formatted_chain_inputs(chain=chain)
        objective = chain.invoke(chain_inputs).dict()
        if not objective or "final_answer" not in objective:
            return None
        return objective["final_answer"]

    def suggest_improvements(self, **chain_kwargs) -> dict:
        """Suggest improvements for the resume.

        Args:
            **chain_kwargs: Additional keyword arguments for the chain.

        Returns:
            dict: The suggested improvements.
        """
        chain = self._chain_updater(
            Prompts.lookup["IMPROVER"], ResumeImproverOutput, **chain_kwargs
        )
        chain_inputs = self._get_formatted_chain_inputs(chain=chain)
        improvements = chain.invoke(chain_inputs).dict()
        if not improvements or "final_answer" not in improvements:
            return None
        return improvements["final_answer"]

    def finalize(self) -> dict:
        """Finalize the resume data.

        Returns:
            dict: The finalized resume data.
        """
        return dict(
            basic=self.basic_info,
            objective=self.objective,
            education=self.education,
            experiences=self.experiences,
            projects=self.projects,
            skills=self.skills,
        )

    def create_pdf(self, auto_open=True):
        """Create a PDF of the resume.

        Args:
            auto_open (bool, optional): Whether to automatically open the generated PDF. Defaults to True.

        Returns:
            str: The file path to the generated PDF.
        """
        pdf_generator = ResumePDFGenerator()
        pdf_location = pdf_generator.generate_resume(
            job_data_location=self.job_data_location,
            data=utils.read_yaml(filename=self.yaml_loc),
        )
        if auto_open:
            subprocess.run(config.OPEN_FILE_COMMAND.split(" ") + [pdf_location])
        return pdf_location
