"""
Content security utilities for preventing injection attacks and ensuring safe content processing.

This module provides functions to sanitize content, validate templates,
and prevent various injection attacks.
"""

import re
import html
from typing import Any, Dict, List, Optional, Set
import logging

from ..exceptions import ValidationError, TemplateValidationError


logger = logging.getLogger(__name__)

# Template injection patterns to detect and prevent
TEMPLATE_INJECTION_PATTERNS = [
    r'\{\{.*?__.*?\}\}',           # Django/Jinja2 dangerous attributes
    r'\{\{.*?import.*?\}\}',       # Import statements in templates
    r'\{\{.*?exec.*?\}\}',         # Exec calls in templates
    r'\{\{.*?eval.*?\}\}',         # Eval calls in templates
    r'\{\{.*?subprocess.*?\}\}',   # Subprocess calls
    r'\{\{.*?os\..*?\}\}',         # OS module access
    r'\{\{.*?file.*?\}\}',         # File operations
    r'\{\{.*?open.*?\}\}',         # File open operations
    r'\{%.*?import.*?%\}',         # Template import statements
    r'\{%.*?load.*?%\}',           # Template load statements
]

# Safe template placeholder pattern
SAFE_PLACEHOLDER_PATTERN = r'^\{[a-zA-Z_][a-zA-Z0-9_]*\}$'

# Content patterns that might indicate injection attempts
CONTENT_INJECTION_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script tags
    r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
    r'<object[^>]*>.*?</object>',  # Object tags
    r'<embed[^>]*>.*?</embed>',    # Embed tags
    r'javascript:',                # JavaScript URLs
    r'vbscript:',                 # VBScript URLs
    r'data:text/html',            # Data URLs with HTML
    r'on\w+\s*=',                 # Event handlers
]


def sanitize_user_content(content: str, 
                         preserve_formatting: bool = True,
                         max_length: int = 100000) -> str:
    """
    Sanitize user-provided content for safe processing.
    
    Args:
        content: Content to sanitize
        preserve_formatting: Whether to preserve basic formatting
        max_length: Maximum allowed content length
        
    Returns:
        Sanitized content
        
    Raises:
        ValidationError: If content is too long or contains dangerous patterns
    """
    if not isinstance(content, str):
        content = str(content)
    
    if len(content) > max_length:
        raise ValidationError(
            "content",
            [f"Content too long: {len(content)} characters (max: {max_length})"]
        )
    
    # Remove null bytes and most control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
    
    # Check for and remove dangerous content patterns
    for pattern in CONTENT_INJECTION_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE | re.DOTALL):
            logger.warning(f"Dangerous content pattern detected: {pattern}")
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # HTML escape if not preserving formatting
    if not preserve_formatting:
        sanitized = html.escape(sanitized)
    else:
        # Only escape the most dangerous HTML entities
        sanitized = sanitized.replace('<script', '&lt;script')
        sanitized = sanitized.replace('</script>', '&lt;/script&gt;')
        sanitized = sanitized.replace('<iframe', '&lt;iframe')
        sanitized = sanitized.replace('javascript:', 'javascript-blocked:')
    
    return sanitized.strip()


def sanitize_template_content(template_content: str) -> str:
    """
    Sanitize template content to prevent template injection attacks.
    
    Args:
        template_content: Template content to sanitize
        
    Returns:
        Sanitized template content
        
    Raises:
        TemplateValidationError: If template contains dangerous patterns
    """
    if not isinstance(template_content, str):
        template_content = str(template_content)
    
    # Check for template injection patterns
    dangerous_patterns = []
    for pattern in TEMPLATE_INJECTION_PATTERNS:
        matches = re.findall(pattern, template_content, re.IGNORECASE | re.DOTALL)
        if matches:
            dangerous_patterns.extend(matches)
    
    if dangerous_patterns:
        logger.warning(f"Template injection patterns detected: {dangerous_patterns}")
        raise TemplateValidationError(
            "template_content",
            [f"Template contains dangerous patterns: {', '.join(dangerous_patterns[:5])}"]
        )
    
    # Validate placeholders are in safe format
    placeholder_pattern = r'\{[^}]+\}'
    placeholders = re.findall(placeholder_pattern, template_content)
    
    for placeholder in placeholders:
        if not re.match(SAFE_PLACEHOLDER_PATTERN, placeholder):
            logger.warning(f"Unsafe placeholder detected: {placeholder}")
            raise TemplateValidationError(
                "template_content",
                [f"Unsafe placeholder format: {placeholder}. Use only alphanumeric and underscore."]
            )
    
    # Remove any remaining dangerous content
    sanitized = sanitize_user_content(template_content, preserve_formatting=True)
    
    return sanitized


def validate_template_structure(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate template structure for security.
    
    Args:
        template_data: Template data to validate
        
    Returns:
        Validated template data
        
    Raises:
        TemplateValidationError: If template structure is invalid or dangerous
    """
    if not isinstance(template_data, dict):
        raise TemplateValidationError(
            "template_structure",
            ["Template data must be a dictionary"]
        )
    
    # Required fields
    required_fields = {'name', 'template_type', 'sections'}
    missing_fields = required_fields - set(template_data.keys())
    if missing_fields:
        raise TemplateValidationError(
            "template_structure",
            [f"Missing required fields: {', '.join(missing_fields)}"]
        )
    
    # Validate template name
    name = template_data.get('name', '')
    if not isinstance(name, str) or not re.match(r'^[a-zA-Z0-9_.-]+$', name):
        raise TemplateValidationError(
            "template_name",
            ["Template name must contain only alphanumeric characters, underscore, hyphen, and dot"]
        )
    
    # Validate template type
    template_type = template_data.get('template_type', '')
    allowed_types = {'prd', 'spec', 'design'}
    if template_type not in allowed_types:
        raise TemplateValidationError(
            "template_type",
            [f"Invalid template type: {template_type}. Allowed: {', '.join(allowed_types)}"]
        )
    
    # Validate sections
    sections = template_data.get('sections', {})
    if not isinstance(sections, dict):
        raise TemplateValidationError(
            "template_sections",
            ["Template sections must be a dictionary"]
        )
    
    validated_sections = {}
    for section_name, section_content in sections.items():
        if not isinstance(section_name, str):
            raise TemplateValidationError(
                "section_name",
                ["Section names must be strings"]
            )
        
        if not re.match(r'^[a-zA-Z0-9_]+$', section_name):
            raise TemplateValidationError(
                "section_name",
                [f"Invalid section name: {section_name}. Use only alphanumeric and underscore."]
            )
        
        # Sanitize section content
        validated_sections[section_name] = sanitize_template_content(str(section_content))
    
    # Create validated template data
    validated_data = {
        'name': name,
        'template_type': template_type,
        'sections': validated_sections,
        'version': str(template_data.get('version', '1.0')),
        'metadata': validate_template_metadata(template_data.get('metadata', {}))
    }
    
    return validated_data


def validate_template_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate template metadata for security.
    
    Args:
        metadata: Metadata to validate
        
    Returns:
        Validated metadata
    """
    if not isinstance(metadata, dict):
        return {}
    
    validated_metadata = {}
    allowed_keys = {
        'description', 'author', 'supports_customization', 
        'requires_prd', 'requires_spec', 'created_date'
    }
    
    for key, value in metadata.items():
        if not isinstance(key, str):
            continue
        
        # Only allow safe metadata keys
        if key not in allowed_keys:
            logger.warning(f"Unexpected metadata key: {key}")
            continue
        
        # Sanitize metadata values
        if isinstance(value, str):
            validated_metadata[key] = sanitize_user_content(value, preserve_formatting=False)
        elif isinstance(value, bool):
            validated_metadata[key] = value
        else:
            validated_metadata[key] = str(value)
    
    return validated_metadata


def prevent_template_injection(template_string: str, 
                             context: Dict[str, Any]) -> str:
    """
    Safely render template string with context, preventing injection.
    
    Args:
        template_string: Template string to render
        context: Context variables for template
        
    Returns:
        Safely rendered template
        
    Raises:
        TemplateValidationError: If template or context is unsafe
    """
    # Sanitize template string
    safe_template = sanitize_template_content(template_string)
    
    # Validate and sanitize context
    safe_context = validate_template_context(context)
    
    # Simple and safe template replacement
    result = safe_template
    for key, value in safe_context.items():
        placeholder = f"{{{key}}}"
        if placeholder in result:
            # Ensure value is safe
            safe_value = sanitize_user_content(str(value), preserve_formatting=True)
            result = result.replace(placeholder, safe_value)
    
    return result


def validate_template_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate template context for security.
    
    Args:
        context: Template context to validate
        
    Returns:
        Validated context
        
    Raises:
        ValidationError: If context is invalid or dangerous
    """
    if not isinstance(context, dict):
        raise ValidationError(
            "template_context",
            ["Template context must be a dictionary"]
        )
    
    validated_context = {}
    
    for key, value in context.items():
        # Validate key
        if not isinstance(key, str):
            continue
        
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            logger.warning(f"Invalid context key: {key}")
            continue
        
        # Validate and sanitize value
        if isinstance(value, str):
            validated_context[key] = sanitize_user_content(value)
        elif isinstance(value, (int, float, bool)) or value is None:
            validated_context[key] = value
        elif isinstance(value, (list, tuple)):
            # Convert list/tuple to string representation
            validated_context[key] = sanitize_user_content(str(value))
        else:
            # Convert other types to string
            validated_context[key] = sanitize_user_content(str(value))
    
    return validated_context


def detect_content_anomalies(content: str) -> List[str]:
    """
    Detect potential security anomalies in content.
    
    Args:
        content: Content to analyze
        
    Returns:
        List of detected anomalies
    """
    anomalies = []
    
    # Check for excessive repetition (potential DoS)
    if len(content) > 1000:
        # Check for repeated patterns
        for pattern_length in [10, 50, 100]:
            if pattern_length * 10 < len(content):
                pattern = content[:pattern_length]
                if content.count(pattern) > len(content) // pattern_length // 2:
                    anomalies.append(f"Excessive repetition detected (pattern length: {pattern_length})")
                    break
    
    # Check for unusual character distributions
    if len(content) > 100:
        non_printable_count = sum(1 for c in content if ord(c) < 32 and c not in '\t\n\r')
        if non_printable_count > len(content) * 0.1:
            anomalies.append("High ratio of non-printable characters")
    
    # Check for potential encoding attacks
    if '\\x' in content or '\\u' in content:
        anomalies.append("Potential encoding-based attack detected")
    
    # Check for extremely long lines (potential buffer overflow attempts)
    lines = content.split('\n')
    max_line_length = max(len(line) for line in lines) if lines else 0
    if max_line_length > 10000:
        anomalies.append(f"Extremely long line detected: {max_line_length} characters")
    
    return anomalies
