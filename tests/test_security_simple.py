#!/usr/bin/env python3
"""
Simple security test to verify our security implementation works.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_input_validation():
    """Test input validation security."""
    print("Testing input validation...")
    
    try:
        from document_generator_mcp.security.validators import validate_user_input
        
        # Test normal input
        normal_input = "Create a task management system"
        result = validate_user_input(normal_input)
        assert result == normal_input
        print("✓ Normal input validation passed")
        
        # Test dangerous input
        try:
            dangerous_input = "<script>alert('xss')</script>"
            validate_user_input(dangerous_input)
            print("✗ Dangerous input validation failed - should have been blocked")
            return False
        except Exception:
            print("✓ Dangerous input correctly blocked")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_path_security():
    """Test path security measures."""
    print("Testing path security...")
    
    try:
        from document_generator_mcp.security.path_security import is_safe_path
        
        # Test safe path
        safe_path = "documents/test.md"
        assert is_safe_path(safe_path) == True
        print("✓ Safe path validation passed")
        
        # Test dangerous path
        dangerous_path = "../../../etc/passwd"
        assert is_safe_path(dangerous_path) == False
        print("✓ Dangerous path correctly blocked")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_content_security():
    """Test content security measures."""
    print("Testing content security...")
    
    try:
        from document_generator_mcp.security.content_security import sanitize_user_content
        
        # Test normal content
        normal_content = "This is normal content"
        result = sanitize_user_content(normal_content)
        assert "normal content" in result
        print("✓ Normal content sanitization passed")
        
        # Test dangerous content
        dangerous_content = "<script>alert('xss')</script>Normal content"
        result = sanitize_user_content(dangerous_content)
        assert "<script>" not in result
        assert "Normal content" in result
        print("✓ Dangerous content correctly sanitized")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_template_security():
    """Test template security measures."""
    print("Testing template security...")
    
    try:
        from document_generator_mcp.security.content_security import sanitize_template_content
        from document_generator_mcp.exceptions import TemplateValidationError
        
        # Test safe template
        safe_template = "# {title}\n\nContent: {content}"
        result = sanitize_template_content(safe_template)
        assert "{title}" in result
        print("✓ Safe template validation passed")
        
        # Test dangerous template
        try:
            dangerous_template = "{{__import__('os').system('rm -rf /')}}"
            sanitize_template_content(dangerous_template)
            print("✗ Dangerous template validation failed - should have been blocked")
            return False
        except TemplateValidationError:
            print("✓ Dangerous template correctly blocked")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_security_config():
    """Test security configuration."""
    print("Testing security configuration...")
    
    try:
        from document_generator_mcp.security.config_security import get_secure_defaults
        
        config = get_secure_defaults()
        
        # Check that security features are enabled
        assert config.enable_content_sanitization == True
        assert config.enable_template_validation == True
        assert config.restrict_to_base_directory == True
        assert config.allow_absolute_paths == False
        assert config.expose_detailed_errors == False
        
        print("✓ Security configuration validation passed")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def main():
    """Run all security tests."""
    print("=" * 50)
    print("Document Generator MCP Security Tests")
    print("=" * 50)
    
    tests = [
        test_input_validation,
        test_path_security,
        test_content_security,
        test_template_security,
        test_security_config,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        if test():
            passed += 1
        else:
            print("Test failed!")
    
    print()
    print("=" * 50)
    print(f"Security Test Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 All security tests passed!")
        return 0
    else:
        print("⚠️  Some security tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
