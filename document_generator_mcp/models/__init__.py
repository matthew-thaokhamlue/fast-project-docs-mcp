"""
Data models for the MCP Document Generator.

This module contains all the core data structures used throughout the system,
including document results, resource analysis, templates, and document structures.
"""

from .core import (
    DocumentResult,
    ResourceAnalysis,
    Template,
    FileContent,
    ValidationResult,
    PromptResult,
    GenerationRequest,
    AIGeneratedContent,
    ContentValidationResult,
)

from .document_structures import (
    PRDStructure,
    SPECStructure,
    DESIGNStructure,
)

__all__ = [
    "DocumentResult",
    "ResourceAnalysis",
    "Template",
    "FileContent",
    "ValidationResult",
    "PromptResult",
    "GenerationRequest",
    "AIGeneratedContent",
    "ContentValidationResult",
    "PRDStructure",
    "SPECStructure",
    "DESIGNStructure",
]
