"""Prompts package for ResumeGPT.

This package is responsible for managing and initializing prompt templates
and related descriptions that are used to guide Large Language Model (LLM)
interactions for various tasks like resume improvement, skill matching, etc.
"""
from .prompts import Prompts

# Initialize prompts when the package is imported to make them readily available.
Prompts.initialize()
