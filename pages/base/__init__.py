"""
API publique du Framework des Pages.

Ce package expose les abstractions communes utilisées par
toutes les pages d'IRIS Copilot.
"""

from .base_page import BasePage
from .exceptions import (
    PageConfigurationError,
    PageError,
    PageInitializationError,
    PageRenderError,
)
from .interfaces import Page
from .page_context import PageContext

__all__ = [
    "BasePage",
    "Page",
    "PageContext",
    "PageError",
    "PageConfigurationError",
    "PageInitializationError",
    "PageRenderError",
]