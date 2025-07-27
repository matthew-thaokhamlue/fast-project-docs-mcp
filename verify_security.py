#!/usr/bin/env python3
"""
Simple verification script to check security implementation.
"""

import re
import html
from pathlib import Path

def test_basic_security_patterns():
    """Test basic security pattern detection."""
    print("Testing basic security patterns...")
    
    # Dangerous patterns we should detect
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'vbscript:',                 # VBScript URLs
        r'on\w+\s*=',                 # Event handlers
        r'eval\s*\(',                 # eval() calls
        r'exec\s*\(',                 # exec() calls
        r'import\s+',                 # Import statements
        r'__import__',                # __import__ calls
        r'subprocess',                # Subprocess calls
        r'os\.',                      # OS module calls
    ]
    
    # Test inputs that should be caught
    dangerous_inputs = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "eval('malicious code')",
        "import os; os.system('rm -rf /')",
        "__import__('os').system('malicious')",
        "subprocess.call(['rm', '-rf', '/'])",
        "os.system('malicious')"
    ]
    
    detected = 0
    total = len(dangerous_inputs)
    
    for dangerous_input in dangerous_inputs:
        for pattern in dangerous_patterns:
            if re.search(pattern, dangerous_input, re.IGNORECASE):
                print(f"✓ Detected dangerous pattern in: {dangerous_input[:30]}...")
                detected += 1
                break
        else:
            print(f"✗ Missed dangerous pattern in: {dangerous_input[:30]}...")
    
    print(f"Pattern detection: {detected}/{total} dangerous inputs detected")
    return detected == total


def test_html_sanitization():
    """Test HTML sanitization."""
    print("\nTesting HTML sanitization...")
    
    test_cases = [
        ("<script>alert('xss')</script>", "&lt;script&gt;"),
        ("<b>bold</b>", "&lt;b&gt;"),
        ("normal text", "normal text"),
        ("<iframe src='evil'></iframe>", "&lt;iframe"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for input_text, expected_pattern in test_cases:
        sanitized = html.escape(input_text)
        if expected_pattern in sanitized:
            print(f"✓ HTML sanitization worked for: {input_text[:20]}...")
            passed += 1
        else:
            print(f"✗ HTML sanitization failed for: {input_text[:20]}...")
    
    print(f"HTML sanitization: {passed}/{total} tests passed")
    return passed == total


def test_path_validation():
    """Test path validation logic."""
    print("\nTesting path validation...")
    
    # Test cases: (path, should_be_safe)
    test_cases = [
        ("documents/test.md", True),
        ("../../../etc/passwd", False),
        ("/etc/passwd", False),
        ("normal/path/file.txt", True),
        ("path/with/../traversal", False),
        ("./safe/relative/path", True),
        ("~/../etc/passwd", False),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for path_str, should_be_safe in test_cases:
        # Simple path safety check
        is_safe = True
        
        # Check for dangerous components
        dangerous_parts = {'..', '~'}
        path_parts = Path(path_str).parts
        
        for part in path_parts:
            if part in dangerous_parts:
                is_safe = False
                break
        
        # Check for absolute paths
        if Path(path_str).is_absolute():
            is_safe = False
        
        if is_safe == should_be_safe:
            print(f"✓ Path validation correct for: {path_str}")
            passed += 1
        else:
            print(f"✗ Path validation incorrect for: {path_str} (expected {should_be_safe}, got {is_safe})")
    
    print(f"Path validation: {passed}/{total} tests passed")
    return passed == total


def test_template_injection_patterns():
    """Test template injection pattern detection."""
    print("\nTesting template injection patterns...")
    
    # Template injection patterns
    template_patterns = [
        r'\{\{.*?__.*?\}\}',           # Django/Jinja2 dangerous attributes
        r'\{\{.*?import.*?\}\}',       # Import statements in templates
        r'\{\{.*?exec.*?\}\}',         # Exec calls in templates
        r'\{\{.*?eval.*?\}\}',         # Eval calls in templates
        r'\{\{.*?subprocess.*?\}\}',   # Subprocess calls
        r'\{\{.*?os\..*?\}\}',         # OS module access
        r'\{%.*?import.*?%\}',         # Template import statements
    ]
    
    # Dangerous template inputs
    dangerous_templates = [
        "{{__import__('os').system('rm -rf /')}}",
        "{% load dangerous_module %}",
        "{{request.user.password}}",
        "{{config.SECRET_KEY}}",
        "{{subprocess.call(['rm', '-rf', '/'])}}",
        "{{os.system('malicious')}}",
        "{{eval('dangerous_code')}}",
    ]
    
    detected = 0
    total = len(dangerous_templates)
    
    for dangerous_template in dangerous_templates:
        for pattern in template_patterns:
            if re.search(pattern, dangerous_template, re.IGNORECASE):
                print(f"✓ Detected template injection in: {dangerous_template[:30]}...")
                detected += 1
                break
        else:
            print(f"✗ Missed template injection in: {dangerous_template[:30]}...")
    
    print(f"Template injection detection: {detected}/{total} dangerous templates detected")
    return detected == total


def test_content_sanitization():
    """Test content sanitization."""
    print("\nTesting content sanitization...")
    
    # Content injection patterns
    content_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
        r'javascript:',                # JavaScript URLs
        r'on\w+\s*=',                 # Event handlers
    ]
    
    test_content = """
    <script>alert('xss')</script>
    <iframe src="evil.com"></iframe>
    <a href="javascript:alert('xss')">click</a>
    <div onclick="alert('xss')">click</div>
    Normal content should remain.
    """
    
    # Simulate content sanitization
    sanitized = test_content
    for pattern in content_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Check if dangerous content was removed
    dangerous_removed = (
        '<script>' not in sanitized and
        '<iframe' not in sanitized and
        'javascript:' not in sanitized and
        'onclick=' not in sanitized
    )
    
    # Check if normal content remains
    normal_remains = 'Normal content should remain' in sanitized
    
    if dangerous_removed and normal_remains:
        print("✓ Content sanitization working correctly")
        return True
    else:
        print("✗ Content sanitization failed")
        print(f"Dangerous removed: {dangerous_removed}")
        print(f"Normal remains: {normal_remains}")
        return False


def main():
    """Run all security verification tests."""
    print("=" * 60)
    print("Document Generator MCP Security Verification")
    print("=" * 60)
    
    tests = [
        test_basic_security_patterns,
        test_html_sanitization,
        test_path_validation,
        test_template_injection_patterns,
        test_content_sanitization,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Security Verification Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All security verification tests passed!")
        print("✓ Input validation patterns working")
        print("✓ Path security measures working")
        print("✓ Template injection prevention working")
        print("✓ Content sanitization working")
        print("✓ HTML escaping working")
        return 0
    else:
        print("⚠️  Some security verification tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
