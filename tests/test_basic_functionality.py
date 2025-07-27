"""
Basic functionality tests for the Document Generator MCP.

These tests verify that the core components can be imported and initialized
without errors.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from document_generator_mcp.models.core import (
    DocumentResult, ResourceAnalysis, Template,
    PromptResult, AIGeneratedContent, ContentValidationResult
)
from document_generator_mcp.models.document_structures import PRDStructure, SPECStructure, DESIGNStructure
from document_generator_mcp.processors.registry import FileProcessorRegistry
from document_generator_mcp.templates.manager import TemplateManager
from document_generator_mcp.services.document_generator import DocumentGeneratorService


class TestBasicImports:
    """Test that all modules can be imported successfully."""
    
    def test_import_models(self):
        """Test importing core models."""
        # Original models
        assert DocumentResult is not None
        assert ResourceAnalysis is not None
        assert Template is not None
        assert PRDStructure is not None
        assert SPECStructure is not None
        assert DESIGNStructure is not None

        # New hybrid workflow models
        assert PromptResult is not None
        assert AIGeneratedContent is not None
        assert ContentValidationResult is not None
    
    def test_import_processors(self):
        """Test importing file processors."""
        registry = FileProcessorRegistry()
        assert registry is not None
        assert len(registry.get_supported_extensions()) > 0
    
    def test_import_templates(self):
        """Test importing template manager."""
        template_manager = TemplateManager()
        assert template_manager is not None
        templates = template_manager.list_templates()
        assert len(templates) > 0
    
    def test_import_services(self):
        """Test importing services."""
        service = DocumentGeneratorService()
        assert service is not None


class TestDataModels:
    """Test basic data model functionality."""
    
    def test_document_result_creation(self):
        """Test creating a DocumentResult."""
        result = DocumentResult(
            file_path=Path("test.md"),
            content="# Test Document",
            summary="Test summary",
            sections_generated=["Introduction"],
            references_used=[]
        )
        
        assert result.file_path == Path("test.md")
        assert result.content == "# Test Document"
        assert result.summary == "Test summary"
        assert "Introduction" in result.sections_generated
    
    def test_prd_structure_creation(self):
        """Test creating a PRD structure."""
        prd = PRDStructure()
        prd.introduction = "Test introduction"
        prd.objectives = ["Objective 1", "Objective 2"]
        
        assert prd.introduction == "Test introduction"
        assert len(prd.objectives) == 2
        assert "Objective 1" in prd.objectives
    
    def test_prd_user_story_addition(self):
        """Test adding user stories to PRD."""
        prd = PRDStructure()
        prd.add_user_story("user", "login", "access the system", ["Valid credentials required"])
        
        assert len(prd.user_stories) == 1
        story = prd.user_stories[0]
        assert story["role"] == "user"
        assert story["feature"] == "login"
        assert story["benefit"] == "access the system"
        assert "As a user, I want login, so that access the system" in story["story"]

    def test_prompt_result_creation(self):
        """Test creating a PromptResult for hybrid workflow."""
        prompt_result = PromptResult(
            document_type="prd",
            prompt="Create a comprehensive PRD...",
            template_structure={"introduction": "# Introduction\n{content}"},
            extracted_data={"objectives": ["Test objective"]},
            context_summary="Test context",
            suggested_filename="PRD.md"
        )

        assert prompt_result.document_type == "prd"
        assert "comprehensive PRD" in prompt_result.prompt
        assert prompt_result.suggested_filename == "PRD.md"
        assert "objectives" in prompt_result.extracted_data

        # Test to_dict conversion
        result_dict = prompt_result.to_dict()
        assert result_dict["action"] == "generate_with_claude"
        assert result_dict["document_type"] == "prd"
        assert "next_action" in result_dict

    def test_ai_generated_content_creation(self):
        """Test creating AIGeneratedContent for saving workflow."""
        ai_content = AIGeneratedContent(
            document_type="prd",
            content="# PRD\n\n## Introduction\nTest content",
            filename="TEST_PRD.md",
            user_notes="Generated for testing",
            validation_requested=True
        )

        assert ai_content.document_type == "prd"
        assert ai_content.filename == "TEST_PRD.md"
        assert ai_content.validation_requested is True
        assert "Test content" in ai_content.content

        # Test to_dict conversion
        content_dict = ai_content.to_dict()
        assert content_dict["document_type"] == "prd"
        assert content_dict["filename"] == "TEST_PRD.md"
        assert content_dict["validation_requested"] is True

    def test_content_validation_result_creation(self):
        """Test creating ContentValidationResult."""
        validation_result = ContentValidationResult(
            is_valid=False,
            document_type="prd",
            sections_found=["Introduction"],
            missing_sections=["Objectives", "User Stories"],
            quality_issues=["Content too short"]
        )

        assert validation_result.is_valid is False
        assert validation_result.document_type == "prd"
        assert "Introduction" in validation_result.sections_found
        assert "Objectives" in validation_result.missing_sections
        assert len(validation_result.quality_issues) == 1

        # Test adding issues
        validation_result.add_issue("New issue", "Fix suggestion")
        assert len(validation_result.quality_issues) == 2
        assert len(validation_result.suggestions) == 1
        assert validation_result.is_valid is False

    def test_document_structure_serialization(self):
        """Test that document structures can be serialized to dict."""
        # Test PRDStructure
        prd = PRDStructure()
        prd.introduction = "Test intro"
        prd.objectives = ["Obj 1", "Obj 2"]
        prd.add_user_story("user", "login", "access system")

        prd_dict = prd.to_dict()
        assert prd_dict["introduction"] == "Test intro"
        assert len(prd_dict["objectives"]) == 2
        assert len(prd_dict["user_stories"]) == 1

        # Test SPECStructure
        spec = SPECStructure()
        spec.overview = "Test overview"
        spec.add_component("API", "REST API component")

        spec_dict = spec.to_dict()
        assert spec_dict["overview"] == "Test overview"
        assert len(spec_dict["components"]) == 1
        assert spec_dict["components"][0]["name"] == "API"

        # Test DESIGNStructure
        design = DESIGNStructure()
        design.system_design = "Test system design"
        design.add_design_pattern("MVC", "Model-View-Controller", "Web architecture")

        design_dict = design.to_dict()
        assert design_dict["system_design"] == "Test system design"
        assert len(design_dict["design_patterns"]) == 1
        assert design_dict["design_patterns"][0]["name"] == "MVC"


class TestFileProcessors:
    """Test file processor functionality."""
    
    def test_processor_registry_initialization(self):
        """Test that processor registry initializes with default processors."""
        registry = FileProcessorRegistry()
        
        # Check that common extensions are supported
        supported = registry.get_supported_extensions()
        assert '.md' in supported
        assert '.txt' in supported
        assert '.json' in supported
        assert '.yaml' in supported
    
    def test_processor_selection(self):
        """Test that appropriate processors are selected for files."""
        registry = FileProcessorRegistry()
        
        # Test markdown file
        md_file = Path("test.md")
        assert registry.can_process(md_file)
        
        # Test unsupported file
        unknown_file = Path("test.unknown")
        assert not registry.can_process(unknown_file)


class TestTemplateManager:
    """Test template manager functionality."""
    
    def test_template_manager_initialization(self):
        """Test template manager initialization."""
        manager = TemplateManager()
        templates = manager.list_templates()
        
        # Should have default templates
        assert len(templates) >= 3  # PRD, SPEC, DESIGN
        
        template_types = [t['type'] for t in templates]
        assert 'prd' in template_types
        assert 'spec' in template_types
        assert 'design' in template_types
    
    def test_get_default_templates(self):
        """Test getting default templates."""
        manager = TemplateManager()
        
        # Test getting PRD template
        prd_template = manager.get_template('prd')
        assert prd_template.template_type == 'prd'
        assert 'introduction' in prd_template.sections
        
        # Test getting SPEC template
        spec_template = manager.get_template('spec')
        assert spec_template.template_type == 'spec'
        assert 'overview' in spec_template.sections
    
    def test_template_validation(self):
        """Test template validation."""
        manager = TemplateManager()
        template = manager.get_template('prd')
        
        validation_result = manager.validate_template(template)
        assert validation_result.is_valid


class TestDocumentGenerator:
    """Test document generator service."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.service = DocumentGeneratorService(output_directory=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_service_initialization(self):
        """Test that document generator service initializes correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DocumentGeneratorService(output_directory=Path(temp_dir))
            assert service.output_directory == Path(temp_dir)
            assert service.template_manager is not None
            assert service.resource_analyzer is not None
            assert service.content_processor is not None
    
    def test_generation_statistics(self):
        """Test getting generation statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DocumentGeneratorService(output_directory=Path(temp_dir))
            stats = service.get_generation_statistics()
            
            assert 'supported_document_types' in stats
            assert 'prd' in stats['supported_document_types']
            assert 'spec' in stats['supported_document_types']
            assert 'design' in stats['supported_document_types']
            
            assert 'available_templates' in stats
            assert len(stats['available_templates']) > 0


if __name__ == "__main__":
    pytest.main([__file__])
