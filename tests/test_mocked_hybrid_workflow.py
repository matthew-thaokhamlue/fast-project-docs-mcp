"""
Mock-based tests for the complete hybrid workflow.

These tests use mocking to simulate the complete workflow including AI responses,
allowing us to test the integration without depending on actual AI generation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from pytest_mock import MockerFixture

from document_generator_mcp.services.document_generator import DocumentGeneratorService
from document_generator_mcp.models.core import PromptResult, AIGeneratedContent, ResourceAnalysis
from document_generator_mcp.server.tools import register_tools
from mcp.server.fastmcp import FastMCP


class TestMockedHybridWorkflow:
    """Test complete hybrid workflow with mocked components."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_resource_analysis(self):
        """Mock resource analysis for testing."""
        return ResourceAnalysis(
            total_files=3,
            categorized_files={
                "documentation": [],
                "configuration": [],
                "code": []
            },
            content_summary="Mock reference materials including docs and config",
            processing_errors=[],
            supported_formats=[".md", ".json", ".py"]
        )
    
    @pytest.mark.asyncio
    async def test_mocked_end_to_end_prd_workflow(self, temp_workspace, mock_resource_analysis, mocker: MockerFixture):
        """Test complete PRD workflow with mocked AI response."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Mock the resource analyzer
        mocker.patch.object(
            service.resource_analyzer, 
            'analyze_folder', 
            return_value=mock_resource_analysis
        )
        
        # Step 1: Generate prompt (real)
        prompt_result = await service.generate_prd_prompt(
            user_input="As a developer, I want to create APIs so that I can build applications",
            project_context="Microservices architecture",
            reference_folder="mock_folder",
            template_config="default_prd"
        )
        
        # Verify prompt generation
        assert isinstance(prompt_result, PromptResult)
        assert "developer" in prompt_result.prompt
        assert "APIs" in prompt_result.prompt
        assert "microservices" in prompt_result.prompt.lower()
        
        # Step 2: Mock AI response (simulate Claude Desktop)
        mock_ai_response = """# Product Requirements Document

## Introduction
This PRD defines requirements for an API development platform that enables developers to create robust APIs for application development within a microservices architecture.

## Objectives
- Provide intuitive API creation tools
- Support microservices architecture patterns
- Enable rapid API development and deployment
- Ensure API security and performance

## User Stories
### Story 1: API Creation
**As a** developer  
**I want** to create new APIs with defined endpoints  
**So that** I can build applications that consume these services

**Acceptance Criteria:**
- Developer can define API endpoints and methods
- System generates OpenAPI specification
- API is automatically deployed to development environment
- Developer receives API documentation

## Success Metrics
- API creation time < 10 minutes
- Developer satisfaction score > 4.5/5
- API uptime > 99.9%

## Constraints and Dependencies
- Must support REST and GraphQL
- Requires container orchestration platform
- Database abstraction layer needed
"""
        
        # Step 3: Save AI-generated content (real)
        ai_content = AIGeneratedContent(
            document_type="prd",
            content=mock_ai_response,
            filename="API_PLATFORM_PRD.md",
            user_notes="Generated from mocked AI response",
            validation_requested=True
        )
        
        save_result = await service.save_ai_generated_content(ai_content)
        
        # Verify complete workflow
        assert save_result.file_path.exists()
        assert "API development platform" in save_result.content
        assert save_result.metadata["validation_performed"] is True
        assert len(save_result.sections_generated) > 0
    
    @pytest.mark.asyncio
    async def test_mocked_mcp_tools_integration(self, temp_workspace, mocker: MockerFixture):
        """Test MCP tools with mocked responses."""
        # Create MCP server and register tools
        mcp = FastMCP("test-server")
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Mock the service methods
        mock_prompt_result = PromptResult(
            document_type="prd",
            prompt="Mocked intelligent prompt for testing",
            template_structure={"intro": "test", "objectives": "test"},
            extracted_data={"test": "data"},
            context_summary="Mocked context",
            suggested_filename="MOCKED_PRD.md"
        )
        
        mocker.patch.object(service, 'generate_prd_prompt', return_value=mock_prompt_result)
        
        # Register tools with mocked service
        register_tools(mcp, service)
        
        # Test that tools are registered
        assert len(mcp.list_tools()) > 0
        
        # Find the generate_prd tool
        tools = mcp.list_tools()
        prd_tool = next((tool for tool in tools if tool.name == "generate_prd"), None)
        assert prd_tool is not None
        
        # Test tool execution would call our mocked method
        # (In real usage, this would be called by the MCP client)
        result = await service.generate_prd_prompt(
            user_input="Test input",
            template_config="default_prd"
        )
        
        assert result == mock_prompt_result
        assert result.prompt == "Mocked intelligent prompt for testing"
    
    @pytest.mark.asyncio
    async def test_mocked_validation_workflow(self, temp_workspace, mocker: MockerFixture):
        """Test validation workflow with mocked content processor."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Mock the content processor validation
        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validation_result.sections_found = ["Introduction", "Objectives"]
        mock_validation_result.missing_sections = []
        mock_validation_result.quality_issues = []
        
        mocker.patch.object(
            service.content_processor,
            'validate_ai_generated_content',
            return_value=mock_validation_result
        )
        
        # Test validation
        result = await service.validate_ai_content("prd", "Mock content")
        
        assert result.is_valid is True
        assert "Introduction" in result.sections_found
        assert len(result.missing_sections) == 0
    
    @pytest.mark.asyncio
    async def test_mocked_error_scenarios(self, temp_workspace, mocker: MockerFixture):
        """Test error handling with mocked failures."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Mock template manager to raise an error
        mocker.patch.object(
            service.template_manager,
            'get_template',
            side_effect=Exception("Template not found")
        )
        
        # Test that error is properly handled
        with pytest.raises(Exception) as exc_info:
            await service.generate_prd_prompt(
                user_input="Test input",
                template_config="invalid_template"
            )
        
        assert "Template not found" in str(exc_info.value)
    
    def test_mock_ai_response_patterns(self, mocker: MockerFixture):
        """Test different AI response patterns with mocking."""
        # Mock different types of AI responses
        responses = {
            "complete_prd": """# PRD\n## Introduction\nComplete PRD content""",
            "incomplete_prd": """# PRD\n## Introduction\nTODO: Add more content""",
            "malformed_prd": """Random text without proper structure""",
            "empty_response": "",
        }
        
        for response_type, content in responses.items():
            ai_content = AIGeneratedContent(
                document_type="prd",
                content=content,
                filename=f"{response_type}.md"
            )
            
            # Verify content structure
            if response_type == "complete_prd":
                assert "Complete PRD content" in ai_content.content
            elif response_type == "incomplete_prd":
                assert "TODO" in ai_content.content
            elif response_type == "empty_response":
                assert len(ai_content.content) == 0
    
    @pytest.mark.asyncio
    async def test_mocked_concurrent_workflows(self, temp_workspace, mocker: MockerFixture):
        """Test multiple concurrent workflows with mocking."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Mock multiple prompt generations
        mock_results = [
            PromptResult(
                document_type="prd",
                prompt=f"Prompt {i}",
                template_structure={},
                extracted_data={},
                context_summary=f"Context {i}",
                suggested_filename=f"PRD_{i}.md"
            )
            for i in range(3)
        ]
        
        # Mock the service to return different results
        side_effects = iter(mock_results)
        mocker.patch.object(
            service,
            'generate_prd_prompt',
            side_effect=lambda *args, **kwargs: next(side_effects)
        )
        
        # Test concurrent prompt generation
        import asyncio
        tasks = [
            service.generate_prd_prompt(user_input=f"Input {i}")
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all results are different
        assert len(results) == 3
        assert all(isinstance(r, PromptResult) for r in results)
        assert len(set(r.suggested_filename for r in results)) == 3
    
    @pytest.mark.asyncio
    async def test_mocked_resource_integration(self, temp_workspace, mocker: MockerFixture):
        """Test resource analysis integration with mocking."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Mock resource analyzer with rich data
        rich_analysis = ResourceAnalysis(
            total_files=10,
            categorized_files={
                "documentation": [MagicMock(file_path=Path("doc1.md"))],
                "code": [MagicMock(file_path=Path("app.py"))],
                "configuration": [MagicMock(file_path=Path("config.json"))]
            },
            content_summary="Rich project with docs, code, and config files",
            processing_errors=[],
            supported_formats=[".md", ".py", ".json"]
        )
        
        mocker.patch.object(
            service.resource_analyzer,
            'analyze_folder',
            return_value=rich_analysis
        )
        
        # Test prompt generation with rich resources
        result = await service.generate_prd_prompt(
            user_input="Create a web application",
            reference_folder="mock_folder"
        )
        
        # Verify resource data is included
        assert "Rich project" in result.prompt or len(result.references_used) > 0
        assert result.metadata.get("has_reference_resources") is True
