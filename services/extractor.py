from typing import Optional
from langchain_core.pydantic_v1 import BaseModel
from .. import config
from . import langchain_helpers

class ExtractorLLM:
    def __init__(self):
        """Initialize the Extractor LLM with a default model."""
        self.extractor_llm = langchain_helpers.create_llm(
            chat_model=config.CHAT_MODEL,
            model_name=config.MODEL_NAME,
            temperature=config.TEMPERATURE,
            cache=True,
        )

    def extract_from_input(self, pydantic_object, input: str, **chain_kwargs) -> dict:
        """Extract structured data from input using the specified pydantic object."""
        try:
            model_with_structure = self.extractor_llm.with_structured_output(
                pydantic_object
            )
            return model_with_structure.invoke(input).dict()
        except Exception as e:
            print("Encountered exception during parsing input. See below:")
            print(e)
