"""
Security tests for the Document Generator MCP.

These tests verify that security measures are working correctly
and that the system is protected against common attacks.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from document_generator_mcp.security import (
    validate_user_input,
    validate_file_path,
    validate_template_config,
    sanitize_content,
    sanitize_template_content,
    validate_template_structure,
    is_safe_path,
    secure_path_join,
    get_secure_defaults,
)
from document_generator_mcp.exceptions import ValidationError, TemplateValidationError


class TestInputValidation:
    """Test input validation security measures."""
    
    def test_validate_user_input_normal(self):
        """Test normal user input validation."""
        normal_input = "Create a task management system with user authentication"
        result = validate_user_input(normal_input)
        assert result == normal_input
    
    def test_validate_user_input_empty(self):
        """Test empty input validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate_user_input("")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_validate_user_input_too_long(self):
        """Test input that's too long."""
        long_input = "x" * 60000  # Exceeds default max length
        with pytest.raises(ValidationError) as exc_info:
            validate_user_input(long_input)
        assert "too long" in str(exc_info.value)
    
    def test_validate_user_input_dangerous_patterns(self):
        """Test input with dangerous patterns."""
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "eval('malicious code')",
            "import os; os.system('rm -rf /')",
            "__import__('os').system('malicious')"
        ]
        
        for dangerous_input in dangerous_inputs:
            with pytest.raises(ValidationError) as exc_info:
                validate_user_input(dangerous_input)
            assert "dangerous content" in str(exc_info.value)
    
    def test_validate_user_input_html_escape(self):
        """Test HTML escaping in user input."""
        html_input = "This is <b>bold</b> text"
        result = validate_user_input(html_input)
        assert "&lt;b&gt;" in result
        assert "&lt;/b&gt;" in result


class TestPathSecurity:
    """Test path security measures."""
    
    def test_validate_file_path_normal(self):
        """Test normal file path validation."""
        normal_path = "documents/test.md"
        result = validate_file_path(normal_path)
        assert result == Path(normal_path)
    
    def test_validate_file_path_traversal_attack(self):
        """Test path traversal attack prevention."""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "~/../../etc/passwd"
        ]
        
        for dangerous_path in dangerous_paths:
            with pytest.raises(ValidationError) as exc_info:
                validate_file_path(dangerous_path)
            assert "dangerous component" in str(exc_info.value) or "outside allowed" in str(exc_info.value)
    
    def test_validate_file_path_with_base_directory(self):
        """Test file path validation with base directory restriction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            safe_file = base_dir / "safe.txt"
            safe_file.touch()
            
            # This should work
            result = validate_file_path(safe_file, base_directory=base_dir)
            assert result == safe_file
            
            # This should fail (outside base directory)
            outside_file = Path("/tmp/outside.txt")
            with pytest.raises(ValidationError):
                validate_file_path(outside_file, base_directory=base_dir)
    
    def test_is_safe_path(self):
        """Test safe path checking."""
        assert is_safe_path("documents/test.md")
        assert not is_safe_path("../../../etc/passwd")
        assert not is_safe_path("/etc/passwd", allow_absolute=False)
    
    def test_secure_path_join(self):
        """Test secure path joining."""
        base = Path("/safe/base")
        result = secure_path_join(base, "documents", "test.md")
        assert str(result).startswith(str(base))
        
        # This should fail
        with pytest.raises(ValidationError):
            secure_path_join(base, "../../../etc/passwd")


class TestContentSecurity:
    """Test content security measures."""
    
    def test_sanitize_content_normal(self):
        """Test normal content sanitization."""
        normal_content = "This is normal content with some text."
        result = sanitize_content(normal_content)
        assert result == normal_content
    
    def test_sanitize_content_dangerous_patterns(self):
        """Test content with dangerous patterns."""
        dangerous_content = "<script>alert('xss')</script>Some content"
        result = sanitize_content(dangerous_content)
        assert "<script>" not in result
        assert "Some content" in result
    
    def test_sanitize_template_content_normal(self):
        """Test normal template content sanitization."""
        normal_template = "# {title}\n\nThis is a template with {placeholder}."
        result = sanitize_template_content(normal_template)
        assert result == normal_template
    
    def test_sanitize_template_content_injection(self):
        """Test template injection prevention."""
        dangerous_templates = [
            "{{__import__('os').system('rm -rf /')}}",
            "{% load dangerous_module %}",
            "{{request.user.password}}",
            "{{config.SECRET_KEY}}"
        ]
        
        for dangerous_template in dangerous_templates:
            with pytest.raises(TemplateValidationError):
                sanitize_template_content(dangerous_template)
    
    def test_validate_template_structure(self):
        """Test template structure validation."""
        valid_template = {
            "name": "test_template",
            "template_type": "prd",
            "sections": {
                "introduction": "# {title}\n\nIntroduction content",
                "objectives": "## Objectives\n{objectives_list}"
            }
        }
        
        result = validate_template_structure(valid_template)
        assert result["name"] == "test_template"
        assert result["template_type"] == "prd"
        assert "introduction" in result["sections"]
    
    def test_validate_template_structure_invalid_type(self):
        """Test template structure validation with invalid type."""
        invalid_template = {
            "name": "test_template",
            "template_type": "invalid_type",
            "sections": {}
        }
        
        with pytest.raises(TemplateValidationError) as exc_info:
            validate_template_structure(invalid_template)
        assert "Invalid template type" in str(exc_info.value)


class TestTemplateConfig:
    """Test template configuration validation."""
    
    def test_validate_template_config_normal(self):
        """Test normal template config validation."""
        normal_configs = ["default", "custom_prd", "my-template", "template_v1.0"]
        
        for config in normal_configs:
            result = validate_template_config(config)
            assert result == config
    
    def test_validate_template_config_empty(self):
        """Test empty template config."""
        result = validate_template_config("")
        assert result == "default"
    
    def test_validate_template_config_invalid_chars(self):
        """Test template config with invalid characters."""
        invalid_configs = [
            "template with spaces",
            "template/with/slashes",
            "template<script>",
            "template;rm -rf /"
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises(ValidationError):
                validate_template_config(invalid_config)
    
    def test_validate_template_config_too_long(self):
        """Test template config that's too long."""
        long_config = "x" * 150  # Exceeds max length
        with pytest.raises(ValidationError) as exc_info:
            validate_template_config(long_config)
        assert "too long" in str(exc_info.value)


class TestSecurityConfiguration:
    """Test security configuration."""
    
    def test_get_secure_defaults(self):
        """Test secure default configuration."""
        config = get_secure_defaults()
        
        # Check that security features are enabled
        assert config.enable_content_sanitization is True
        assert config.enable_template_validation is True
        assert config.restrict_to_base_directory is True
        assert config.allow_absolute_paths is False
        assert config.expose_detailed_errors is False
        assert config.log_user_input is False
        
        # Check reasonable limits
        assert config.max_input_length > 0
        assert config.max_file_size > 0
        assert config.max_concurrent_files > 0
    
    def test_security_config_validation(self):
        """Test security configuration validation."""
        config = get_secure_defaults()
        issues = config.validate()
        
        # Should have no critical issues with secure defaults
        critical_issues = [issue for issue in issues if not issue.startswith("WARNING:")]
        assert len(critical_issues) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
