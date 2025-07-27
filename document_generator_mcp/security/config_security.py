"""
Security configuration utilities.

This module provides secure default configurations and validation
for security-related settings.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import logging

from ..exceptions import ConfigurationError


logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    
    # Input validation settings
    max_input_length: int = 50000
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_concurrent_files: int = 10
    max_template_name_length: int = 100
    
    # Path security settings
    allowed_base_directories: List[Path] = field(default_factory=list)
    allowed_file_extensions: Set[str] = field(default_factory=lambda: {
        '.md', '.txt', '.json', '.yaml', '.yml', '.pdf', '.png', '.jpg', '.jpeg'
    })
    restrict_to_base_directory: bool = True
    allow_absolute_paths: bool = False
    
    # Content security settings
    enable_content_sanitization: bool = True
    enable_template_validation: bool = True
    max_template_depth: int = 10
    preserve_formatting: bool = True
    
    # Resource limits
    max_processing_time: int = 300  # 5 minutes
    max_memory_usage: int = 512 * 1024 * 1024  # 512MB
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    
    # Logging security
    log_security_events: bool = True
    log_user_input: bool = False  # Don't log user input by default
    log_file_paths: bool = True
    sanitize_logs: bool = True
    
    # Error handling
    expose_detailed_errors: bool = False
    log_all_errors: bool = True
    
    def validate(self) -> List[str]:
        """
        Validate security configuration.
        
        Returns:
            List of validation issues
        """
        issues = []
        
        # Validate numeric limits
        if self.max_input_length <= 0:
            issues.append("max_input_length must be positive")
        
        if self.max_file_size <= 0:
            issues.append("max_file_size must be positive")
        
        if self.max_concurrent_files <= 0:
            issues.append("max_concurrent_files must be positive")
        
        if self.max_processing_time <= 0:
            issues.append("max_processing_time must be positive")
        
        # Validate file extensions
        for ext in self.allowed_file_extensions:
            if not ext.startswith('.'):
                issues.append(f"File extension must start with dot: {ext}")
        
        # Validate base directories
        for base_dir in self.allowed_base_directories:
            if not isinstance(base_dir, Path):
                issues.append(f"Base directory must be Path object: {base_dir}")
            elif not base_dir.exists():
                issues.append(f"Base directory does not exist: {base_dir}")
        
        # Security warnings
        if not self.enable_content_sanitization:
            issues.append("WARNING: Content sanitization is disabled")
        
        if not self.enable_template_validation:
            issues.append("WARNING: Template validation is disabled")
        
        if self.allow_absolute_paths and not self.allowed_base_directories:
            issues.append("WARNING: Absolute paths allowed without base directory restrictions")
        
        if self.expose_detailed_errors:
            issues.append("WARNING: Detailed error exposure enabled (potential information leak)")
        
        if self.log_user_input:
            issues.append("WARNING: User input logging enabled (potential privacy issue)")
        
        return issues


def get_secure_defaults() -> SecurityConfig:
    """
    Get secure default configuration.
    
    Returns:
        SecurityConfig with secure defaults
    """
    return SecurityConfig(
        # Conservative input limits
        max_input_length=50000,
        max_file_size=50 * 1024 * 1024,  # 50MB (reduced from 100MB)
        max_concurrent_files=5,  # Reduced from 10
        
        # Strict path security
        restrict_to_base_directory=True,
        allow_absolute_paths=False,
        
        # Enable all security features
        enable_content_sanitization=True,
        enable_template_validation=True,
        
        # Conservative resource limits
        max_processing_time=180,  # 3 minutes (reduced from 5)
        max_memory_usage=256 * 1024 * 1024,  # 256MB (reduced from 512MB)
        enable_rate_limiting=True,
        max_requests_per_minute=30,  # Reduced from 60
        
        # Secure logging
        log_security_events=True,
        log_user_input=False,
        sanitize_logs=True,
        
        # Secure error handling
        expose_detailed_errors=False,
        log_all_errors=True,
    )


def get_development_config() -> SecurityConfig:
    """
    Get development configuration (less restrictive for development).
    
    Returns:
        SecurityConfig for development use
    """
    config = get_secure_defaults()
    
    # Relax some restrictions for development
    config.max_input_length = 100000
    config.max_file_size = 100 * 1024 * 1024
    config.max_concurrent_files = 10
    config.max_processing_time = 300
    config.max_requests_per_minute = 120
    config.expose_detailed_errors = True  # For debugging
    
    return config


def validate_security_config(config: Dict[str, Any]) -> SecurityConfig:
    """
    Validate and create SecurityConfig from dictionary.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Validated SecurityConfig
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    try:
        # Start with secure defaults
        security_config = get_secure_defaults()
        
        # Override with provided values
        for key, value in config.items():
            if hasattr(security_config, key):
                # Validate specific fields
                if key == 'allowed_file_extensions' and isinstance(value, list):
                    security_config.allowed_file_extensions = set(value)
                elif key == 'allowed_base_directories' and isinstance(value, list):
                    security_config.allowed_base_directories = [Path(p) for p in value]
                else:
                    setattr(security_config, key, value)
            else:
                logger.warning(f"Unknown security configuration key: {key}")
        
        # Validate the configuration
        issues = security_config.validate()
        if issues:
            error_issues = [issue for issue in issues if not issue.startswith("WARNING:")]
            if error_issues:
                raise ConfigurationError(
                    "security_config",
                    f"Security configuration validation failed: {'; '.join(error_issues)}"
                )
            
            # Log warnings
            for warning in [issue for issue in issues if issue.startswith("WARNING:")]:
                logger.warning(warning)
        
        return security_config
        
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        raise ConfigurationError(
            "security_config",
            f"Failed to validate security configuration: {str(e)}"
        )


def create_secure_environment_config() -> Dict[str, Any]:
    """
    Create secure environment configuration.
    
    Returns:
        Dictionary with secure environment settings
    """
    return {
        # File system security
        'umask': 0o077,  # Restrictive file permissions
        'temp_dir_permissions': 0o700,  # Owner only
        
        # Process security
        'max_open_files': 1024,
        'max_processes': 10,
        'nice_level': 10,  # Lower priority
        
        # Network security (for SSE transport)
        'bind_address': '127.0.0.1',  # Localhost only by default
        'enable_ssl': False,  # Require explicit SSL configuration
        'ssl_verify': True,
        
        # Memory security
        'disable_core_dumps': True,
        'secure_heap': True,
        
        # Logging security
        'log_rotation': True,
        'max_log_size': 10 * 1024 * 1024,  # 10MB
        'max_log_files': 5,
    }


def apply_security_hardening() -> None:
    """
    Apply security hardening measures to the current process.
    """
    import os
    import resource
    
    try:
        # Set restrictive umask
        os.umask(0o077)
        
        # Limit resource usage
        try:
            # Limit memory usage (if supported)
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, -1))
            
            # Limit CPU time
            resource.setrlimit(resource.RLIMIT_CPU, (300, -1))  # 5 minutes
            
            # Limit number of open files
            resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))
            
        except (ValueError, OSError) as e:
            logger.warning(f"Could not set resource limits: {e}")
        
        # Disable core dumps for security
        try:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except (ValueError, OSError) as e:
            logger.warning(f"Could not disable core dumps: {e}")
        
        logger.info("Security hardening applied")
        
    except Exception as e:
        logger.warning(f"Failed to apply security hardening: {e}")


def get_security_headers() -> Dict[str, str]:
    """
    Get security headers for HTTP transport.
    
    Returns:
        Dictionary of security headers
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'none'; object-src 'none';",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }
