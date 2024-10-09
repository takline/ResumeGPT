import yaml
from typing import List, Dict, Any
from .. import utils
from .. import config
from .langchain_helpers import *
from ..prompts import Prompts
from ..models.job_post import JobPost
from ..pdf_generation import ResumePDFGenerator
from langchain_core.runnables import RunnableSequence, RunnableParallel
from ..models.resume import (
    ResumeBulletPointRewriterOutput,
    BulletPointImproverOutput,
)
from typing import List, Dict, Any, Tuple


class BulletPointsProcessor:
    def __init__(
        self,
        target_list: List[Dict[str, Any]],
        parsed_job,
        llm_kwargs: dict = None,
    ):
        """
        Initialize the BulletPointsProcessor with the target list.

        Args:
            target_list (List[Dict[str, Any]]): The list of experiences or projects to process.
        """
        self.target_list: List[Dict[str, Any]] = target_list
        self.updater_chain: RunnableSequence = None
        self.reviewer_chain: RunnableSequence = None
        self.updater_chain_inputs: Dict[str, Any] = {}
        self.reviewer_chain_inputs: Dict[str, Any] = {}
        self.prompt_template: List[str] = []
        self.llm_kwargs = llm_kwargs or {}
        self.parsed_job = parsed_job
        self.reviewer_chain_output = None
        self.updater_chain_output = None

    def rewrite_bullet_points(self) -> Dict[str, Any]:
        """
        Rewrite bullet points in the resume.

        Returns:
            dict: The status of the operation.
        """
        config.logger.info("Starting bullet point rewriting process.")

        self.updater_chain = self._initialize_bullet_point_chain()
        config.logger.debug("Initialized bullet point rewriting chain.")

        self.updater_chain_inputs = self._prepare_chain_inputs(self.updater_chain)
        config.logger.debug("Prepared chain inputs.")

        self._rewrite_bullets()
        config.logger.info("Rewritten bullets based on initial rewrite chain.")

        reviewed_bullets = self._review_bullets()
        config.logger.info("Reviewed and improved bullets.")

        self._update_target_highlights(reviewed_bullets)
        config.logger.info("Updated target highlights with reviewed bullets.")

        return self.target_list

    def _initialize_bullet_point_chain(self) -> RunnableSequence:
        """
        Initialize the bullet point rewriting chain.

        Returns:
            RunnableSequence: The initialized chain for rewriting bullet points.
        """
        return chain_updater(
            prompt_msgs=Prompts.lookup["BULLET_POINT_REWRITER"],
            pydantic_object=ResumeBulletPointRewriterOutput,
            **self.llm_kwargs,
        )

    def _prepare_chain_inputs(self, chain: RunnableSequence) -> Dict[str, Any]:
        """
        Prepare the initial inputs for the chain.

        Args:
            chain (RunnableSequence): The chain for rewriting bullet points.

        Returns:
            Dict[str, Any]: The formatted chain inputs.
        """
        output_dict = {}
        for key in chain.get_input_schema().schema()["required"]:
            output_dict[key] = chain_formatter(key, self.parsed_job.get(key))
        return output_dict

    def _rewrite_bullets(self) -> None:
        """
        Rewrite the bullet points for each item in the target list.
        """
        config.logger.info("Rewriting bullets for each item in the target list.")
        config.logger.debug(f"self.target_list: {self.target_list}")
        for exp_index, exp in enumerate(self.target_list):
            draft_key = "draft"
            self.updater_chain_inputs[draft_key] = utils.format_list_as_string(
                exp["highlights"]
            )
            config.logger.debug(
                f"Formatted highlights for item {exp_index}: {self.updater_chain_inputs[draft_key]}"
            )

            self.updater_chain_output = (
                self.updater_chain.invoke(self.updater_chain_inputs)
                .dict()
                .get("answer", [])
            )
            config.logger.debug(
                f"Received response from bullet point chain for item {exp_index}: {self.updater_chain_output}"
            )

            sorted_bullets = self._sort_bullets_by_relevance(self.updater_chain_output)
            config.logger.debug(
                f"Sorted bullets for item {exp_index}: {sorted_bullets}"
            )

            self.target_list[exp_index]["highlights"] = [
                bullet["highlight"] for bullet in sorted_bullets
            ]
            config.logger.debug(f"Updated highlights for item {exp_index}.")

    def _sort_bullets_by_relevance(
        self, bullets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sort bullets based on their relevance in descending order.

        Args:
            bullets (List[Dict[str, Any]]): The list of bullets to sort.

        Returns:
            List[Dict[str, Any]]: The sorted list of bullets.
        """
        return sorted(bullets, key=lambda d: d.get("relevance", 0), reverse=True)

    def _review_bullets(self) -> List[Dict[str, List[str]]]:
        """
        Review and improve the rewritten bullet points.

        Returns:
            BulletPointImproverOutput: The reviewed bullets.
        """
        config.logger.info("Loading prompt template for bullet point improvement.")
        self.prompt_template = self._load_prompt_template("BULLET_POINT_IMPROVER")
        config.logger.debug(
            f"self.prompt_template (BULLET_POINT_IMPROVER): {self.prompt_template}"
        )

        self._format_prompts()
        config.logger.debug(f"Formatted prompts: {self.prompt_template}")

        self.reviewer_chain = self._initialize_reviewer_chain()
        config.logger.debug("Initialized reviewer chain.")

        self.reviewer_chain_output = self.reviewer_chain.invoke(
            self.updater_chain_inputs
        ).dict()
        config.logger.debug(f"Received reviewed bullets: {self.reviewer_chain_output}")

        return self.reviewer_chain_output.get("answer", [])

    def _load_prompt_template(self, prompt_key: str) -> List[str]:
        """
        Load the prompt template from the YAML configuration.

        Args:
            prompt_key (str): The key to identify the prompt template.

        Returns:
            List[str]: The loaded prompt template.
        """
        try:
            with open(config.PROMPTS_YAML, "r") as file:
                raw_prompts = yaml.safe_load(file)
            config.logger.info(f"Loaded prompt template for key: {prompt_key}")
            return raw_prompts[prompt_key]
        except FileNotFoundError:
            config.logger.error(
                f"Prompts YAML file not found at {config.PROMPTS_YAML}."
            )
            raise
        except KeyError:
            config.logger.error(f"Prompt key '{prompt_key}' not found in prompts YAML.")
            raise
        except Exception as e:
            config.logger.error(
                f"An error occurred while loading prompt templates: {e}"
            )
            raise

    def _format_prompts(
        self,
    ):
        """
        Format the prompts with the new bullets and tags.

        Returns:
            Tuple[str, str]: The formatted prompts and tags.
        """
        new_bullets = ""
        new_tags = ""
        for i, exp in enumerate(self.target_list):
            key = f"draft_{i}"
            self.updater_chain_inputs[key] = utils.format_list_as_string(
                exp["highlights"]
            )
            new_tags += f", <{key}>"
            bullet_section = f"\n<{key}>\n{{{key}}}\n</{key}>\n"
            new_bullets += bullet_section
            config.logger.debug(f"Formatted bullet section for {key}.")

        # Create a copy of the prompt_template to avoid modifying the list during iteration
        updated_prompts = self.prompt_template.copy()
        for key, prompt in updated_prompts.items():
            updated_prompts[key] = prompt.replace("PUT_BULLETS_HERE", new_bullets)
            updated_prompts[key] = updated_prompts[key].replace(
                "PUT_DRAFT_TAGS_HERE", f"({new_tags})"
            )
            config.logger.debug(f"Updated prompt {key} with bullets and tags.")

        self.prompt_template = updated_prompts
        config.logger.debug("All prompts formatted with new bullets and tags.")

    def _initialize_reviewer_chain(self) -> RunnableSequence:
        """
        Initialize the reviewer chain with the formatted prompt template.

        Args:
            formatted_prompts (List[str]): The formatted prompt template.

        Returns:
            RunnableSequence: The initialized reviewer chain.
        """
        formatted_prompt = Prompts.create_prompt_from_dict(self.prompt_template)
        chain = chain_updater(
            prompt_msgs=formatted_prompt,
            pydantic_object=BulletPointImproverOutput,
        )
        config.logger.debug("Reviewer chain initialized successfully.")
        return chain

    def _update_target_highlights(
        self, reviewed_bullets: List[Dict[str, List[str]]]
    ) -> None:
        """
        Update the highlights in the target list with the reviewed bullets.
        """
        config.logger.info(
            f"Updating target highlights with reviewed bullets, reviewed_bullets: {reviewed_bullets}"
        )

        for i, bullet_dict in enumerate(reviewed_bullets):
            highlights = bullet_dict.get("highlights", [])

            if i < len(self.target_list):
                self.target_list[i]["highlights"] = highlights
                config.logger.debug(f"Updated highlights for item {i}: {highlights}")
            else:
                config.logger.warning(
                    f"Reviewed bullets contain more items than the target list at index {i}."
                )

        if len(reviewed_bullets) < len(self.target_list):
            config.logger.warning(
                f"Fewer reviewed bullets ({len(reviewed_bullets)}) than target list items ({len(self.target_list)})."
            )
