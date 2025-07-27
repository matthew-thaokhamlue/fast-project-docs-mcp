"""
MCP tools for the Document Generator server.

This module defines all the MCP tools that clients can use to interact
with the document generation system.
"""

from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp import types

from ..services.document_generator import DocumentGeneratorService
from ..services.resource_analyzer import ResourceAnalyzerService
from ..templates.manager import TemplateManager
from ..processors.registry import get_registry
from ..exceptions import DocumentGeneratorError, ValidationError
from ..models.core import PromptResult, AIGeneratedContent, ContentValidationResult
from ..security import (
    validate_user_input,
    validate_file_path,
    validate_template_config,
    validate_reference_folder,
    validate_dict_input,
    get_security_logger,
    log_security_event,
    log_input_validation,
    get_secure_defaults,
)


logger = get_security_logger(__name__)


def register_tools(mcp: FastMCP, document_service: DocumentGeneratorService) -> None:
    """Register all MCP tools with the server."""
    
    @mcp.tool()
    def generate_prd(
        user_input: str,
        project_context: str = "",
        reference_folder: str = "reference_resources",
        template_config: str = "default"
    ) -> Dict[str, Any]:
        """Generate intelligent prompt for Product Requirements Document (PRD.md)

        Args:
            user_input: User's description of the feature or product requirements
            project_context: Additional project context and constraints
            reference_folder: Path to folder containing reference materials
            template_config: Template configuration to use (default, custom, etc.)

        Returns:
            Dict containing intelligent prompt for Claude to process and generate PRD content
        """
        try:
            # Security validation
            security_config = get_secure_defaults()

            # Validate user input
            validated_user_input = validate_user_input(
                user_input,
                max_length=security_config.max_input_length
            )
            log_input_validation("user_input", True)

            # Validate project context
            validated_project_context = validate_user_input(
                project_context,
                max_length=security_config.max_input_length
            ) if project_context else ""

            # Validate template configuration
            validated_template_config = validate_template_config(template_config)
            log_input_validation("template_config", True)

            # Validate reference folder
            validated_reference_folder = validate_reference_folder(
                reference_folder,
                base_directory=Path.cwd() if security_config.restrict_to_base_directory else None
            )

            # Log security event
            log_security_event("prd_generation_request", {
                "user_input_length": len(validated_user_input),
                "has_project_context": bool(validated_project_context),
                "template_config": validated_template_config,
                "has_reference_folder": validated_reference_folder is not None
            })

            import asyncio
            result = asyncio.run(document_service.generate_prd_prompt(
                user_input=validated_user_input,
                project_context=validated_project_context,
                reference_folder=str(validated_reference_folder) if validated_reference_folder else "",
                template_config=validated_template_config
            ))

            log_security_event("prd_prompt_generation_success", {
                "document_type": result.document_type,
                "prompt_length": len(result.prompt)
            })

            return result.to_dict()

        except ValidationError as e:
            log_input_validation("prd_generation", False, e.recovery_suggestions)
            logger.warning(f"PRD generation validation failed: {e}")
            return {
                "error": "Input validation failed",
                "error_type": "ValidationError",
                "recovery_suggestions": e.recovery_suggestions
            }
        except Exception as e:
            log_security_event("prd_generation_error", {
                "error_type": type(e).__name__,
                "error_message": str(e)[:200]  # Limit error message length
            }, severity="ERROR")
            logger.error(f"PRD generation failed: {e}")
            return {
                "error": "Document generation failed",
                "error_type": type(e).__name__,
                "recovery_suggestions": getattr(e, 'recovery_suggestions', [
                    "Check input parameters",
                    "Verify reference folder exists",
                    "Try with default template"
                ])
            }
    
    @mcp.tool()
    def generate_spec(
        requirements_input: str,
        existing_prd_path: str = "",
        reference_folder: str = "reference_resources",
        template_config: str = "default"
    ) -> Dict[str, Any]:
        """Generate intelligent prompt for Technical Specification Document (SPEC.md)

        Args:
            requirements_input: Requirements or specification input text
            existing_prd_path: Path to existing PRD document to reference
            reference_folder: Path to folder containing reference materials
            template_config: Template configuration to use (default, custom, etc.)

        Returns:
            Dict containing intelligent prompt for Claude to process and generate SPEC content
        """
        try:
            import asyncio
            result = asyncio.run(document_service.generate_spec_prompt(
                requirements_input=requirements_input,
                existing_prd_path=existing_prd_path,
                reference_folder=reference_folder,
                template_config=template_config
            ))

            return result.to_dict()

        except Exception as e:
            logger.error(f"SPEC prompt generation failed: {e}")
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "recovery_suggestions": getattr(e, 'recovery_suggestions', [
                    "Check input parameters",
                    "Verify existing PRD path if provided",
                    "Verify reference folder exists",
                    "Try with default template"
                ])
            }
    
    @mcp.tool()
    def generate_design(
        specification_input: str,
        existing_spec_path: str = "",
        reference_folder: str = "reference_resources",
        template_config: str = "default"
    ) -> Dict[str, Any]:
        """Generate intelligent prompt for Design Document (DESIGN.md)

        Args:
            specification_input: Specification or design input text
            existing_spec_path: Path to existing SPEC document to reference
            reference_folder: Path to folder containing reference materials
            template_config: Template configuration to use (default, custom, etc.)

        Returns:
            Dict containing intelligent prompt for Claude to process and generate DESIGN content
        """
        try:
            import asyncio
            result = asyncio.run(document_service.generate_design_prompt(
                specification_input=specification_input,
                existing_spec_path=existing_spec_path,
                reference_folder=reference_folder,
                template_config=template_config
            ))

            return result.to_dict()

        except Exception as e:
            logger.error(f"DESIGN prompt generation failed: {e}")
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "recovery_suggestions": getattr(e, 'recovery_suggestions', [
                    "Check input parameters",
                    "Verify existing SPEC path if provided",
                    "Verify reference folder exists",
                    "Try with default template"
                ])
            }
    
    @mcp.tool()
    def analyze_resources(
        folder_path: str = "reference_resources"
    ) -> Dict[str, Any]:
        """Analyze and categorize reference resources

        Args:
            folder_path: Path to folder containing reference resources

        Returns:
            Dict containing analysis results, file categories, and statistics
        """
        try:
            # Security validation
            security_config = get_secure_defaults()

            # Validate folder path
            validated_folder_path = validate_reference_folder(
                folder_path,
                base_directory=Path.cwd() if security_config.restrict_to_base_directory else None
            )

            if validated_folder_path is None:
                return {
                    "error": "Invalid or empty folder path",
                    "error_type": "ValidationError",
                    "recovery_suggestions": [
                        "Provide a valid folder path",
                        "Ensure folder exists and is accessible"
                    ]
                }

            log_input_validation("folder_path", True)
            log_security_event("resource_analysis_request", {
                "folder_path": str(validated_folder_path)
            })

            import asyncio
            resource_analyzer = ResourceAnalyzerService()
            analysis = asyncio.run(resource_analyzer.analyze_folder(validated_folder_path))

            log_security_event("resource_analysis_success", {
                "total_files": analysis.total_files,
                "categories_count": len(analysis.categorized_files)
            })

            return {
                "total_files": analysis.total_files,
                "categories": {
                    category: len(files)
                    for category, files in analysis.categorized_files.items()
                },
                "content_summary": analysis.content_summary,
                "processing_errors": analysis.processing_errors,
                "supported_formats": analysis.supported_formats,
                "analysis_time": analysis.analysis_time.isoformat()
            }

        except ValidationError as e:
            log_input_validation("resource_analysis", False, e.recovery_suggestions)
            logger.warning(f"Resource analysis validation failed: {e}")
            return {
                "error": "Path validation failed",
                "error_type": "ValidationError",
                "recovery_suggestions": e.recovery_suggestions
            }
        except Exception as e:
            log_security_event("resource_analysis_error", {
                "error_type": type(e).__name__,
                "error_message": str(e)[:200]
            }, severity="ERROR")
            logger.error(f"Resource analysis failed: {e}")
            return {
                "error": "Resource analysis failed",
                "error_type": type(e).__name__,
                "recovery_suggestions": getattr(e, 'recovery_suggestions', [
                    "Check if folder path exists",
                    "Verify folder permissions",
                    "Ensure folder contains supported file types"
                ])
            }
    
    @mcp.tool()
    def list_supported_formats() -> Dict[str, Any]:
        """List supported file formats for reference resources
        
        Returns:
            Dict containing supported formats and processor information
        """
        try:
            registry = get_registry()
            return {
                "supported_extensions": registry.get_supported_extensions(),
                "processors": registry.get_all_processors_info(),
                "statistics": registry.get_statistics()
            }
            
        except Exception as e:
            logger.error(f"Failed to list supported formats: {e}")
            return {
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @mcp.tool()
    def list_templates() -> Dict[str, Any]:
        """List available document templates
        
        Returns:
            Dict containing available templates and their information
        """
        try:
            template_manager = TemplateManager()
            templates = template_manager.list_templates()
            
            return {
                "templates": templates,
                "total_count": len(templates),
                "template_types": list(set(t['type'] for t in templates))
            }
            
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return {
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @mcp.tool()
    def customize_template(
        template_type: str,
        sections: Dict[str, Any],
        formatting_rules: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Customize document template structure

        Args:
            template_type: Type of template to customize (prd, spec, design)
            sections: Section customizations (add, modify, remove)
            formatting_rules: Optional formatting rules and preferences

        Returns:
            Dict containing customized template information
        """
        try:
            # Security validation
            validated_template_type = validate_template_config(template_type)

            # Validate sections dictionary
            allowed_section_keys = ['add', 'modify', 'remove']
            validated_sections = validate_dict_input(sections, allowed_keys=allowed_section_keys)

            # Validate formatting rules if provided
            validated_formatting_rules = None
            if formatting_rules:
                allowed_formatting_keys = ['description', 'author', 'supports_customization']
                validated_formatting_rules = validate_dict_input(
                    formatting_rules,
                    allowed_keys=allowed_formatting_keys
                )

            log_input_validation("template_customization", True)
            log_security_event("template_customization_request", {
                "template_type": validated_template_type,
                "sections_keys": list(validated_sections.keys()),
                "has_formatting_rules": validated_formatting_rules is not None
            })

            template_manager = TemplateManager()

            customizations = {
                'name': f"custom_{validated_template_type}",
                'sections': validated_sections
            }

            if validated_formatting_rules:
                customizations['metadata'] = validated_formatting_rules

            custom_template = template_manager.customize_template(
                validated_template_type, customizations
            )

            log_security_event("template_customization_success", {
                "template_name": custom_template.name,
                "sections_count": len(custom_template.sections)
            })

            return {
                "template_name": custom_template.name,
                "template_type": custom_template.template_type,
                "sections": list(custom_template.sections.keys()),
                "validation": template_manager.validate_template(custom_template).to_dict()
            }

        except ValidationError as e:
            log_input_validation("template_customization", False, e.recovery_suggestions)
            logger.warning(f"Template customization validation failed: {e}")
            return {
                "error": "Template customization validation failed",
                "error_type": "ValidationError",
                "recovery_suggestions": e.recovery_suggestions
            }
        except Exception as e:
            log_security_event("template_customization_error", {
                "error_type": type(e).__name__,
                "error_message": str(e)[:200]
            }, severity="ERROR")
            logger.error(f"Template customization failed: {e}")
            return {
                "error": "Template customization failed",
                "error_type": type(e).__name__,
                "recovery_suggestions": getattr(e, 'recovery_suggestions', [
                    "Check template type is valid (prd, spec, design)",
                    "Verify section customizations are properly formatted",
                    "Use list_templates to see available base templates"
                ])
            }
    
    @mcp.tool()
    def get_generation_statistics() -> Dict[str, Any]:
        """Get statistics about document generation capabilities
        
        Returns:
            Dict containing system capabilities and statistics
        """
        try:
            return document_service.get_generation_statistics()
            
        except Exception as e:
            logger.error(f"Failed to get generation statistics: {e}")
            return {
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @mcp.tool()
    def save_generated_document(
        document_type: str,
        content: str,
        filename: str = "",
        user_notes: str = "",
        validate_content: bool = True
    ) -> Dict[str, Any]:
        """Save AI-generated document content to file

        Args:
            document_type: Type of document ('prd', 'spec', 'design')
            content: The AI-generated document content
            filename: Optional custom filename (defaults to document_type.md)
            user_notes: Optional notes about the generation process
            validate_content: Whether to validate the content structure

        Returns:
            Dict containing file_path, validation_result, and metadata
        """
        try:
            import asyncio

            # Create AIGeneratedContent object
            ai_content = AIGeneratedContent(
                document_type=document_type.lower(),
                content=content,
                filename=filename or f"{document_type.upper()}.md",
                user_notes=user_notes,
                validation_requested=validate_content
            )

            result = asyncio.run(document_service.save_ai_generated_content(ai_content))

            log_security_event("ai_content_saved", {
                "document_type": document_type,
                "filename": ai_content.filename,
                "content_length": len(content)
            })

            return result.to_dict()

        except Exception as e:
            logger.error(f"Failed to save AI-generated content: {e}")
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "recovery_suggestions": [
                    "Check that the content is valid",
                    "Verify the document type is supported",
                    "Ensure write permissions to output directory"
                ]
            }

    @mcp.tool()
    def validate_generated_content(
        document_type: str,
        content: str
    ) -> Dict[str, Any]:
        """Validate AI-generated document content structure

        Args:
            document_type: Type of document ('prd', 'spec', 'design')
            content: The document content to validate

        Returns:
            Dict containing validation results and suggestions
        """
        try:
            import asyncio

            result = asyncio.run(document_service.validate_ai_content(
                document_type=document_type.lower(),
                content=content
            ))

            return result.to_dict()

        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "recovery_suggestions": [
                    "Check that the document type is supported",
                    "Verify the content format is correct"
                ]
            }

    logger.info("Registered all MCP tools successfully")
