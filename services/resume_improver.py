import os
import time
import subprocess
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
import uuid
import requests
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from ..models.resume import (
    ResumeSkillsMatcherOutput,
    ResumeSummarizerOutput,
    ResumeBulletPointRewriterOutput,
    BulletPointImproverOutput,
)
import yaml
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

    def __init__(
        self,
        url=None,
        job_description=None,
        resume_location=None,
        llm_kwargs: dict = None,
    ):
        """Initialize ResumeImprover with the job post URL and optional resume location.

        Args:
            url (str): The URL of the job post.
            resume_location (str, optional): The file path to the resume. Defaults to None.
            llm_kwargs (dict, optional): Additional keyword arguments for the language model. Defaults to None.
        """
        super().__init__()
        self.url = url
        self.resume_location = resume_location or config.DEFAULT_RESUME_PATH
        self.job_post_html_data = None
        self.resume = None
        self.resume_yaml = None
        self.job_post_raw = None
        self.job_post = None
        self.parsed_job = None
        self.llm_kwargs = llm_kwargs or {}
        self.editing = False
        self.clean_url = None
        self.job_data_location = None
        self.yaml_loc = None
        if self.url:
            self.download_and_parse_job_post()
        elif job_description:
            self.parse_raw_job_post(raw_description=job_description)
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
                if "response" in locals() and response.status_code == 429:
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
        self.parsed_job = self.job_post.parse_job_post()
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

    def parse_raw_job_post(self, raw_html=None, raw_description=None):
        """Download and parse the job post from the provided URL.

        Args:
            url (str, optional): The URL of the job post. Defaults to None.
        """
        if raw_html:
            self.job_post_html_data = raw_html
            self._extract_html_data()
        elif raw_description:
            self.job_post_raw = raw_description
        self.job_post = JobPost(self.job_post_raw)
        self.parsed_job = self.job_post.parse_job_post()
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
        self,
        auto_open=True,
        manual_review=True,
        skip_pdf_create=False,
        background_runner=None,
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
        resume_dict = {
            "editing": True,
            "basic": self.basic_info,
            "education": self.education,
        }

        logger.info("Extracting matched skills...")
        self.skills = self.extract_matched_skills()
        if self.skills:
            resume_dict["skills"] = self.skills

        if self.objective:
            logger.info("Writing objective...")
            self.objective = self.write_objective()
            resume_dict["objective"] = self.objective
        else:
            logger.info("Objective not found; skipping objective improvement.")

        logger.info("Updating bullet points...")
        self.rewrite_unedited_experiences()
        if self.experiences:
            resume_dict["experiences"] = self.experiences

        if self.projects:
            logger.info("Updating projects...")
            self.projects = self.rewrite_unedited_projects()
            resume_dict["projects"] = self.projects
        else:
            logger.info("Projects not found; skipping projects improvement.")

        logger.info("Done updating...")
        self.yaml_loc = os.path.join(self.job_data_location, "resume.yaml")
        utils.write_yaml(resume_dict, filename=self.yaml_loc)
        self.resume_yaml = utils.read_yaml(filename=self.yaml_loc)
        if auto_open:
            subprocess.run(config.OPEN_FILE_COMMAND.split(" ") + [self.yaml_loc])
        while manual_review and utils.read_yaml(filename=self.yaml_loc)["editing"]:
            time.sleep(5)
        logger.info("Saving PDF")
        if not skip_pdf_create:
            self.create_pdf(auto_open=auto_open)

        async def create_draft_tailored_resume_async(
            self,
            auto_open=True,
            manual_review=True,
            skip_pdf_create=False,
            background_runner=None,
        ):
            return self.create_draft_tailored_resume(
                auto_open=auto_open,
                manual_review=manual_review,
                skip_pdf_create=skip_pdf_create,
                background_runner=background_runner,
            )

        @staticmethod
        def create_draft_tailored_resumes_in_background(background_configs: List[dict]):
            """Run create_draft_tailored_resume for multiple configurations in the background.

            Args:
                background_configs (List[dict]): List of configurations for creating draft tailored resumes.
                    Each configuration dictionary should have the following keys:
                    - url (str): The URL of the job posting.
                    - resume_location (str): The file path to the resume to be tailored.
                    - auto_open (bool, optional): Whether to automatically open the generated resume. Defaults to True.
                    - manual_review (bool, optional): Whether to wait for manual review. Defaults to True.
            """
            background_runner = BackgroundRunner()
            resume_improvers = []

            def run_config(background_config):
                resume_improver = ResumeImprover(
                    url=background_config["url"],
                    resume_location=background_config.get("resume_location"),
                )
                resume_improvers.append(resume_improver)
                resume_improver.download_and_parse_job_post()
                resume_improver.create_draft_tailored_resume_async(
                    auto_open=background_config.get("auto_open", True),
                    manual_review=background_config.get("manual_review", True),
                )

            for background_config in background_configs:
                background_runner.run_in_background(run_config, background_config)

            return {
                "ResumeImprovers": resume_improvers,
                "background_runner": background_runner,
            }

    def _get_formatted_chain_inputs(self, chain):
        output_dict = {}
        raw_self_data = self.__dict__
        for key in chain.get_input_schema().schema()["required"]:
            output_dict[key] = chain_formatter(
                key, raw_self_data.get(key) or self.parsed_job.get(key)
            )
        return output_dict

    def _chain_updater(self, prompt_msgs, pydantic_object) -> RunnableSequence:
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

    def rewrite_bullet_points(self, projects=False) -> dict:
        """Rewrite bullet points in the resume.

        Args:
            projects (bool): If True, update self.projects instead of self.experiences.

        Returns:
            dict: The rewritten bullet points.
        """
        bullet_point_chain = self._chain_updater(
            prompt_msgs=Prompts.lookup["BULLET_POINT_REWRITER"],
            pydantic_object=ResumeBulletPointRewriterOutput,
        )
        bullet_point_chain_inputs = self._get_formatted_chain_inputs(
            chain=bullet_point_chain
        )

        target_list = self.projects if projects else self.experiences

        for exp in target_list:
            bullet_point_chain_inputs["draft"] = format_list_as_string(
                exp["highlights"]
            )
            new_bullets = bullet_point_chain.invoke(bullet_point_chain_inputs).dict()[
                "answer"
            ]

            new_bullets = sorted(new_bullets, key=lambda d: d["relevance"] * -1)
            new_bullets = [s["highlight"] for s in new_bullets]
            exp["highlights"] = new_bullets

        with open(config.PROMPTS_YAML, "r") as file:
            raw_prompts = yaml.safe_load(file)

        prompt_template = raw_prompts["BULLET_POINT_IMPROVER"]
        new_bullets = ""
        new_tags = ""
        for i, exp in enumerate(target_list):
            bullet_point_chain_inputs[f"draft_{i}"] = format_list_as_string(
                exp["highlights"]
            )
            new_tags += f", <draft_{i}>"
            new_bullets += "\n<draft_%i>\n{draft_%i}\n</draft_%i>\n" % (i)
            for ii in range(len(prompt_template)):
                prompt_template[ii] = prompt_template[ii].replace(
                    "PUT_BULLETS_HERE", new_bullets
                )
                prompt_template[ii] = prompt_template[ii].replace(
                    "PUT_DRAFT_TAGS_HERE", f"({new_tags})"
                )
        prompt_template = Prompts.create_prompt_from_dict(prompt_template)
        reviewer_chain = self._chain_updater(
            prompt_msgs=prompt_template, pydantic_object=BulletPointImproverOutput
        )
        reviewed_bullets = reviewer_chain.invoke(bullet_point_chain_inputs).dict()
        for i, exp in enumerate(reviewed_bullets["answer"]):
            target_list[i]["highlights"] = exp["highlights"]
        return "Done!"

    def rewrite_bullet_points(self, projects=False) -> dict:
        """Rewrite bullet points in the resume.

        Args:
            projects (bool): If True, update self.projects instead of self.experiences.

        Returns:
            dict: The rewritten bullet points.
        """
        bullet_point_chain = self._chain_updater(
            prompt_msgs=Prompts.lookup["BULLET_POINT_REWRITER"],
            pydantic_object=ResumeBulletPointRewriterOutput,
        )
        bullet_point_chain_inputs = self._get_formatted_chain_inputs(
            chain=bullet_point_chain
        )

        target_list = self.projects if projects else self.experiences

        for exp in target_list:
            bullet_point_chain_inputs["draft"] = format_list_as_string(
                exp["highlights"]
            )
            new_bullets = bullet_point_chain.invoke(bullet_point_chain_inputs).dict()[
                "answer"
            ]

            new_bullets = sorted(new_bullets, key=lambda d: d["relevance"] * -1)
            new_bullets = [s["highlight"] for s in new_bullets]
            exp["highlights"] = new_bullets

        with open(config.PROMPTS_YAML, "r") as file:
            raw_prompts = yaml.safe_load(file)

        prompt_template = raw_prompts["BULLET_POINT_IMPROVER"]
        new_bullets = ""
        new_tags = ""
        for i, exp in enumerate(target_list):
            bullet_point_chain_inputs[f"draft_{i}"] = format_list_as_string(
                exp["highlights"]
            )
            new_tags += f", <draft_{i}>"
            new_bullets += "\n<draft_%i>\n{draft_%i}\n</draft_%i>\n" % (i)
            for ii in range(len(prompt_template)):
                prompt_template[ii] = prompt_template[ii].replace(
                    "PUT_BULLETS_HERE", new_bullets
                )
                prompt_template[ii] = prompt_template[ii].replace(
                    "PUT_DRAFT_TAGS_HERE", f"({new_tags})"
                )
        prompt_template = Prompts.create_prompt_from_dict(prompt_template)
        reviewer_chain = self._chain_updater(
            prompt_msgs=prompt_template, pydantic_object=BulletPointImproverOutput
        )
        reviewed_bullets = reviewer_chain.invoke(bullet_point_chain_inputs).dict()
        for i, exp in enumerate(reviewed_bullets["answer"]):
            target_list[i]["highlights"] = exp["highlights"]
        return "Done!"

    def rewrite_unedited_experiences(self) -> dict:
        """Rewrite unedited experiences in the resume.

        Returns:
            dict: The rewritten experiences.
        """
        self.rewrite_bullet_points()
        return self.experiences

    def rewrite_unedited_projects(self) -> dict:
        """Rewrite unedited projects in the resume.

        Returns:
            dict: The rewritten projects.
        """
        self.rewrite_bullet_points(projects=True)
        return self.projects

    def extract_matched_skills(self) -> dict:
        """Extract matched skills from the resume and job post.

        Returns:
            dict: The extracted skills.
        """

        chain = self._chain_updater(
            Prompts.lookup["SKILLS_MATCHER"], ResumeSkillsMatcherOutput
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

    def write_objective(self) -> dict:
        """Write a objective for the resume.

        Returns:
            dict: The written objective.
        """
        chain = self._chain_updater(
            Prompts.lookup["OBJECTIVE_WRITER"], ResumeSummarizerOutput
        )

        chain_inputs = self._get_formatted_chain_inputs(chain=chain)
        objective = chain.invoke(chain_inputs).dict()
        if not objective or "final_answer" not in objective:
            return None
        return objective["final_answer"]

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
