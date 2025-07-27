"""
Integration tests for the Document Generator MCP.

These tests verify that the complete document generation workflow works
end-to-end.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

from document_generator_mcp.services.document_generator import DocumentGeneratorService
from document_generator_mcp.services.resource_analyzer import ResourceAnalyzerService


class TestDocumentGenerationIntegration:
    """Integration tests for document generation."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create reference resources folder with sample files
        ref_dir = temp_dir / "reference_resources"
        ref_dir.mkdir()
        
        # Create sample markdown file
        (ref_dir / "requirements.md").write_text("""
# Sample Requirements

## User Stories
- As a user, I want to login, so that I can access the system
- As an admin, I want to manage users, so that I can control access

## Acceptance Criteria
- WHEN a user enters valid credentials THEN the system SHALL authenticate them
- IF credentials are invalid THEN the system SHALL show an error message
        """)
        
        # Create sample JSON file
        (ref_dir / "config.json").write_text("""
{
    "database": {
        "type": "postgresql",
        "host": "localhost",
        "port": 5432
    },
    "features": {
        "authentication": true,
        "user_management": true
    }
}
        """)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_prd_generation_with_resources(self, temp_workspace):
        """Test PRD generation with reference resources."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        user_input = """
        Create a user management system with the following features:
        - User registration and authentication
        - Role-based access control
        - User profile management
        - Admin dashboard for user management
        
        The system should be secure and scalable.
        """
        
        result = await service.generate_prd(
            user_input=user_input,
            project_context="Web application for enterprise use",
            reference_folder=str(temp_workspace / "reference_resources")
        )
        
        # Verify result
        assert result is not None
        assert result.file_path.exists()
        assert result.content is not None
        assert len(result.content) > 100  # Should have substantial content
        assert "user management" in result.content.lower()
        assert len(result.sections_generated) > 0
        
        # Verify file was created
        prd_file = temp_workspace / "PRD.md"
        assert prd_file.exists()
        
        # Verify content structure
        content = prd_file.read_text()
        assert "# " in content  # Should have headers
        assert "introduction" in content.lower() or "overview" in content.lower()
    
    @pytest.mark.asyncio
    async def test_spec_generation_from_prd(self, temp_workspace):
        """Test SPEC generation using existing PRD."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # First generate a PRD
        prd_result = await service.generate_prd(
            user_input="Create a simple task management API with CRUD operations",
            reference_folder=str(temp_workspace / "reference_resources")
        )
        
        # Then generate SPEC using the PRD
        spec_result = await service.generate_spec(
            requirements_input="Technical specification for the task management API",
            existing_prd_path=str(prd_result.file_path),
            reference_folder=str(temp_workspace / "reference_resources")
        )
        
        # Verify SPEC result
        assert spec_result is not None
        assert spec_result.file_path.exists()
        assert spec_result.content is not None
        assert len(spec_result.content) > 100
        assert "api" in spec_result.content.lower() or "technical" in spec_result.content.lower()
        
        # Verify both files exist
        assert (temp_workspace / "PRD.md").exists()
        assert (temp_workspace / "SPEC.md").exists()
    
    @pytest.mark.asyncio
    async def test_design_generation_from_spec(self, temp_workspace):
        """Test DESIGN generation using existing SPEC."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Generate PRD first
        await service.generate_prd(
            user_input="Create a web dashboard for data visualization",
            reference_folder=str(temp_workspace / "reference_resources")
        )
        
        # Generate SPEC
        spec_result = await service.generate_spec(
            requirements_input="Technical specification for data visualization dashboard",
            existing_prd_path=str(temp_workspace / "PRD.md"),
            reference_folder=str(temp_workspace / "reference_resources")
        )
        
        # Generate DESIGN
        design_result = await service.generate_design(
            specification_input="Design document for the dashboard interface",
            existing_spec_path=str(spec_result.file_path),
            reference_folder=str(temp_workspace / "reference_resources")
        )
        
        # Verify DESIGN result
        assert design_result is not None
        assert design_result.file_path.exists()
        assert design_result.content is not None
        assert len(design_result.content) > 100
        assert "design" in design_result.content.lower() or "interface" in design_result.content.lower()
        
        # Verify all three files exist
        assert (temp_workspace / "PRD.md").exists()
        assert (temp_workspace / "SPEC.md").exists()
        assert (temp_workspace / "DESIGN.md").exists()
    
    @pytest.mark.asyncio
    async def test_resource_analysis_integration(self, temp_workspace):
        """Test resource analysis integration."""
        analyzer = ResourceAnalyzerService()
        
        analysis = await analyzer.analyze_folder(temp_workspace / "reference_resources")
        
        # Verify analysis results
        assert analysis is not None
        assert analysis.total_files >= 2  # We created 2 files
        assert len(analysis.categorized_files) > 0
        assert analysis.content_summary is not None
        assert len(analysis.content_summary) > 0
        
        # Check that files were categorized
        all_files = []
        for category_files in analysis.categorized_files.values():
            all_files.extend(category_files)
        
        assert len(all_files) >= 2
        
        # Check that content was extracted
        for file_content in all_files:
            assert file_content.extracted_text is not None
            assert len(file_content.extracted_text) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_resources(self, temp_workspace):
        """Test error handling when reference resources are missing."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Try to generate with non-existent reference folder
        result = await service.generate_prd(
            user_input="Create a simple application",
            reference_folder="non_existent_folder"
        )
        
        # Should still work, just without reference resources
        assert result is not None
        assert result.file_path.exists()
        assert result.content is not None
        
        # Should have a warning or indication that resources weren't used
        assert result.metadata.get('has_reference_resources') is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
