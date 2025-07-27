"""
Input validation utilities for security.

This module provides functions to validate and sanitize user inputs
to prevent injection attacks and ensure data integrity.
"""

import re
import html
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

from ..exceptions import ValidationError


logger = logging.getLogger(__name__)

# Security constants
MAX_INPUT_LENGTH = 50000  # 50KB max input
MAX_PATH_LENGTH = 4096    # Max path length
MAX_TEMPLATE_NAME_LENGTH = 100
ALLOWED_TEMPLATE_TYPES = {'prd', 'spec', 'design'}
DANGEROUS_PATTERNS = [
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


def validate_user_input(user_input: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """
    Validate and sanitize user input.
    
    Args:
        user_input: The user input to validate
        max_length: Maximum allowed length
        
    Returns:
        Sanitized user input
        
    Raises:
        ValidationError: If input is invalid or dangerous
    """
    if not isinstance(user_input, str):
        raise ValidationError(
            "user_input",
            ["Input must be a string"]
        )
    
    if not user_input.strip():
        raise ValidationError(
            "user_input", 
            ["Input cannot be empty"]
        )
    
    if len(user_input) > max_length:
        raise ValidationError(
            "user_input",
            [f"Input too long: {len(user_input)} characters (max: {max_length})"]
        )
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            logger.warning(f"Dangerous pattern detected in user input: {pattern}")
            raise ValidationError(
                "user_input",
                ["Input contains potentially dangerous content"]
            )
    
    # Sanitize HTML entities
    sanitized = html.escape(user_input)
    
    # Remove null bytes and other control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    return sanitized.strip()


def validate_file_path(file_path: Union[str, Path], 
                      allowed_extensions: Optional[List[str]] = None,
                      base_directory: Optional[Path] = None) -> Path:
    """
    Validate file path for security.
    
    Args:
        file_path: Path to validate
        allowed_extensions: List of allowed file extensions
        base_directory: Base directory to restrict access to
        
    Returns:
        Validated and normalized Path object
        
    Raises:
        ValidationError: If path is invalid or dangerous
    """
    if not file_path:
        raise ValidationError(
            "file_path",
            ["File path cannot be empty"]
        )
    
    # Convert to Path object
    if isinstance(file_path, str):
        if len(file_path) > MAX_PATH_LENGTH:
            raise ValidationError(
                "file_path",
                [f"Path too long: {len(file_path)} characters (max: {MAX_PATH_LENGTH})"]
            )
        path = Path(file_path)
    else:
        path = file_path
    
    # Check for dangerous path components
    dangerous_components = ['..', '.', '~', '$']
    path_str = str(path)
    
    for component in dangerous_components:
        if component in path.parts:
            raise ValidationError(
                "file_path",
                [f"Path contains dangerous component: {component}"]
            )
    
    # Check for absolute paths that might escape sandbox
    if path.is_absolute() and base_directory:
        try:
            # Resolve both paths and check if file path is within base directory
            resolved_path = path.resolve()
            resolved_base = base_directory.resolve()
            
            if not str(resolved_path).startswith(str(resolved_base)):
                raise ValidationError(
                    "file_path",
                    ["Path is outside allowed directory"]
                )
        except (OSError, ValueError) as e:
            raise ValidationError(
                "file_path",
                [f"Invalid path: {str(e)}"]
            )
    
    # Validate file extension if specified
    if allowed_extensions:
        if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
            raise ValidationError(
                "file_path",
                [f"File extension not allowed: {path.suffix}. Allowed: {allowed_extensions}"]
            )
    
    # Check for null bytes and other dangerous characters
    if '\x00' in path_str or any(ord(c) < 32 for c in path_str if c not in '\t\n\r'):
        raise ValidationError(
            "file_path",
            ["Path contains invalid characters"]
        )
    
    return path


def validate_template_config(template_config: str) -> str:
    """
    Validate template configuration string.
    
    Args:
        template_config: Template configuration to validate
        
    Returns:
        Validated template configuration
        
    Raises:
        ValidationError: If configuration is invalid
    """
    if not isinstance(template_config, str):
        raise ValidationError(
            "template_config",
            ["Template configuration must be a string"]
        )
    
    if not template_config.strip():
        return "default"  # Use default if empty
    
    if len(template_config) > MAX_TEMPLATE_NAME_LENGTH:
        raise ValidationError(
            "template_config",
            [f"Template name too long: {len(template_config)} characters (max: {MAX_TEMPLATE_NAME_LENGTH})"]
        )
    
    # Allow alphanumeric, underscore, hyphen, and dot
    if not re.match(r'^[a-zA-Z0-9_.-]+$', template_config):
        raise ValidationError(
            "template_config",
            ["Template configuration contains invalid characters. Use only letters, numbers, underscore, hyphen, and dot."]
        )
    
    return template_config.strip()


def validate_reference_folder(folder_path: str, base_directory: Optional[Path] = None) -> Optional[Path]:
    """
    Validate reference folder path.
    
    Args:
        folder_path: Folder path to validate
        base_directory: Base directory to restrict access to
        
    Returns:
        Validated Path object or None if empty
        
    Raises:
        ValidationError: If path is invalid or dangerous
    """
    if not folder_path or not folder_path.strip():
        return None
    
    # Use file path validation
    validated_path = validate_file_path(folder_path, base_directory=base_directory)
    
    return validated_path


def sanitize_content(content: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """
    Sanitize content for safe processing.
    
    Args:
        content: Content to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized content
        
    Raises:
        ValidationError: If content is too long or dangerous
    """
    if not isinstance(content, str):
        return str(content)
    
    if len(content) > max_length:
        raise ValidationError(
            "content",
            [f"Content too long: {len(content)} characters (max: {max_length})"]
        )
    
    # Remove null bytes and control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
    
    # Check for dangerous patterns in content
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE):
            logger.warning(f"Dangerous pattern detected in content: {pattern}")
            # Remove the dangerous pattern instead of rejecting entirely
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def validate_dict_input(data: Dict[str, Any], 
                       allowed_keys: Optional[List[str]] = None,
                       max_depth: int = 10) -> Dict[str, Any]:
    """
    Validate dictionary input for security.
    
    Args:
        data: Dictionary to validate
        allowed_keys: List of allowed keys
        max_depth: Maximum nesting depth
        
    Returns:
        Validated dictionary
        
    Raises:
        ValidationError: If dictionary is invalid or dangerous
    """
    if not isinstance(data, dict):
        raise ValidationError(
            "dict_input",
            ["Input must be a dictionary"]
        )
    
    def validate_recursive(obj: Any, depth: int = 0) -> Any:
        if depth > max_depth:
            raise ValidationError(
                "dict_input",
                [f"Dictionary nesting too deep (max: {max_depth})"]
            )
        
        if isinstance(obj, dict):
            validated = {}
            for key, value in obj.items():
                # Validate key
                if not isinstance(key, str):
                    raise ValidationError(
                        "dict_input",
                        ["Dictionary keys must be strings"]
                    )
                
                if allowed_keys and key not in allowed_keys:
                    logger.warning(f"Unexpected key in dictionary: {key}")
                    continue  # Skip unexpected keys
                
                # Validate value recursively
                validated[key] = validate_recursive(value, depth + 1)
            
            return validated
        
        elif isinstance(obj, list):
            return [validate_recursive(item, depth + 1) for item in obj]
        
        elif isinstance(obj, str):
            return sanitize_content(obj)
        
        elif isinstance(obj, (int, float, bool)) or obj is None:
            return obj
        
        else:
            # Convert other types to string and sanitize
            return sanitize_content(str(obj))
    
    return validate_recursive(data)
