"""
Custom exception hierarchy for the MCP Document Generator.

This module defines all custom exceptions used throughout the system,
following the pattern of providing recovery suggestions for better error handling.
"""

from typing import List, Optional


class DocumentGeneratorError(Exception):
    """Base exception for document generator errors."""
    
    def __init__(self, message: str, recovery_suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.recovery_suggestions = recovery_suggestions or []


class FileProcessingError(DocumentGeneratorError):
    """Raised when file cannot be processed."""
    
    def __init__(self, message: str, file_path: str = "", recovery_suggestions: Optional[List[str]] = None):
        super().__init__(message, recovery_suggestions)
        self.file_path = file_path


class UnsupportedFormatError(FileProcessingError):
    """Raised when file format is not supported."""
    
    def __init__(self, file_path: str, format_extension: str):
        message = f"Unsupported file format '{format_extension}' for file: {file_path}"
        recovery_suggestions = [
            f"Convert the file to a supported format (.md, .txt, .json, .yaml, .pdf)",
            "Check if the file extension is correct",
            "Add a custom processor for this file type"
        ]
        super().__init__(message, file_path, recovery_suggestions)
        self.format_extension = format_extension


class TemplateValidationError(DocumentGeneratorError):
    """Raised when template validation fails."""
    
    def __init__(self, template_name: str, validation_errors: List[str]):
        message = f"Template validation failed for '{template_name}': {', '.join(validation_errors)}"
        recovery_suggestions = [
            "Check template syntax and structure",
            "Ensure all required sections are present",
            "Use the default template as a reference",
            "Validate template against schema"
        ]
        super().__init__(message, recovery_suggestions)
        self.template_name = template_name
        self.validation_errors = validation_errors


class ResourceAccessError(DocumentGeneratorError):
    """Raised when reference resources cannot be accessed."""
    
    def __init__(self, message: str, resource_path: str = "", recovery_suggestions: Optional[List[str]] = None):
        if not recovery_suggestions:
            recovery_suggestions = [
                "Check if the resource path exists",
                "Verify read permissions for the resource",
                "Ensure the resource is not corrupted",
                "Try with a different resource path"
            ]
        super().__init__(message, recovery_suggestions)
        self.resource_path = resource_path


class ContentGenerationError(DocumentGeneratorError):
    """Raised when document content generation fails."""
    
    def __init__(self, document_type: str, generation_stage: str, message: str):
        full_message = f"Content generation failed for {document_type} at stage '{generation_stage}': {message}"
        recovery_suggestions = [
            "Check input data quality and completeness",
            "Verify template compatibility",
            "Review reference resources for conflicts",
            "Try with minimal input to isolate the issue"
        ]
        super().__init__(full_message, recovery_suggestions)
        self.document_type = document_type
        self.generation_stage = generation_stage


class ValidationError(DocumentGeneratorError):
    """Raised when content validation fails."""
    
    def __init__(self, content_type: str, validation_issues: List[str]):
        message = f"Validation failed for {content_type}: {', '.join(validation_issues)}"
        recovery_suggestions = [
            "Review the validation issues listed",
            "Check content structure and formatting",
            "Ensure all required sections are present",
            "Validate against the appropriate schema"
        ]
        super().__init__(message, recovery_suggestions)
        self.content_type = content_type
        self.validation_issues = validation_issues


class ConfigurationError(DocumentGeneratorError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, config_item: str, message: str):
        full_message = f"Configuration error for '{config_item}': {message}"
        recovery_suggestions = [
            "Check configuration file syntax",
            "Ensure all required configuration items are present",
            "Verify configuration values are valid",
            "Use default configuration as a reference"
        ]
        super().__init__(full_message, recovery_suggestions)
        self.config_item = config_item
