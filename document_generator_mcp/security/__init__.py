"""
Security utilities for the MCP Document Generator.

This module provides security functions for input validation, path security,
content sanitization, and secure configuration management.
"""

from .validators import (
    validate_user_input,
    validate_file_path,
    validate_template_config,
    validate_reference_folder,
    sanitize_content,
    validate_dict_input,
)

from .path_security import (
    secure_path_join,
    is_safe_path,
    normalize_path,
    validate_file_access,
)

from .content_security import (
    sanitize_template_content,
    validate_template_structure,
    prevent_template_injection,
    sanitize_user_content,
)

from .config_security import (
    get_secure_defaults,
    validate_security_config,
    SecurityConfig,
)

from .logging_security import (
    get_security_logger,
    log_security_event,
    sanitize_log_data,
    log_file_access,
    log_input_validation,
)

__all__ = [
    "validate_user_input",
    "validate_file_path",
    "validate_template_config",
    "validate_reference_folder",
    "sanitize_content",
    "validate_dict_input",
    "secure_path_join",
    "is_safe_path",
    "normalize_path",
    "validate_file_access",
    "sanitize_template_content",
    "validate_template_structure",
    "prevent_template_injection",
    "sanitize_user_content",
    "get_secure_defaults",
    "validate_security_config",
    "SecurityConfig",
    "get_security_logger",
    "log_security_event",
    "sanitize_log_data",
    "log_file_access",
    "log_input_validation",
]
