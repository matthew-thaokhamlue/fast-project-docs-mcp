"""
Template system for the MCP Document Generator.

This module contains default templates and template management functionality
for generating structured documents.
"""

from .manager import TemplateManager
from .defaults import DefaultTemplates

__all__ = [
    "TemplateManager",
    "DefaultTemplates",
]
