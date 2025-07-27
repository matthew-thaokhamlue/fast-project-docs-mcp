"""
Document generator service for the MCP Document Generator.

This service orchestrates the document generation process, coordinating
template management, resource analysis, and content processing.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..models.core import (
    DocumentResult,
    ProcessingContext,
    ResourceAnalysis,
    PromptResult,
    AIGeneratedContent,
    ContentValidationResult
)
from ..templates.manager import TemplateManager
from ..services.resource_analyzer import ResourceAnalyzerService
from ..services.content_processor import ContentProcessor
from ..exceptions import (
    DocumentGeneratorError, 
    ContentGenerationError,
    ResourceAccessError,
    TemplateValidationError
)


logger = logging.getLogger(__name__)


class DocumentGeneratorService:
    """Main service for orchestrating document generation."""
    
    def __init__(self, 
                 template_manager: Optional[TemplateManager] = None,
                 resource_analyzer: Optional[ResourceAnalyzerService] = None,
                 content_processor: Optional[ContentProcessor] = None,
                 output_directory: Optional[Path] = None):
        """Initialize the document generator service."""
        self.template_manager = template_manager or TemplateManager()
        self.resource_analyzer = resource_analyzer or ResourceAnalyzerService()
        self.content_processor = content_processor or ContentProcessor(self.template_manager)
        self.output_directory = output_directory or Path.cwd()
        
        # Note: Directory creation is deferred until actually needed
    
    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists, creating it if necessary."""
        try:
            # Resolve the path to absolute
            resolved_path = self.output_directory.resolve()
            resolved_path.mkdir(parents=True, exist_ok=True)
            self.output_directory = resolved_path
        except (PermissionError, OSError) as e:
            logger.warning(f"Could not create output directory {self.output_directory}: {e}")
            # Fall back to a generated_docs folder in current working directory
            fallback_dir = Path.cwd() / 'generated_docs'
            try:
                fallback_dir.mkdir(parents=True, exist_ok=True)
                self.output_directory = fallback_dir
                logger.info(f"Using fallback directory as output: {self.output_directory}")
            except (PermissionError, OSError) as e2:
                logger.error(f"Could not create fallback directory: {e2}")
                # Last resort: use current working directory
                self.output_directory = Path.cwd()
                logger.info(f"Using current directory as output: {self.output_directory}")
    
    async def generate_prd(self, 
                          user_input: str,
                          project_context: str = "",
                          reference_folder: str = "reference_resources",
                          template_config: str = "default") -> DocumentResult:
        """Generate Product Requirements Document (PRD.md)."""
        try:
            logger.info("Starting PRD generation")
            
            # Create processing context
            context = await self._create_processing_context(
                user_input, project_context, reference_folder, template_config
            )
            
            # Generate document content
            content = await self.content_processor.process_prd_content(context)
            
            # Save document to file
            file_path = self.output_directory / "PRD.md"
            await self._save_document(file_path, content)
            
            # Create document result
            result = DocumentResult(
                file_path=file_path,
                content=content,
                summary=self._generate_summary(content, "PRD"),
                sections_generated=self._extract_sections(content),
                references_used=self._extract_references(context),
                warnings=[],
                metadata={
                    "document_type": "prd",
                    "template_used": template_config,
                    "has_reference_resources": context.reference_resources is not None,
                    "generation_mode": context.generation_mode
                }
            )
            
            logger.info(f"PRD generation completed: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"PRD generation failed: {e}")
            raise ContentGenerationError("prd", "generation", str(e))
    
    async def generate_spec(self,
                           requirements_input: str,
                           existing_prd_path: str = "",
                           reference_folder: str = "reference_resources", 
                           template_config: str = "default") -> DocumentResult:
        """Generate Technical Specification Document (SPEC.md)."""
        try:
            logger.info("Starting SPEC generation")
            
            # Enhance input with existing PRD if provided
            enhanced_input = await self._enhance_with_existing_document(
                requirements_input, existing_prd_path
            )
            
            # Create processing context
            context = await self._create_processing_context(
                enhanced_input, "", reference_folder, template_config
            )
            
            # Generate document content
            content = await self.content_processor.process_spec_content(context)
            
            # Save document to file
            file_path = self.output_directory / "SPEC.md"
            await self._save_document(file_path, content)
            
            # Create document result
            result = DocumentResult(
                file_path=file_path,
                content=content,
                summary=self._generate_summary(content, "SPEC"),
                sections_generated=self._extract_sections(content),
                references_used=self._extract_references(context),
                warnings=[],
                metadata={
                    "document_type": "spec",
                    "template_used": template_config,
                    "has_reference_resources": context.reference_resources is not None,
                    "existing_prd_used": bool(existing_prd_path),
                    "generation_mode": context.generation_mode
                }
            )
            
            logger.info(f"SPEC generation completed: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"SPEC generation failed: {e}")
            raise ContentGenerationError("spec", "generation", str(e))
    
    async def generate_design(self,
                             specification_input: str,
                             existing_spec_path: str = "",
                             reference_folder: str = "reference_resources",
                             template_config: str = "default") -> DocumentResult:
        """Generate Design Document (DESIGN.md)."""
        try:
            logger.info("Starting DESIGN generation")
            
            # Enhance input with existing SPEC if provided
            enhanced_input = await self._enhance_with_existing_document(
                specification_input, existing_spec_path
            )
            
            # Create processing context
            context = await self._create_processing_context(
                enhanced_input, "", reference_folder, template_config
            )
            
            # Generate document content
            content = await self.content_processor.process_design_content(context)
            
            # Save document to file
            file_path = self.output_directory / "DESIGN.md"
            await self._save_document(file_path, content)
            
            # Create document result
            result = DocumentResult(
                file_path=file_path,
                content=content,
                summary=self._generate_summary(content, "DESIGN"),
                sections_generated=self._extract_sections(content),
                references_used=self._extract_references(context),
                warnings=[],
                metadata={
                    "document_type": "design",
                    "template_used": template_config,
                    "has_reference_resources": context.reference_resources is not None,
                    "existing_spec_used": bool(existing_spec_path),
                    "generation_mode": context.generation_mode
                }
            )
            
            logger.info(f"DESIGN generation completed: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"DESIGN generation failed: {e}")
            raise ContentGenerationError("design", "generation", str(e))
    
    async def _create_processing_context(self,
                                        user_input: str,
                                        project_context: str,
                                        reference_folder: str,
                                        template_config: str) -> ProcessingContext:
        """Create processing context with resource analysis."""
        # Analyze reference resources if folder exists
        reference_resources = None
        if reference_folder:
            reference_path = Path(reference_folder)
            if reference_path.exists():
                try:
                    reference_resources = await self.resource_analyzer.analyze_folder(reference_path)
                    logger.info(f"Analyzed {reference_resources.total_files} reference files")
                except ResourceAccessError as e:
                    logger.warning(f"Failed to analyze reference resources: {e}")
        
        return ProcessingContext(
            user_input=user_input,
            reference_resources=reference_resources,
            template_config=template_config,
            project_context=project_context,
            generation_mode="full"
        )
    
    async def _enhance_with_existing_document(self, 
                                             input_text: str, 
                                             existing_doc_path: str) -> str:
        """Enhance input with content from existing document."""
        if not existing_doc_path or not Path(existing_doc_path).exists():
            return input_text
        
        try:
            existing_content = Path(existing_doc_path).read_text(encoding='utf-8')
            enhanced_input = f"{input_text}\n\n--- Existing Document Context ---\n{existing_content}"
            logger.info(f"Enhanced input with existing document: {existing_doc_path}")
            return enhanced_input
        except Exception as e:
            logger.warning(f"Failed to read existing document {existing_doc_path}: {e}")
            return input_text
    
    async def _save_document(self, file_path: Path, content: str) -> None:
        """Save document content to file."""
        try:
            # Ensure output directory exists before saving
            self._ensure_output_directory()
            
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"Document saved to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save document to {file_path}: {e}")
            raise DocumentGeneratorError(
                f"Failed to save document: {str(e)}",
                [
                    "Check file permissions",
                    "Ensure directory exists",
                    "Verify available disk space"
                ]
            )

    def _generate_summary(self, content: str, doc_type: str) -> str:
        """Generate a summary of the document content."""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # Count sections (lines starting with #)
        sections = [line for line in non_empty_lines if line.strip().startswith('#')]

        # Count words
        word_count = len(content.split())

        # Count characters
        char_count = len(content)

        summary = (
            f"Generated {doc_type} document with {len(sections)} sections, "
            f"{word_count} words, and {char_count} characters."
        )

        if sections:
            main_sections = [s.strip('#').strip() for s in sections[:3]]
            summary += f" Main sections: {', '.join(main_sections)}"
            if len(sections) > 3:
                summary += f" and {len(sections) - 3} more."

        return summary

    def _extract_sections(self, content: str) -> List[str]:
        """Extract section names from document content."""
        sections = []
        lines = content.split('\n')

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                # Extract section title (remove # and clean up)
                section_title = stripped.lstrip('#').strip()
                if section_title:
                    sections.append(section_title)

        return sections

    def _extract_references(self, context: ProcessingContext) -> List[str]:
        """Extract references used during generation."""
        references = []

        if context.reference_resources:
            # Add reference files that were used
            for category, files in context.reference_resources.categorized_files.items():
                for file_content in files:
                    references.append(str(file_content.file_path))

        return references

    async def generate_document_with_fallbacks(self,
                                              doc_type: str,
                                              input_data: str,
                                              context_data: Dict[str, Any]) -> DocumentResult:
        """Generate document with graceful fallback handling."""
        warnings = []

        try:
            # Try with full context including reference resources
            if doc_type == "prd":
                result = await self.generate_prd(
                    input_data,
                    context_data.get('project_context', ''),
                    context_data.get('reference_folder', 'reference_resources'),
                    context_data.get('template_config', 'default')
                )
            elif doc_type == "spec":
                result = await self.generate_spec(
                    input_data,
                    context_data.get('existing_prd_path', ''),
                    context_data.get('reference_folder', 'reference_resources'),
                    context_data.get('template_config', 'default')
                )
            elif doc_type == "design":
                result = await self.generate_design(
                    input_data,
                    context_data.get('existing_spec_path', ''),
                    context_data.get('reference_folder', 'reference_resources'),
                    context_data.get('template_config', 'default')
                )
            else:
                raise DocumentGeneratorError(f"Unknown document type: {doc_type}")

            return result

        except ResourceAccessError as e:
            warnings.append(f"Resource access failed: {e}")
            # Fallback to generation without reference resources
            logger.warning("Falling back to generation without reference resources")
            context_data['reference_folder'] = ""
            return await self.generate_document_with_fallbacks(doc_type, input_data, context_data)

        except TemplateValidationError as e:
            warnings.append(f"Template validation failed: {e}")
            # Fallback to default template
            logger.warning("Falling back to default template")
            context_data['template_config'] = "default"
            return await self.generate_document_with_fallbacks(doc_type, input_data, context_data)

    async def generate_prd_prompt(self,
                                  user_input: str,
                                  project_context: str = "",
                                  reference_folder: str = "reference_resources",
                                  template_config: str = "default") -> PromptResult:
        """Generate intelligent prompt for PRD creation."""
        try:
            logger.info("Starting PRD prompt generation")

            # Create processing context
            context = await self._create_processing_context(
                user_input, project_context, reference_folder, template_config
            )

            # Generate intelligent prompt
            prompt_result = await self.content_processor.generate_prd_prompt(context)

            logger.info("PRD prompt generation completed")
            return prompt_result

        except Exception as e:
            logger.error(f"PRD prompt generation failed: {e}")
            raise ContentGenerationError("prd", "prompt_generation", str(e))

    async def generate_spec_prompt(self,
                                   requirements_input: str,
                                   existing_prd_path: str = "",
                                   reference_folder: str = "reference_resources",
                                   template_config: str = "default") -> PromptResult:
        """Generate intelligent prompt for SPEC creation."""
        try:
            logger.info("Starting SPEC prompt generation")

            # Enhance input with existing PRD if provided
            enhanced_input = await self._enhance_with_existing_document(
                requirements_input, existing_prd_path
            )

            # Create processing context
            context = await self._create_processing_context(
                enhanced_input, "", reference_folder, template_config
            )

            # Generate intelligent prompt
            prompt_result = await self.content_processor.generate_spec_prompt(context)

            logger.info("SPEC prompt generation completed")
            return prompt_result

        except Exception as e:
            logger.error(f"SPEC prompt generation failed: {e}")
            raise ContentGenerationError("spec", "prompt_generation", str(e))

    async def generate_design_prompt(self,
                                     specification_input: str,
                                     existing_spec_path: str = "",
                                     reference_folder: str = "reference_resources",
                                     template_config: str = "default") -> PromptResult:
        """Generate intelligent prompt for DESIGN creation."""
        try:
            logger.info("Starting DESIGN prompt generation")

            # Enhance input with existing SPEC if provided
            enhanced_input = await self._enhance_with_existing_document(
                specification_input, existing_spec_path
            )

            # Create processing context
            context = await self._create_processing_context(
                enhanced_input, "", reference_folder, template_config
            )

            # Generate intelligent prompt
            prompt_result = await self.content_processor.generate_design_prompt(context)

            logger.info("DESIGN prompt generation completed")
            return prompt_result

        except Exception as e:
            logger.error(f"DESIGN prompt generation failed: {e}")
            raise ContentGenerationError("design", "prompt_generation", str(e))

    async def save_ai_generated_content(self, ai_content: AIGeneratedContent) -> DocumentResult:
        """Save AI-generated content to file with optional validation."""
        try:
            logger.info(f"Saving AI-generated {ai_content.document_type} content")

            # Validate content if requested
            validation_result = None
            if ai_content.validation_requested:
                validation_result = await self.validate_ai_content(
                    ai_content.document_type, ai_content.content
                )

            # Save document to file
            file_path = self.output_directory / ai_content.filename
            await self._save_document(file_path, ai_content.content)

            # Create document result
            result = DocumentResult(
                file_path=file_path,
                content=ai_content.content,
                summary=f"AI-generated {ai_content.document_type.upper()} document",
                sections_generated=validation_result.sections_found if validation_result else [],
                references_used=[],
                warnings=validation_result.quality_issues if validation_result else [],
                metadata={
                    "document_type": ai_content.document_type,
                    "generation_method": "ai_generated",
                    "user_notes": ai_content.user_notes,
                    "validation_performed": ai_content.validation_requested,
                    "is_valid": validation_result.is_valid if validation_result else True
                }
            )

            logger.info(f"AI-generated content saved: {file_path}")
            return result

        except Exception as e:
            logger.error(f"Failed to save AI-generated content: {e}")
            raise ContentGenerationError(ai_content.document_type, "save_ai_content", str(e))

    async def validate_ai_content(self, document_type: str, content: str) -> ContentValidationResult:
        """Validate AI-generated content structure and quality."""
        try:
            logger.info(f"Validating AI-generated {document_type} content")

            # Use content processor to validate structure
            validation_result = await self.content_processor.validate_ai_generated_content(
                document_type, content
            )

            logger.info(f"Content validation completed: {'valid' if validation_result.is_valid else 'invalid'}")
            return validation_result

        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            # Return a failed validation result
            return ContentValidationResult(
                is_valid=False,
                document_type=document_type,
                quality_issues=[f"Validation error: {str(e)}"],
                suggestions=["Check content format and structure"]
            )

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get statistics about document generation capabilities."""
        return {
            'supported_document_types': ['prd', 'spec', 'design'],
            'available_templates': [t['name'] for t in self.template_manager.list_templates()],
            'supported_file_formats': self.resource_analyzer.file_registry.get_supported_extensions(),
            'output_directory': str(self.output_directory),
            'template_manager_info': {
                'templates_count': len(self.template_manager.list_templates()),
                'custom_templates_path': str(self.template_manager.custom_templates_path) if self.template_manager.custom_templates_path else None
            }
        }
