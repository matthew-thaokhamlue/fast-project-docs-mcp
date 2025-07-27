"""
Security-focused logging utilities.

This module provides secure logging functions that prevent information
leakage while maintaining useful audit trails.
"""

import logging
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .validators import sanitize_content


# Patterns for sensitive data that should not be logged
SENSITIVE_PATTERNS = [
    r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+',  # Passwords
    r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+',     # Tokens
    r'key["\']?\s*[:=]\s*["\']?[^"\'\s]+',       # API keys
    r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]+',    # Secrets
    r'auth["\']?\s*[:=]\s*["\']?[^"\'\s]+',      # Auth tokens
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card numbers
    r'\b\d{3}-\d{2}-\d{4}\b',                    # SSN format
]

# Compile patterns for performance
COMPILED_SENSITIVE_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SENSITIVE_PATTERNS]


class SecurityLogger:
    """Security-focused logger that sanitizes sensitive information."""
    
    def __init__(self, name: str, sanitize_logs: bool = True):
        """
        Initialize security logger.
        
        Args:
            name: Logger name
            sanitize_logs: Whether to sanitize log messages
        """
        self.logger = logging.getLogger(name)
        self.sanitize_logs = sanitize_logs
        self._setup_formatter()
    
    def _setup_formatter(self) -> None:
        """Setup secure log formatter."""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Ensure handlers have the formatter
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            for handler in self.logger.handlers:
                handler.setFormatter(formatter)
    
    def _sanitize_message(self, message: str) -> str:
        """
        Sanitize log message to remove sensitive information.
        
        Args:
            message: Original message
            
        Returns:
            Sanitized message
        """
        if not self.sanitize_logs:
            return message
        
        sanitized = message
        
        # Replace sensitive patterns
        for pattern in COMPILED_SENSITIVE_PATTERNS:
            sanitized = pattern.sub('[REDACTED]', sanitized)
        
        # Remove potential file paths that might contain sensitive info
        sanitized = re.sub(r'/[^\s]*(?:password|secret|key|token)[^\s]*', '[REDACTED_PATH]', sanitized)
        
        # Sanitize content for other security issues
        try:
            sanitized = sanitize_content(sanitized, max_length=10000)
        except Exception:
            # If sanitization fails, use a safe fallback
            sanitized = "[LOG_SANITIZATION_FAILED]"
        
        return sanitized
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with sanitization."""
        sanitized_message = self._sanitize_message(str(message))
        self.logger.debug(sanitized_message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with sanitization."""
        sanitized_message = self._sanitize_message(str(message))
        self.logger.info(sanitized_message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with sanitization."""
        sanitized_message = self._sanitize_message(str(message))
        self.logger.warning(sanitized_message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with sanitization."""
        sanitized_message = self._sanitize_message(str(message))
        self.logger.error(sanitized_message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with sanitization."""
        sanitized_message = self._sanitize_message(str(message))
        self.logger.critical(sanitized_message, **kwargs)


def get_security_logger(name: str, sanitize_logs: bool = True) -> SecurityLogger:
    """
    Get a security logger instance.
    
    Args:
        name: Logger name
        sanitize_logs: Whether to sanitize log messages
        
    Returns:
        SecurityLogger instance
    """
    return SecurityLogger(name, sanitize_logs)


def log_security_event(event_type: str, 
                      details: Dict[str, Any],
                      severity: str = "INFO",
                      logger_name: str = "security") -> None:
    """
    Log a security event with structured data.
    
    Args:
        event_type: Type of security event
        details: Event details
        severity: Log severity level
        logger_name: Logger name to use
    """
    security_logger = get_security_logger(logger_name)
    
    # Create structured log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": sanitize_log_data(details),
    }
    
    # Convert to JSON string
    try:
        log_message = json.dumps(log_entry, default=str)
    except Exception:
        log_message = f"Security event: {event_type} (JSON serialization failed)"
    
    # Log at appropriate level
    if severity.upper() == "DEBUG":
        security_logger.debug(log_message)
    elif severity.upper() == "INFO":
        security_logger.info(log_message)
    elif severity.upper() == "WARNING":
        security_logger.warning(log_message)
    elif severity.upper() == "ERROR":
        security_logger.error(log_message)
    elif severity.upper() == "CRITICAL":
        security_logger.critical(log_message)
    else:
        security_logger.info(log_message)


def sanitize_log_data(data: Any, max_depth: int = 5, current_depth: int = 0) -> Any:
    """
    Recursively sanitize data for logging.
    
    Args:
        data: Data to sanitize
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth
        
    Returns:
        Sanitized data
    """
    if current_depth > max_depth:
        return "[MAX_DEPTH_EXCEEDED]"
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Sanitize key
            safe_key = str(key)[:100]  # Limit key length
            
            # Check if key suggests sensitive data
            if any(sensitive in safe_key.lower() for sensitive in ['password', 'token', 'key', 'secret', 'auth']):
                sanitized[safe_key] = "[REDACTED]"
            else:
                sanitized[safe_key] = sanitize_log_data(value, max_depth, current_depth + 1)
        
        return sanitized
    
    elif isinstance(data, (list, tuple)):
        return [sanitize_log_data(item, max_depth, current_depth + 1) for item in data[:100]]  # Limit list size
    
    elif isinstance(data, str):
        # Limit string length and sanitize
        limited_str = data[:1000]  # Limit to 1000 characters
        
        # Check for sensitive patterns
        for pattern in COMPILED_SENSITIVE_PATTERNS:
            if pattern.search(limited_str):
                return "[REDACTED_STRING]"
        
        # Basic sanitization
        try:
            return sanitize_content(limited_str, max_length=1000)
        except Exception:
            return "[SANITIZATION_FAILED]"
    
    elif isinstance(data, Path):
        # Sanitize file paths
        path_str = str(data)
        if any(sensitive in path_str.lower() for sensitive in ['password', 'secret', 'key', 'token']):
            return "[REDACTED_PATH]"
        return path_str[:500]  # Limit path length
    
    elif isinstance(data, (int, float, bool)) or data is None:
        return data
    
    else:
        # Convert other types to string and sanitize
        try:
            str_data = str(data)[:500]  # Limit length
            return sanitize_content(str_data, max_length=500)
        except Exception:
            return "[CONVERSION_FAILED]"


def log_file_access(file_path: Union[str, Path], 
                   operation: str,
                   success: bool = True,
                   error_message: Optional[str] = None) -> None:
    """
    Log file access operations for security auditing.
    
    Args:
        file_path: Path to the file
        operation: Type of operation (read, write, delete, etc.)
        success: Whether operation was successful
        error_message: Error message if operation failed
    """
    details = {
        "file_path": str(file_path),
        "operation": operation,
        "success": success,
    }
    
    if error_message:
        details["error"] = error_message
    
    severity = "INFO" if success else "WARNING"
    log_security_event("file_access", details, severity)


def log_input_validation(input_type: str,
                        validation_result: bool,
                        issues: Optional[List[str]] = None) -> None:
    """
    Log input validation results.
    
    Args:
        input_type: Type of input being validated
        validation_result: Whether validation passed
        issues: List of validation issues if any
    """
    details = {
        "input_type": input_type,
        "validation_passed": validation_result,
    }
    
    if issues:
        details["issues"] = issues[:10]  # Limit number of issues logged
    
    severity = "DEBUG" if validation_result else "WARNING"
    log_security_event("input_validation", details, severity)


def log_template_processing(template_name: str,
                           operation: str,
                           success: bool = True,
                           security_issues: Optional[List[str]] = None) -> None:
    """
    Log template processing for security monitoring.
    
    Args:
        template_name: Name of the template
        operation: Operation being performed
        success: Whether operation was successful
        security_issues: Any security issues detected
    """
    details = {
        "template_name": template_name,
        "operation": operation,
        "success": success,
    }
    
    if security_issues:
        details["security_issues"] = security_issues[:5]  # Limit issues logged
    
    severity = "INFO" if success and not security_issues else "WARNING"
    log_security_event("template_processing", details, severity)


def setup_secure_logging(log_level: str = "INFO",
                        log_file: Optional[Path] = None,
                        max_log_size: int = 10 * 1024 * 1024,
                        backup_count: int = 5) -> None:
    """
    Setup secure logging configuration.
    
    Args:
        log_level: Logging level
        log_file: Optional log file path
        max_log_size: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
    """
    import logging.handlers
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation if specified
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_log_size,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # Set secure permissions on log file
            try:
                log_file.chmod(0o600)  # Owner read/write only
            except Exception:
                pass  # Ignore permission errors
                
        except Exception as e:
            logging.warning(f"Failed to setup file logging: {e}")
    
    logging.info("Secure logging configured")
