"""
Selenium2Playwright - Convert Selenium code to Playwright using Local LLM
"""

__version__ = "1.0.0"
__author__ = "Qais7744"
__license__ = "MIT"

from .converter import SeleniumToPlaywrightConverter
from .llm_client import LocalLLMClient
from .code_parser import SeleniumCodeParser

__all__ = [
    "SeleniumToPlaywrightConverter",
    "LocalLLMClient", 
    "SeleniumCodeParser"
]
