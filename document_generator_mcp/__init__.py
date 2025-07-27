"""
MCP Document Generator Server

A Python-based Model Context Protocol server that automates the generation of 
project documentation including PRD.md, SPEC.md, and DESIGN.md files.

This package provides:
- Document generation tools for MCP clients
- Reference resource analysis and integration
- Customizable document templates
- Multi-format file processing capabilities
"""

__version__ = "0.1.0"
__author__ = "Kiro Development Team"
__description__ = "MCP server for automated document generation"

from .models import (
    DocumentResult,
    ResourceAnalysis,
    Template,
    FileContent,
    PRDStructure,
    SPECStructure,
    DESIGNStructure,
    PromptResult,
    GenerationRequest,
    AIGeneratedContent,
    ContentValidationResult,
)

from .exceptions import (
    DocumentGeneratorError,
    FileProcessingError,
    TemplateValidationError,
    ResourceAccessError,
    ContentGenerationError,
)

__all__ = [
    "DocumentResult",
    "ResourceAnalysis",
    "Template",
    "FileContent",
    "PRDStructure",
    "SPECStructure",
    "DESIGNStructure",
    "PromptResult",
    "GenerationRequest",
    "AIGeneratedContent",
    "ContentValidationResult",
    "DocumentGeneratorError",
    "FileProcessingError",
    "TemplateValidationError",
    "ResourceAccessError",
    "ContentGenerationError",
]
