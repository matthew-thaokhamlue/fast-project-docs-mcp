"""
Integration tests for the hybrid MCP workflow.

These tests verify the complete prompt generation → AI content → saving workflow
that represents the new hybrid approach where MCP generates prompts and Claude
Desktop generates the actual content.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch

from document_generator_mcp.services.document_generator import DocumentGeneratorService
from document_generator_mcp.models.core import PromptResult, AIGeneratedContent, DocumentResult


class TestHybridWorkflowIntegration:
    """Test the complete hybrid workflow integration."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create reference resources folder with sample files
        ref_dir = temp_dir / "reference_resources"
        ref_dir.mkdir()
        
        # Create sample markdown file
        (ref_dir / "requirements.md").write_text("""
# Requirements Document

## User Management
- Users can register with email
- Users can login with credentials
- Admin can manage user roles

## Security Requirements
- Passwords must be hashed
- Session management required
- HTTPS only communication
        """)
        
        # Create sample JSON file
        (ref_dir / "config.json").write_text("""
{
    "database": {
        "type": "postgresql",
        "host": "localhost"
    },
    "authentication": {
        "method": "jwt",
        "expiry": "24h"
    }
}
        """)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_prd_workflow(self, temp_workspace):
        """Test complete PRD workflow: prompt generation → AI content → saving."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Step 1: Generate intelligent prompt
        prompt_result = await service.generate_prd_prompt(
            user_input="As a user, I want to manage my tasks so that I can stay organized",
            project_context="Task management web application",
            reference_folder=str(temp_workspace / "reference_resources"),
            template_config="default_prd"
        )
        
        # Verify prompt generation
        assert isinstance(prompt_result, PromptResult)
        assert prompt_result.document_type == "prd"
        assert "task management" in prompt_result.prompt.lower()
        assert "organized" in prompt_result.prompt.lower()
        assert len(prompt_result.template_structure) > 0
        
        # Step 2: Simulate AI-generated content (what Claude Desktop would produce)
        ai_generated_content = """# Product Requirements Document

## Introduction
This PRD outlines the requirements for a task management web application that helps users stay organized by managing their tasks effectively.

## Objectives
- Enable users to create, edit, and delete tasks
- Provide task organization through categories and priorities
- Ensure intuitive user experience
- Support task tracking and completion status

## User Stories
### Story 1: Task Creation
**As a** user  
**I want** to create new tasks with titles and descriptions  
**So that** I can track what needs to be done

**Acceptance Criteria:**
- User can enter task title (required)
- User can add optional description
- Task is saved with creation timestamp
- User receives confirmation of task creation

### Story 2: Task Management
**As a** user  
**I want** to edit and delete my tasks  
**So that** I can keep my task list current

**Acceptance Criteria:**
- User can modify task title and description
- User can delete tasks they no longer need
- Changes are saved immediately
- User can undo accidental deletions

## Success Metrics
- Task creation time < 5 seconds
- User engagement > 80% weekly active users
- Task completion rate > 60%

## Constraints and Dependencies
- Must work on web browsers (Chrome, Firefox, Safari)
- Requires user authentication system
- Database for persistent storage
- Responsive design for mobile devices
"""
        
        # Step 3: Save AI-generated content
        ai_content = AIGeneratedContent(
            document_type="prd",
            content=ai_generated_content,
            filename="TASK_MANAGEMENT_PRD.md",
            user_notes="Generated from prompt about task management",
            validation_requested=True
        )
        
        save_result = await service.save_ai_generated_content(ai_content)
        
        # Verify saving
        assert isinstance(save_result, DocumentResult)
        assert save_result.file_path.exists()
        assert save_result.file_path.name == "TASK_MANAGEMENT_PRD.md"
        assert save_result.content == ai_generated_content
        
        # Verify file content
        saved_content = save_result.file_path.read_text()
        assert "task management" in saved_content.lower()
        assert "User Stories" in saved_content
        assert "Acceptance Criteria" in saved_content
        
        # Verify validation was performed
        assert save_result.metadata["validation_performed"] is True
        assert save_result.metadata["generation_method"] == "ai_generated"
    
    @pytest.mark.asyncio
    async def test_spec_workflow_with_existing_prd(self, temp_workspace):
        """Test SPEC workflow that references existing PRD."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # First create a PRD file to reference
        prd_content = """# Product Requirements Document
## Introduction
Task management system for organizing work.
## Objectives
- Task CRUD operations
- User authentication
"""
        prd_path = temp_workspace / "EXISTING_PRD.md"
        prd_path.write_text(prd_content)
        
        # Generate SPEC prompt that references the PRD
        spec_prompt = await service.generate_spec_prompt(
            requirements_input="Create technical specification for the task management system",
            existing_prd_path=str(prd_path),
            template_config="default_spec"
        )
        
        # Verify prompt includes PRD context
        assert isinstance(spec_prompt, PromptResult)
        assert spec_prompt.document_type == "spec"
        assert "task management" in spec_prompt.prompt.lower()
        
        # Simulate AI-generated SPEC content
        spec_content = """# Technical Specification

## Technical Overview
RESTful API for task management with PostgreSQL database and JWT authentication.

## System Architecture
- Frontend: React.js SPA
- Backend: Node.js with Express
- Database: PostgreSQL
- Authentication: JWT tokens

## Components
### API Server
- Handles HTTP requests
- Implements business logic
- Manages database connections

### Database Layer
- User table for authentication
- Tasks table for task storage
- Indexes for performance

## Implementation Details
- Use bcrypt for password hashing
- Implement rate limiting
- Add request validation middleware
"""
        
        # Save the SPEC
        spec_ai_content = AIGeneratedContent(
            document_type="spec",
            content=spec_content,
            filename="TASK_MANAGEMENT_SPEC.md"
        )
        
        spec_result = await service.save_ai_generated_content(spec_ai_content)
        
        # Verify both documents exist
        assert prd_path.exists()
        assert spec_result.file_path.exists()
        assert "PostgreSQL" in spec_result.content
        assert "RESTful API" in spec_result.content
    
    @pytest.mark.asyncio
    async def test_design_workflow_complete_chain(self, temp_workspace):
        """Test complete workflow: PRD → SPEC → DESIGN."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Create PRD
        prd_content = "# PRD\nUser interface for task management"
        prd_path = temp_workspace / "PRD.md"
        prd_path.write_text(prd_content)
        
        # Create SPEC
        spec_content = "# SPEC\nReact components and API endpoints"
        spec_path = temp_workspace / "SPEC.md"
        spec_path.write_text(spec_content)
        
        # Generate DESIGN prompt
        design_prompt = await service.generate_design_prompt(
            specification_input="Create design document for task management UI",
            existing_spec_path=str(spec_path),
            template_config="default_design"
        )
        
        assert isinstance(design_prompt, PromptResult)
        assert design_prompt.document_type == "design"
        assert "design document" in design_prompt.prompt.lower()
        
        # Simulate and save DESIGN
        design_content = """# Design Document

## System Design
Component-based architecture using React with Material-UI components.

## User Interface Design
- Clean, minimalist interface
- Task cards with drag-and-drop
- Responsive grid layout

## Data Flow
User actions → React components → API calls → Database updates → UI refresh

## Implementation Plan
1. Set up React project structure
2. Create reusable UI components
3. Implement state management
4. Add API integration
"""
        
        design_ai_content = AIGeneratedContent(
            document_type="design",
            content=design_content,
            filename="TASK_MANAGEMENT_DESIGN.md"
        )
        
        design_result = await service.save_ai_generated_content(design_ai_content)
        
        # Verify all three documents exist
        assert prd_path.exists()
        assert spec_path.exists()
        assert design_result.file_path.exists()
        
        # Verify design content
        assert "React" in design_result.content
        assert "User Interface Design" in design_result.content
    
    @pytest.mark.asyncio
    async def test_workflow_with_validation_errors(self, temp_workspace):
        """Test workflow when AI content has validation issues."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Create AI content with validation issues
        poor_content = """# PRD

## Introduction
TODO: Add introduction later

## Objectives
[PLACEHOLDER - define objectives]

## Random Section
This doesn't follow the template structure.
"""
        
        ai_content = AIGeneratedContent(
            document_type="prd",
            content=poor_content,
            filename="POOR_QUALITY_PRD.md",
            validation_requested=True
        )
        
        result = await service.save_ai_generated_content(ai_content)
        
        # Should still save but with warnings
        assert result.file_path.exists()
        assert len(result.warnings) > 0
        assert result.metadata["is_valid"] is False
        
        # Warnings should mention specific issues
        warning_text = " ".join(result.warnings)
        assert "placeholder" in warning_text.lower() or "todo" in warning_text.lower()
    
    @pytest.mark.asyncio 
    async def test_error_handling_in_workflow(self, temp_workspace):
        """Test error handling throughout the workflow."""
        service = DocumentGeneratorService(output_directory=temp_workspace)
        
        # Test with invalid template config
        with pytest.raises(Exception):
            await service.generate_prd_prompt(
                user_input="Test input",
                template_config="nonexistent_template"
            )
        
        # Test saving with invalid document type
        invalid_content = AIGeneratedContent(
            document_type="invalid_type",
            content="Test content",
            filename="test.md"
        )
        
        # Should handle gracefully
        result = await service.save_ai_generated_content(invalid_content)
        assert result.file_path.exists()  # Should still save
        assert result.metadata["document_type"] == "invalid_type"
