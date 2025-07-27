"""
Core data models for the MCP Document Generator.

This module contains the primary data structures used throughout the system
for representing documents, resources, templates, and validation results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DocumentResult:
    """Result of document generation operation."""
    
    file_path: Path
    content: str
    summary: str
    sections_generated: List[str]
    references_used: List[str]
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP tool responses."""
        return {
            "file_path": str(self.file_path),
            "content_length": len(self.content),
            "summary": self.summary,
            "sections_generated": self.sections_generated,
            "references_used": self.references_used,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "generation_time": self.generation_time.isoformat(),
        }


@dataclass
class FileContent:
    """Represents processed content from a file."""
    
    file_path: Path
    extracted_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: datetime = field(default_factory=datetime.now)
    file_size: int = 0
    encoding: str = "utf-8"
    
    def __post_init__(self):
        """Calculate file size if not provided."""
        if self.file_size == 0 and self.file_path.exists():
            self.file_size = self.file_path.stat().st_size


@dataclass
class ResourceAnalysis:
    """Result of analyzing reference resources."""
    
    total_files: int
    categorized_files: Dict[str, List[FileContent]]
    content_summary: str
    processing_errors: List[str] = field(default_factory=list)
    supported_formats: List[str] = field(default_factory=list)
    analysis_time: datetime = field(default_factory=datetime.now)
    
    def get_files_by_category(self, category: str) -> List[FileContent]:
        """Get files of a specific category."""
        return self.categorized_files.get(category, [])
    
    def get_all_text_content(self) -> str:
        """Get combined text content from all files."""
        all_text = []
        for category_files in self.categorized_files.values():
            for file_content in category_files:
                all_text.append(f"# {file_content.file_path.name}\n")
                all_text.append(file_content.extracted_text)
                all_text.append("\n---\n")
        return "\n".join(all_text)


@dataclass
class Template:
    """Represents a document template."""
    
    name: str
    template_type: str  # 'prd', 'spec', 'design'
    sections: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"
    created_time: datetime = field(default_factory=datetime.now)
    
    def get_section(self, section_name: str) -> Optional[str]:
        """Get a specific section template."""
        return self.sections.get(section_name)
    
    def validate_structure(self) -> List[str]:
        """Validate template structure and return any issues."""
        issues = []
        
        # Check required sections based on template type
        required_sections = self._get_required_sections()
        for section in required_sections:
            if section not in self.sections:
                issues.append(f"Missing required section: {section}")
        
        # Check for empty sections
        for section_name, content in self.sections.items():
            if not content.strip():
                issues.append(f"Empty section: {section_name}")
        
        return issues
    
    def _get_required_sections(self) -> List[str]:
        """Get required sections based on template type."""
        if self.template_type == "prd":
            return ["introduction", "objectives", "user_stories", "acceptance_criteria"]
        elif self.template_type == "spec":
            return ["overview", "architecture", "components", "interfaces"]
        elif self.template_type == "design":
            return ["system_design", "user_interface_design", "data_flow"]
        return []


@dataclass
class ValidationResult:
    """Result of content validation."""
    
    is_valid: bool
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    validation_time: datetime = field(default_factory=datetime.now)
    
    def add_issue(self, issue: str, suggestion: Optional[str] = None):
        """Add a validation issue with optional suggestion."""
        self.issues.append(issue)
        if suggestion:
            self.suggestions.append(suggestion)
        self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for responses."""
        return {
            "is_valid": self.is_valid,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "validation_time": self.validation_time.isoformat(),
        }


@dataclass
class ProcessingContext:
    """Context information for document processing."""

    user_input: str
    reference_resources: Optional[ResourceAnalysis] = None
    template_config: str = "default"
    project_context: str = ""
    generation_mode: str = "full"  # 'full', 'minimal', 'enhanced'
    custom_sections: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for processing."""
        return {
            "user_input": self.user_input,
            "template_config": self.template_config,
            "project_context": self.project_context,
            "generation_mode": self.generation_mode,
            "custom_sections": self.custom_sections,
            "metadata": self.metadata,
            "has_reference_resources": self.reference_resources is not None,
        }


@dataclass
class PromptResult:
    """Result of prompt generation for AI processing."""

    document_type: str  # 'prd', 'spec', 'design'
    prompt: str
    template_structure: Dict[str, str]
    extracted_data: Dict[str, Any]
    context_summary: str
    references_used: List[str] = field(default_factory=list)
    suggested_filename: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP tool responses."""
        return {
            "action": "generate_with_claude",
            "document_type": self.document_type,
            "prompt": self.prompt,
            "template_structure": self.template_structure,
            "extracted_data": self.extracted_data,
            "context_summary": self.context_summary,
            "references_used": self.references_used,
            "suggested_filename": self.suggested_filename,
            "metadata": self.metadata,
            "generation_time": self.generation_time.isoformat(),
            "next_action": f"Please process this prompt to generate the {self.document_type.upper()} content, then use the save_generated_document tool to save it."
        }


@dataclass
class GenerationRequest:
    """Request for AI content generation."""

    document_type: str
    user_input: str
    project_context: str = ""
    reference_folder: str = "reference_resources"
    template_config: str = "default"
    existing_document_path: str = ""
    generation_mode: str = "intelligent"  # 'intelligent', 'template_only'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_type": self.document_type,
            "user_input": self.user_input,
            "project_context": self.project_context,
            "reference_folder": self.reference_folder,
            "template_config": self.template_config,
            "existing_document_path": self.existing_document_path,
            "generation_mode": self.generation_mode,
        }


@dataclass
class AIGeneratedContent:
    """Content generated by AI that needs to be saved."""

    document_type: str
    content: str
    filename: str
    user_notes: str = ""
    validation_requested: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_type": self.document_type,
            "content_length": len(self.content),
            "filename": self.filename,
            "user_notes": self.user_notes,
            "validation_requested": self.validation_requested,
            "metadata": self.metadata,
            "generation_time": self.generation_time.isoformat(),
        }


@dataclass
class ContentValidationResult:
    """Result of validating AI-generated content."""

    is_valid: bool
    document_type: str
    sections_found: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    quality_issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    validation_time: datetime = field(default_factory=datetime.now)

    def add_issue(self, issue: str, suggestion: Optional[str] = None):
        """Add a validation issue with optional suggestion."""
        self.quality_issues.append(issue)
        if suggestion:
            self.suggestions.append(suggestion)
        self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for responses."""
        return {
            "is_valid": self.is_valid,
            "document_type": self.document_type,
            "sections_found": self.sections_found,
            "missing_sections": self.missing_sections,
            "quality_issues": self.quality_issues,
            "suggestions": self.suggestions,
            "validation_time": self.validation_time.isoformat(),
        }
