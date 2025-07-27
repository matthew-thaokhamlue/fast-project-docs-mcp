"""
Pytest configuration and shared fixtures for the Document Generator MCP tests.

This file provides common fixtures and configuration for testing the hybrid
prompt-based workflow and AI content handling functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from document_generator_mcp.models.core import (
    ResourceAnalysis, PromptResult, AIGeneratedContent, 
    ContentValidationResult, ProcessingContext
)
from document_generator_mcp.models.document_structures import PRDStructure, SPECStructure, DESIGNStructure
from document_generator_mcp.services.document_generator import DocumentGeneratorService
from document_generator_mcp.templates.manager import TemplateManager


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_workspace_with_resources():
    """Create a temporary workspace with sample reference resources."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create reference resources folder
    ref_dir = temp_dir / "reference_resources"
    ref_dir.mkdir()
    
    # Create sample documentation
    (ref_dir / "api_docs.md").write_text("""
# API Documentation

## Authentication
- JWT tokens required
- Refresh token mechanism
- Role-based access control

## Endpoints
- GET /api/users - List users
- POST /api/users - Create user
- PUT /api/users/{id} - Update user
- DELETE /api/users/{id} - Delete user
    """)
    
    # Create sample configuration
    (ref_dir / "database_config.json").write_text("""
{
    "database": {
        "type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "name": "app_db"
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0
    },
    "security": {
        "jwt_secret": "your-secret-key",
        "token_expiry": "24h"
    }
}
    """)
    
    # Create sample requirements
    (ref_dir / "requirements.txt").write_text("""
# Core requirements
fastapi==0.68.0
uvicorn==0.15.0
sqlalchemy==1.4.23
alembic==1.7.1
redis==3.5.3
jwt==1.2.0
bcrypt==3.2.0
    """)
    
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_resource_analysis():
    """Create a sample ResourceAnalysis for testing."""
    return ResourceAnalysis(
        total_files=3,
        categorized_files={
            "documentation": [
                MagicMock(file_path=Path("api_docs.md"), extracted_text="API documentation content")
            ],
            "configuration": [
                MagicMock(file_path=Path("database_config.json"), extracted_text="Database config")
            ],
            "code": [
                MagicMock(file_path=Path("requirements.txt"), extracted_text="Python requirements")
            ]
        },
        content_summary="Project includes API documentation, database configuration, and Python requirements",
        processing_errors=[],
        supported_formats=[".md", ".json", ".txt", ".py"]
    )


@pytest.fixture
def sample_prd_structure():
    """Create a sample PRDStructure for testing."""
    prd = PRDStructure()
    prd.introduction = "This is a test PRD for user authentication system"
    prd.objectives = [
        "Implement secure user authentication",
        "Provide seamless user experience",
        "Ensure scalable architecture"
    ]
    prd.add_user_story(
        role="user",
        feature="login with email and password",
        benefit="access the application securely",
        criteria=["Valid email format required", "Password minimum 8 characters"]
    )
    prd.add_user_story(
        role="admin",
        feature="manage user accounts",
        benefit="control system access",
        criteria=["Can view all users", "Can disable/enable accounts"]
    )
    prd.success_metrics = [
        "Login success rate > 95%",
        "Average login time < 2 seconds",
        "Zero security breaches"
    ]
    prd.constraints = [
        "Must comply with GDPR",
        "Support modern browsers only",
        "Mobile-responsive design required"
    ]
    return prd


@pytest.fixture
def sample_spec_structure():
    """Create a sample SPECStructure for testing."""
    spec = SPECStructure()
    spec.overview = "Technical specification for RESTful API with JWT authentication"
    spec.architecture = "Microservices architecture with API Gateway pattern"
    spec.add_component(
        name="Authentication Service",
        description="Handles user authentication and JWT token management",
        responsibilities=["User login/logout", "Token generation", "Token validation"],
        dependencies=["Database", "Redis Cache"]
    )
    spec.add_component(
        name="User Management Service", 
        description="Manages user CRUD operations",
        responsibilities=["User registration", "Profile management", "Role assignment"],
        dependencies=["Database", "Authentication Service"]
    )
    spec.add_interface(
        name="Authentication API",
        interface_type="REST",
        description="RESTful API for authentication operations",
        methods=[
            {"method": "POST", "endpoint": "/auth/login", "description": "User login"},
            {"method": "POST", "endpoint": "/auth/logout", "description": "User logout"},
            {"method": "POST", "endpoint": "/auth/refresh", "description": "Refresh token"}
        ]
    )
    spec.testing_strategy = "Unit tests, integration tests, and end-to-end API testing"
    return spec


@pytest.fixture
def sample_design_structure():
    """Create a sample DESIGNStructure for testing."""
    design = DESIGNStructure()
    design.system_design = "Component-based React frontend with Node.js backend"
    design.user_interface_design = "Material Design principles with responsive layout"
    design.data_flow = "User actions → React components → API calls → Database → Response"
    design.implementation_approach = "Agile development with CI/CD pipeline"
    design.add_design_pattern(
        pattern_name="MVC",
        description="Model-View-Controller pattern for separation of concerns",
        use_case="Frontend component organization",
        implementation_notes="React components as Views, Redux as Model"
    )
    design.ui_components = [
        {"name": "LoginForm", "description": "User login interface"},
        {"name": "UserDashboard", "description": "Main user interface after login"}
    ]
    design.workflows = [
        {"name": "User Registration", "description": "New user signup process"},
        {"name": "Password Reset", "description": "Forgot password workflow"}
    ]
    design.security_considerations = [
        "Input validation on all forms",
        "HTTPS only communication",
        "XSS protection headers"
    ]
    design.performance_requirements = [
        "Page load time < 3 seconds",
        "API response time < 500ms",
        "Support 1000 concurrent users"
    ]
    return design


@pytest.fixture
def sample_prompt_result():
    """Create a sample PromptResult for testing."""
    return PromptResult(
        document_type="prd",
        prompt="""Create a comprehensive Product Requirements Document (PRD) following Kiro's standards.

**User Input:** As a user, I want to login with email and password so that I can access my account

**Project Context:** Web application with secure authentication

Please generate a complete PRD with the following sections:
1. Introduction - Clear overview of the authentication feature
2. Objectives - Specific, measurable goals for user authentication
3. User Stories - Well-formatted stories with acceptance criteria
4. Success Metrics - Quantifiable measures of success
5. Constraints and Dependencies - Technical and business limitations

Generate comprehensive, actionable content for each section.""",
        template_structure={
            "introduction": "# Introduction\n{content}",
            "objectives": "## Objectives\n{content}",
            "user_stories": "## User Stories\n{content}",
            "success_metrics": "## Success Metrics\n{content}"
        },
        extracted_data={
            "user_stories": [
                {"role": "user", "feature": "login", "benefit": "access account"}
            ],
            "objectives": ["Secure authentication", "User experience"]
        },
        context_summary="Document Type: PRD | Project Context: Web application | Template: default_prd",
        references_used=["api_docs.md", "security_requirements.md"],
        suggested_filename="PRD.md",
        metadata={
            "template_used": "default_prd",
            "has_reference_resources": True,
            "user_stories_count": 1,
            "objectives_count": 2
        }
    )


@pytest.fixture
def sample_ai_generated_content():
    """Create sample AI-generated content for testing."""
    return AIGeneratedContent(
        document_type="prd",
        content="""# Product Requirements Document

## Introduction
This PRD outlines the requirements for implementing secure user authentication in our web application.

## Objectives
- Implement secure email/password authentication
- Provide seamless user login experience
- Ensure data security and privacy compliance

## User Stories
### Story 1: User Login
**As a** registered user  
**I want** to login with my email and password  
**So that** I can access my account securely

**Acceptance Criteria:**
- User can enter email and password
- System validates credentials against database
- Successful login redirects to dashboard
- Failed login shows appropriate error message

## Success Metrics
- Login success rate > 95%
- Average login time < 2 seconds
- Zero security breaches in first 6 months

## Constraints and Dependencies
- Must comply with GDPR regulations
- Requires secure password hashing (bcrypt)
- Database for user credential storage
- HTTPS encryption for all authentication requests""",
        filename="SAMPLE_PRD.md",
        user_notes="Generated for testing purposes",
        validation_requested=True,
        metadata={
            "generation_source": "test_fixture",
            "complexity": "medium"
        }
    )


@pytest.fixture
def sample_validation_result():
    """Create a sample ContentValidationResult for testing."""
    return ContentValidationResult(
        is_valid=True,
        document_type="prd",
        sections_found=["Introduction", "Objectives", "User Stories", "Success Metrics"],
        missing_sections=[],
        quality_issues=[],
        suggestions=[]
    )


@pytest.fixture
def document_generator_service(temp_workspace):
    """Create a DocumentGeneratorService instance for testing."""
    return DocumentGeneratorService(output_directory=temp_workspace)


@pytest.fixture
def template_manager():
    """Create a TemplateManager instance for testing."""
    return TemplateManager()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "hybrid: marks tests for hybrid workflow"
    )
    config.addinivalue_line(
        "markers", "prompt: marks tests for prompt generation"
    )
    config.addinivalue_line(
        "markers", "ai_content: marks tests for AI content handling"
    )
