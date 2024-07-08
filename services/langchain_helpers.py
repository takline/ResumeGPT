from datetime import datetime
from typing import List
from dateutil import parser as dateparser
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
import langchain
from langchain_community.cache import InMemoryCache
from .. import config

# Set up LLM cache
langchain.llm_cache = InMemoryCache()


def create_llm(**kwargs):
    """Create an LLM instance with specified parameters."""
    chat_model = kwargs.pop("chat_model", ChatOpenAI)
    kwargs.setdefault("model_name", "gpt-4o")
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
    """Get difference between arbitrarily formatted dates in fractional years to the floor month."""
    datediff = relativedelta(parse_date(end_date), parse_date(start_date))
    return datediff.years + datediff.months / 12.0
