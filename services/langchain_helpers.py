from datetime import datetime
from typing import List
from dateutil import parser as dateparser
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
import langchain
from langchain_community.cache import InMemoryCache
from .. import config
from .. import utils

# Set up LLM cache
langchain.llm_cache = InMemoryCache()


def create_llm(**kwargs):
    """Create an LLM instance with specified parameters."""
    chat_model = kwargs.pop("chat_model", ChatOpenAI)
    kwargs.setdefault("model_name", config.MODEL_NAME)
    kwargs.setdefault("cache", False)
    return chat_model(**kwargs)


def format_list_as_string(lst: list, list_sep: str = "\n- ") -> str:
    """Format a list as a string with a specified separator."""
    if isinstance(lst, list):
        return list_sep + list_sep.join(lst)
    return str(lst)



def format_prompt_inputs_as_strings(prompt_inputs: list[str], **kwargs):
    """Convert values to string for all keys in kwargs matching list in prompt inputs."""
    return {
        k: format_list_as_string(v) for k, v in kwargs.items() if k in prompt_inputs
    }


def parse_date(date_str: str) -> datetime:
    """Given an arbitrary string, parse it to a date."""
    default_date = datetime(datetime.today().year, 1, 1)
    try:
        return dateparser.parse(str(date_str), default=default_date)
    except dateparser._parser.ParserError as e:
        langchain.llm_cache.clear()
        config.logger.error(f"Date input `{date_str}` could not be parsed.")
        raise e


def datediff_years(start_date: str, end_date: str) -> float:
    """Calculate the difference between two dates in fractional years.

    Args:
        start_date (str): The start date in string format.
        end_date (str): The end date in string format. Can be "Present" to use the current date.

    Returns:
        float: The difference in years, including fractional years.
    """
    if isinstance(end_date, str) and end_date.lower() == "present":
        end_date = datetime.today().strftime("%Y-%m-%d")
    datediff = relativedelta(parse_date(end_date), parse_date(start_date))
    return datediff.years + datediff.months / 12.0


def chain_formatter(format_type: str, input_data) -> str:
    """Format resume/job inputs for inclusion in a runnable sequence.

    Args:
        format_type (str): The type of data to format (e.g., 'experience', 'projects', 'skills', 'education').
        input_data: The data to be formatted.

    Returns:
        str: The formatted data as a string.
    """
    if format_type == 'experience':
        as_list = format_experiences_for_prompt(input_data)
        return format_prompt_inputs_as_strings(as_list)
    elif format_type == 'projects':
        as_list = format_projects_for_prompt(input_data)
        return format_prompt_inputs_as_strings(as_list)
    elif format_type == 'skills':
        as_list = format_skills_for_prompt(input_data)
        return format_prompt_inputs_as_strings(as_list)
    elif format_type == 'education':
        return format_education_for_resume(input_data)
    else:
        return input_data


def format_education_for_resume(education_list: list[dict]) -> str:
    """Format education entries for inclusion in a resume.

    Args:
        education_list (list[dict]): A list of dictionaries containing education details.

    Returns:
        str: A formatted string of education entries.
    """
    formatted_education = []
    for entry in education_list:
        school = entry.get('school', '')
        degrees = ', '.join(degree.get('names', ['Degree'])[0] for degree in entry.get('degrees', []))
        formatted_education.append(f"{school}: {degrees}")
    return '\n'.join(formatted_education)


def format_skills_for_prompt(input_data) -> list:
    """Format skills for inclusion in a prompt.

    Args:
        skills (list): The list of skills.

    Returns:
        list: A formatted list of skills.
    """
    result = []
    for cat in input_data:
        curr = ""
        if cat.get("category", ""):
            curr += f"{cat['category']}: "
        if "skills" in cat:
            curr += "Proficient in "
            curr += ", ".join(cat["skills"])
            result.append(curr)
    return result

def get_cumulative_time_from_titles(titles) -> int:
    """Calculate the cumulative time from job titles.

    Args:
        titles (list): A list of job titles with start and end dates.

    Returns:
        int: The cumulative time in years.
    """
    result = 0.0
    for t in titles:
        if "startdate" in t and "enddate" in t:
            if t["enddate"] == "current":
                last_date = datetime.today().strftime("%Y-%m-%d")
            else:
                last_date = t["enddate"]
        result += datediff_years(start_date=t["startdate"], end_date=last_date)
    return round(result)

def format_experiences_for_prompt(input_data) -> list:
    """Format experiences for inclusion in a prompt.

    Returns:
        list: A formatted list of experiences.
    """
    result = []
    for exp in input_data:
        curr = ""
        if "titles" in exp:
            exp_time = get_cumulative_time_from_titles(exp["titles"])
            curr += f"{exp_time} years experience in:"
        if "highlights" in exp:
            curr += format_list_as_string(exp["highlights"], list_sep="\n  - ")
            curr += "\n"
            result.append(curr)
    return result

def format_projects_for_prompt(input_data) -> list:
    """Format projects for inclusion in a prompt.

    Returns:
        list: A formatted list of projects.
    """
    result = []
    for exp in input_data:
        curr = ""
        if "name" in exp:
            name = exp["name"]
            curr += f"Side Project: {name}"
        if "highlights" in exp:
            curr += format_list_as_string(exp["highlights"], list_sep="\n  - ")
            curr += "\n"
            result.append(curr)
    return result
