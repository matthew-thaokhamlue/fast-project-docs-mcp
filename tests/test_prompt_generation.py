"""
Tests for the prompt generation functionality in the hybrid MCP workflow.

These tests verify that the system correctly generates intelligent prompts
for Claude Desktop to process, including context analysis and template integration.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from document_generator_mcp.services.document_generator import DocumentGeneratorService
from document_generator_mcp.services.content_processor import ContentProcessor
from document_generator_mcp.models.core import PromptResult, ProcessingContext, ResourceAnalysis
from document_generator_mcp.models.document_structures import PRDStructure, SPECStructure, DESIGNStructure
from document_generator_mcp.templates.manager import TemplateManager


class TestPromptGeneration:
    """Test prompt generation for different document types."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_resource_analysis(self):
        """Create a mock resource analysis."""
        return ResourceAnalysis(
            total_files=2,
            categorized_files={
                "documentation": [],
                "configuration": []
            },
            content_summary="Test reference materials including API docs and config files",
            processing_errors=[],
            supported_formats=[".md", ".json"]
        )
    
    @pytest.mark.asyncio
    async def test_prd_prompt_generation(self, temp_workspace):
        """Test PRD prompt generation with context analysis."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        result = await service.generate_prd_prompt(
            user_input="As a user, I want to login with email and password so that I can access my account",
            project_context="Building a secure web application",
            template_config="default_prd"
        )
        
        # Verify PromptResult structure
        assert isinstance(result, PromptResult)
        assert result.document_type == "prd"
        assert result.suggested_filename == "PRD.md"
        assert len(result.prompt) > 500  # Should be a substantial prompt
        
        # Verify prompt content
        assert "Product Requirements Document" in result.prompt
        assert "login with email and password" in result.prompt
        assert "secure web application" in result.prompt
        assert "Kiro's standards" in result.prompt
        
        # Verify template structure is included
        assert isinstance(result.template_structure, dict)
        assert len(result.template_structure) > 0
        
        # Verify extracted data
        assert isinstance(result.extracted_data, dict)
        assert "objectives" in result.extracted_data or "user_stories" in result.extracted_data
    
    @pytest.mark.asyncio
    async def test_spec_prompt_generation(self, temp_workspace):
        """Test SPEC prompt generation."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        result = await service.generate_spec_prompt(
            requirements_input="Technical specification for user authentication system",
            template_config="default_spec"
        )
        
        # Verify PromptResult structure
        assert isinstance(result, PromptResult)
        assert result.document_type == "spec"
        assert result.suggested_filename == "SPEC.md"
        
        # Verify prompt content
        assert "Technical Specification Document" in result.prompt
        assert "authentication system" in result.prompt
        assert "architecture" in result.prompt.lower()
        assert "components" in result.prompt.lower()
    
    @pytest.mark.asyncio
    async def test_design_prompt_generation(self, temp_workspace):
        """Test DESIGN prompt generation."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        result = await service.generate_design_prompt(
            specification_input="Design document for user interface and system architecture",
            template_config="default_design"
        )
        
        # Verify PromptResult structure
        assert isinstance(result, PromptResult)
        assert result.document_type == "design"
        assert result.suggested_filename == "DESIGN.md"
        
        # Verify prompt content
        assert "Design Document" in result.prompt
        assert "user interface" in result.prompt
        assert "system architecture" in result.prompt
        assert "UI/UX" in result.prompt or "interface" in result.prompt
    
    @pytest.mark.asyncio
    async def test_prompt_with_reference_resources(self, temp_workspace, mock_resource_analysis):
        """Test prompt generation with reference resources."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Mock the resource analyzer to return our test data
        service.resource_analyzer.analyze_folder = AsyncMock(return_value=mock_resource_analysis)
        
        # Create a fake reference folder
        ref_folder = temp_workspace / "reference_resources"
        ref_folder.mkdir()
        (ref_folder / "api_docs.md").write_text("# API Documentation\nTest API docs")
        
        result = await service.generate_prd_prompt(
            user_input="Create a dashboard for data visualization",
            reference_folder=str(ref_folder),
            template_config="default_prd"
        )
        
        # Verify reference materials are included
        assert "Reference Materials Summary" in result.prompt
        assert "API docs and config files" in result.prompt
        assert len(result.references_used) > 0
        assert result.metadata["has_reference_resources"] is True
    
    def test_prompt_context_analysis(self):
        """Test context analysis for prompt generation."""
        processor = ContentProcessor()
        
        context = ProcessingContext(
            user_input="As a user, I want to reset my password so that I can regain access",
            project_context="Security-focused application",
            template_config="default_prd"
        )
        
        # Test PRD structure extraction
        prd_structure = processor._extract_prd_structure(context)
        
        assert isinstance(prd_structure, PRDStructure)
        # Should extract user story information
        assert len(prd_structure.user_stories) > 0 or "reset" in str(prd_structure.__dict__)
    
    def test_prompt_template_integration(self):
        """Test that prompts correctly integrate template structure."""
        template_manager = TemplateManager()
        template = template_manager.get_template("default_prd")
        
        processor = ContentProcessor(template_manager)
        context = ProcessingContext(
            user_input="Test input",
            template_config="default_prd"
        )
        
        # Test prompt creation includes template sections
        prd_structure = PRDStructure()
        prompt = processor._create_prd_prompt(context, prd_structure, template)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 200
        assert "Introduction" in prompt
        assert "Objectives" in prompt
        assert "User Stories" in prompt
        assert "Kiro's standards" in prompt


class TestPromptQuality:
    """Test the quality and completeness of generated prompts."""
    
    def test_prompt_contains_required_sections(self):
        """Test that prompts contain all required guidance sections."""
        processor = ContentProcessor()
        context = ProcessingContext(user_input="Test input")
        prd_structure = PRDStructure()
        template = MagicMock()
        template.sections = {"introduction": "test", "objectives": "test"}
        
        prompt = processor._create_prd_prompt(context, prd_structure, template)
        
        # Should contain structured guidance
        assert "User Input:" in prompt
        assert "Project Context:" in prompt
        assert "Guidelines:" in prompt
        assert "sections:" in prompt.lower()
    
    def test_prompt_length_appropriate(self):
        """Test that prompts are substantial but not excessive."""
        processor = ContentProcessor()
        context = ProcessingContext(
            user_input="Create a comprehensive user management system",
            project_context="Enterprise application with role-based access"
        )
        prd_structure = PRDStructure()
        template = MagicMock()
        template.sections = {"intro": "test", "objectives": "test"}
        
        prompt = processor._create_prd_prompt(context, prd_structure, template)
        
        # Should be substantial but reasonable
        assert 500 <= len(prompt) <= 5000
        
    def test_prompt_includes_context_data(self):
        """Test that prompts include extracted context data."""
        processor = ContentProcessor()
        
        # Create context with rich data
        context = ProcessingContext(
            user_input="As an admin, I want to manage users so that I can control access",
            project_context="Role-based access control system"
        )
        
        prd_structure = PRDStructure()
        prd_structure.objectives = ["Secure access control", "User management"]
        prd_structure.add_user_story("admin", "manage users", "control access")
        
        template = MagicMock()
        template.sections = {}
        
        prompt = processor._create_prd_prompt(context, prd_structure, template)
        
        # Should include extracted data
        assert "admin" in prompt
        assert "manage users" in prompt
        assert "Secure access control" in prompt or "User management" in prompt
