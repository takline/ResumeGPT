"""
Utility functions for LangChain integration and related data processing.

This module provides helpers for:
- Creating and configuring LangChain LLM (Language Model) instances.
- Formatting lists and specific resume/job data structures for prompt inputs.
- Parsing dates from strings and calculating date differences.
"""
from datetime import datetime
from typing import List, Dict, Any, Type # Added Dict, Any, Type
from dateutil import parser as dateparser
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
import langchain
from langchain_community.cache import InMemoryCache
from .. import config
from .. import utils

# Set up LLM cache
langchain.llm_cache = InMemoryCache()


def create_llm(**kwargs: Any) -> ChatOpenAI:
    """
    Creates and configures an LLM instance, typically ChatOpenAI.

    This function initializes a chat model using parameters from the application's
    configuration (`config.MODEL_NAME`, `config.TEMPERATURE`) as defaults,
    which can be overridden or augmented by `kwargs`. Caching is enabled by default.

    Args:
        **kwargs: Arbitrary keyword arguments passed to the chat model constructor.
                  Common arguments include:
                  - chat_model (Type[ChatOpenAI]): The LangChain chat model class to use.
                    Defaults to `ChatOpenAI`.
                  - model_name (str): The specific model name (e.g., "gpt-4o").
                    Defaults to `config.MODEL_NAME`.
                  - temperature (float): The sampling temperature for the model.
                    Defaults to `config.TEMPERATURE`.
                  - cache (bool): Whether to use LangChain's caching for this LLM.
                    Defaults to `True`.

    Returns:
        ChatOpenAI: An instance of the configured chat model (or the type specified
                    by `chat_model` kwarg).
    """
    chat_model_cls: Type[ChatOpenAI] = kwargs.pop("chat_model", ChatOpenAI)
    kwargs.setdefault("model_name", config.MODEL_NAME)
    kwargs.setdefault("temperature", config.TEMPERATURE) # Ensure temperature is also defaulted from config
    # Ensure caching is enabled by default for LLM calls, leveraging the global langchain.llm_cache
    kwargs.setdefault("cache", True)
    return chat_model_cls(**kwargs)


def format_list_as_string(data_list: List[Any], list_sep: str = "\n- ") -> str:
    """
    Formats a list into a single string, with each item prefixed by a separator.

    If the input is not a list, it's converted to a string directly.

    Args:
        data_list (List[Any]): The list to format.
        list_sep (str): The separator string to prefix each item in the list.
                        Defaults to a newline followed by a hyphen and space.

    Returns:
        str: A string representation of the list, or the string representation
             of `data_list` if it's not a list.
    """
    if isinstance(data_list, list):
        # Filter out None or empty strings before joining, if desired
        # string_items = [str(item) for item in data_list if item is not None and str(item).strip() != ""]
        # return list_sep + list_sep.join(string_items) if string_items else ""
        return list_sep + list_sep.join(map(str, data_list)) # Simpler: convert all to string
    return str(data_list)


def format_prompt_inputs_as_strings(prompt_input_keys: List[str], **kwargs: Any) -> Dict[str, str]:
    """
    Formats specified values in `kwargs` from lists to strings for LLM prompt injection.

    Iterates through `kwargs`. If a key from `kwargs` is present in `prompt_input_keys`,
    its corresponding value (assumed to be a list) is formatted into a single string
    using `format_list_as_string`. Other items in `kwargs` are excluded.

    Args:
        prompt_input_keys (List[str]): A list of keys whose values in `kwargs` should be formatted.
        **kwargs (Any): Keyword arguments containing the data to be formatted.
                       Values corresponding to keys in `prompt_input_keys` are expected
                       to be lists suitable for `format_list_as_string`.

    Returns:
        Dict[str, str]: A dictionary containing only the keys from `prompt_input_keys`
                        that were present in `kwargs`, with their list values formatted as strings.
    """
    return {
        k: format_list_as_string(v) for k, v in kwargs.items() if k in prompt_input_keys
    }


def parse_date(date_str: str) -> datetime:
    """
    Parses an arbitrary date string into a datetime object.

    Uses `dateutil.parser.parse` for robust date string interpretation.
    If parsing fails, it logs an error and clears the global LangChain LLM cache
    as a precaution against potentially corrupted state due to unexpected date formats
    influencing subsequent LLM interactions. It then re-raises the parsing error.

    Args:
        date_str (str): The date string to parse.

    Returns:
        datetime: The parsed datetime object.

    Raises:
        dateparser.ParserError: If the date string cannot be parsed.
        # Note: The original code cleared langchain.llm_cache on error. This is a significant
        # side effect and is preserved here as per original logic, but should be reviewed.
    """
    # Use a default date (e.g., Jan 1st of the current year) if parts of the date are missing.
    default_date = datetime(datetime.today().year, 1, 1)
    try:
        return dateparser.parse(str(date_str), default=default_date)
    except dateparser.ParserError as e:
        # Critical side effect: Clearing the entire LLM cache on a single date parsing error.
        # This could impact performance significantly if date parsing errors are frequent.
        config.logger.warning(
            f"Date input `{date_str}` could not be parsed. Clearing LangChain LLM cache due to potential data inconsistency."
        )
        langchain.llm_cache.clear()
        config.logger.error(f"Date input `{date_str}` could not be parsed. Original error: {e}")
        raise # Re-raise the original parsing error


def datediff_years(start_date_str: str, end_date_str: str) -> float: # Renamed args for clarity
    """Calculate the difference between two dates in fractional years.

    """
    Calculates the difference between two dates in fractional years.

    Args:
        start_date_str (str): The start date in string format.
        end_date_str (str): The end date in string format. Can be "Present" or "current"
                            (case-insensitive) to use the current date.

    Returns:
        float: The difference in years, including fractional part for months.
               Returns 0.0 if date parsing fails for either date.
    """
    try:
        actual_end_date_str = end_date_str
        if isinstance(end_date_str, str) and end_date_str.lower() in ["present", "current"]:
            actual_end_date_str = datetime.today().strftime("%Y-%m-%d")

        start_dt = parse_date(start_date_str)
        end_dt = parse_date(actual_end_date_str)

        datediff = relativedelta(end_dt, start_dt)
        return datediff.years + (datediff.months / 12.0) + (datediff.days / 365.25) # Approximation for days
    except dateparser.ParserError: # Catch errors from parse_date
        # Already logged in parse_date, but good to handle here if needed
        return 0.0 # Or re-raise, or handle as per application's requirements
    except Exception as e:
        config.logger.error(f"Error calculating date difference for '{start_date_str}' and '{end_date_str}': {e}", exc_info=True)
        return 0.0


def chain_formatter(format_type: str, input_data: Any) -> Any:
    """
    Formats various types of resume or job data for inclusion in LLM prompts.

    Based on `format_type`, this function delegates to more specific formatting
    functions. If the `format_type` is not recognized for special formatting,
    the `input_data` is returned as is.

    Args:
        format_type (str): The type of data to format. Supported types include:
                           - 'experience': Formats a list of experience dicts.
                           - 'projects': Formats a list of project dicts.
                           - 'skills': Formats a list of skill category dicts.
                           - 'education': Formats a list of education dicts.
        input_data (Any): The data to be formatted, typically a list of dictionaries
                          or a simple string/list for the default case.

    Returns:
        Any: The formatted data, usually a string or a list of strings. If `format_type`
             is not matched, returns `input_data` unmodified.
    """
    if format_type == 'experience' and isinstance(input_data, list):
        formatted_list = format_experiences_for_prompt(input_data)
        # format_prompt_inputs_as_strings was designed for a dict of lists, not a list directly.
        # If the intention is to make one string from the list of experiences:
        return "\n".join(formatted_list)
    elif format_type == 'projects' and isinstance(input_data, list):
        formatted_list = format_projects_for_prompt(input_data)
        return "\n".join(formatted_list) # Similar adjustment
    elif format_type == 'skills' and isinstance(input_data, list):
        formatted_list = format_skills_for_prompt(input_data)
        return "\n".join(formatted_list) # Similar adjustment
    elif format_type == 'education' and isinstance(input_data, list):
        return format_education_for_resume(input_data) # This already returns a string

    # Default case: if format_type is not recognized or input_data is not of expected type for formatting.
    config.logger.debug(f"chain_formatter: Unhandled format_type '{format_type}' or unexpected input_data type. Returning input_data as is.")
    return input_data


def format_education_for_resume(education_list: List[Dict[str, Any]]) -> str:
    """
    Formats a list of education entries into a single newline-separated string.

    Each entry typically includes school name and degree information.

    Args:
        education_list (List[Dict[str, Any]]): A list of dictionaries, where each
                                              dictionary contains education details
                                              (e.g., 'school', 'degrees').

    Returns:
        str: A formatted string of all education entries, separated by newlines.
             Returns an empty string if the input list is empty.
    """
    formatted_education_entries = []
    if not isinstance(education_list, list):
        config.logger.warning("format_education_for_resume: input_data is not a list.")
        return ""

    for entry in education_list:
        if not isinstance(entry, dict):
            config.logger.warning(f"Skipping non-dictionary education entry: {entry}")
            continue
        school = entry.get('school', 'N/A')
        # Safely access nested 'degrees', 'names'
        degrees_str = "N/A"
        degrees_data = entry.get('degrees')
        if isinstance(degrees_data, list) and degrees_data:
            first_degree_info = degrees_data[0]
            if isinstance(first_degree_info, dict) and first_degree_info.get('names'):
                degree_names = first_degree_info['names']
                if isinstance(degree_names, list) and degree_names:
                    degrees_str = ', '.join(degree_names)
                elif isinstance(degree_names, str):
                     degrees_str = degree_names
        formatted_education_entries.append(f"{school}: {degrees_str}")
    return '\n'.join(formatted_education_entries)


def format_skills_for_prompt(skills_data: List[Dict[str, Any]]) -> List[str]:
    """
    Formats a list of skill categories and their skills into a list of strings.

    Each string typically represents one skill category followed by its skills.
    Example output: ["Category1: SkillA, SkillB", "Category2: SkillC, SkillD"]

    Args:
        skills_data (List[Dict[str, Any]]): A list of dictionaries, where each
                                            dictionary represents a skill category
                                            (e.g., {"category": "Programming", "skills": ["Python", "Java"]}).

    Returns:
        List[str]: A list of formatted strings, each representing a skill category and its skills.
                   Returns an empty list if input is malformed or empty.
    """
    formatted_skills_list = []
    if not isinstance(skills_data, list):
        config.logger.warning("format_skills_for_prompt: input_data is not a list.")
        return []

    for category_entry in skills_data:
        if not isinstance(category_entry, dict):
            config.logger.warning(f"Skipping non-dictionary skill entry: {category_entry}")
            continue
        category_name = category_entry.get("category", "")
        skills_list = category_entry.get("skills")

        current_skill_string = ""
        if category_name:
            current_skill_string += f"{category_name}: "

        if isinstance(skills_list, list) and skills_list:
            # current_skill_string += "Proficient in " # Removed "Proficient in" for more general use
            current_skill_string += ", ".join(str(skill) for skill in skills_list if isinstance(skill, str) and skill.strip())
            formatted_skills_list.append(current_skill_string)
        elif category_name: # If category exists but no skills, still add category name
            formatted_skills_list.append(current_skill_string.strip().rstrip(':'))


    return formatted_skills_list

def get_cumulative_time_from_titles(titles: List[Dict[str, Any]]) -> float: # Return float for more precision before rounding
    """
    Calculates the cumulative duration of employment from a list of job titles.

    Each title dictionary should contain 'startdate' and 'enddate'.
    'enddate' can be "current" or "present" to signify ongoing employment.

    Args:
        titles (List[Dict[str, Any]]): A list of title dictionaries.

    Returns:
        float: The total cumulative time in years (e.g., 2.5 for 2 years and 6 months).
               Returns 0.0 if titles list is empty or malformed.
    """
    total_duration_years = 0.0
    if not isinstance(titles, list):
        config.logger.warning("get_cumulative_time_from_titles: input 'titles' is not a list.")
        return 0.0

    for title_info in titles:
        if not isinstance(title_info, dict):
            config.logger.warning(f"Skipping non-dictionary title entry: {title_info}")
            continue

        start_date = title_info.get("startdate")
        end_date = title_info.get("enddate")

        if start_date and end_date:
            total_duration_years += datediff_years(start_date_str=str(start_date), end_date_str=str(end_date))
        else:
            config.logger.debug(f"Missing startdate or enddate in title: {title_info}")

    return total_duration_years # Return float, rounding can be done by caller if needed

def format_experiences_for_prompt(experiences_data: List[Dict[str, Any]]) -> List[str]:
    """
    Formats a list of job experiences into a list of strings for LLM prompts.

    Each string includes the calculated duration of the experience (if available)
    and a list of highlights.

    Args:
        experiences_data (List[Dict[str, Any]]): A list of experience dictionaries.
            Each dictionary should contain 'titles' (list of title dicts with
            'startdate'/'enddate') and 'highlights' (list of strings).

    Returns:
        List[str]: A list of formatted strings, each representing an experience.
                   Returns an empty list if input is malformed or empty.
    """
    formatted_experiences = []
    if not isinstance(experiences_data, list):
        config.logger.warning("format_experiences_for_prompt: input_data is not a list.")
        return []

    for experience in experiences_data:
        if not isinstance(experience, dict):
            config.logger.warning(f"Skipping non-dictionary experience entry: {experience}")
            continue

        current_experience_str = ""
        if "titles" in experience and isinstance(experience["titles"], list):
            # Calculate cumulative time for this specific experience
            cumulative_time_years = get_cumulative_time_from_titles(experience["titles"])
            if cumulative_time_years > 0: # Only add if time is calculated
                 # Round here for final display if int is desired, or keep float for precision.
                current_experience_str += f"{round(cumulative_time_years)} years experience in: "

        highlights = experience.get("highlights")
        if isinstance(highlights, list) and highlights:
            current_experience_str += format_list_as_string(highlights, list_sep="\n  - ")
            current_experience_str += "\n" # Add a newline after highlights for separation
            formatted_experiences.append(current_experience_str.strip()) # Add stripped string
        elif current_experience_str: # If there was time info but no highlights
             formatted_experiences.append(current_experience_str.strip())


    return formatted_experiences

def format_projects_for_prompt(projects_data: List[Dict[str, Any]]) -> List[str]:
    """
    Formats a list of project experiences into a list of strings for LLM prompts.

    Each string includes the project name and its highlights.

    Args:
        projects_data (List[Dict[str, Any]]): A list of project dictionaries.
            Each dictionary should contain 'name' (str) and 'highlights' (list of strings).

    Returns:
        List[str]: A list of formatted strings, each representing a project.
                   Returns an empty list if input is malformed or empty.
    """
    formatted_projects = []
    if not isinstance(projects_data, list):
        config.logger.warning("format_projects_for_prompt: input_data is not a list.")
        return []

    for project in projects_data:
        if not isinstance(project, dict):
            config.logger.warning(f"Skipping non-dictionary project entry: {project}")
            continue

        current_project_str = ""
        project_name = project.get("name")
        if isinstance(project_name, str) and project_name.strip():
            current_project_str += f"Side Project: {project_name}"

        highlights = project.get("highlights")
        if isinstance(highlights, list) and highlights:
            if current_project_str: # Add newline if name was present
                 current_project_str += ":"
            current_project_str += format_list_as_string(highlights, list_sep="\n  - ")
            current_project_str += "\n" # Add a newline after highlights for separation
            formatted_projects.append(current_project_str.strip())
        elif current_project_str: # If there was a name but no highlights
            formatted_projects.append(current_project_str.strip())

    return formatted_projects
