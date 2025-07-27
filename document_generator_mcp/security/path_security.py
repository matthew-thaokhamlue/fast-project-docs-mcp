"""
Path security utilities for preventing directory traversal and ensuring safe file access.

This module provides functions to safely handle file paths and prevent
path traversal attacks.
"""

import os
from pathlib import Path
from typing import Optional, Union
import logging

from ..exceptions import ValidationError, ResourceAccessError


logger = logging.getLogger(__name__)


def normalize_path(path: Union[str, Path]) -> Path:
    """
    Normalize a path to prevent traversal attacks.
    
    Args:
        path: Path to normalize
        
    Returns:
        Normalized Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    if not path:
        raise ValidationError("path", ["Path cannot be empty"])
    
    try:
        # Convert to Path object and resolve
        if isinstance(path, str):
            path_obj = Path(path)
        else:
            path_obj = path
        
        # Resolve to absolute path to handle .. and . components
        normalized = path_obj.resolve()
        
        return normalized
        
    except (OSError, ValueError) as e:
        raise ValidationError("path", [f"Invalid path: {str(e)}"])


def is_safe_path(path: Union[str, Path], 
                base_directory: Optional[Path] = None,
                allow_absolute: bool = False) -> bool:
    """
    Check if a path is safe (no traversal attacks).
    
    Args:
        path: Path to check
        base_directory: Base directory to restrict access to
        allow_absolute: Whether to allow absolute paths
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        normalized = normalize_path(path)
        
        # Check if absolute path is allowed
        if normalized.is_absolute() and not allow_absolute:
            if not base_directory:
                logger.warning(f"Absolute path not allowed: {normalized}")
                return False
        
        # If base directory is specified, ensure path is within it
        if base_directory:
            try:
                base_resolved = base_directory.resolve()
                
                # Check if the normalized path starts with base directory
                if not str(normalized).startswith(str(base_resolved)):
                    logger.warning(f"Path outside base directory: {normalized} not in {base_resolved}")
                    return False
                    
            except (OSError, ValueError):
                logger.warning(f"Could not resolve base directory: {base_directory}")
                return False
        
        # Check for dangerous path components
        path_parts = normalized.parts
        dangerous_parts = {'.', '..', '~'}
        
        for part in path_parts:
            if part in dangerous_parts:
                logger.warning(f"Dangerous path component found: {part}")
                return False
        
        # Check for null bytes and control characters
        path_str = str(normalized)
        if '\x00' in path_str or any(ord(c) < 32 for c in path_str if c not in '\t\n\r'):
            logger.warning(f"Path contains invalid characters: {path_str}")
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Error checking path safety: {e}")
        return False


def secure_path_join(base: Union[str, Path], *paths: Union[str, Path]) -> Path:
    """
    Safely join paths, preventing directory traversal.
    
    Args:
        base: Base directory path
        *paths: Path components to join
        
    Returns:
        Safely joined Path object
        
    Raises:
        ValidationError: If resulting path is unsafe
    """
    if not base:
        raise ValidationError("base_path", ["Base path cannot be empty"])
    
    try:
        # Normalize base path
        base_path = normalize_path(base)
        
        # Join all path components
        result_path = base_path
        for path_component in paths:
            if path_component:
                # Ensure path component doesn't start with / or contain ..
                path_str = str(path_component)
                if path_str.startswith('/') or '..' in path_str:
                    raise ValidationError(
                        "path_component",
                        [f"Unsafe path component: {path_component}"]
                    )
                
                result_path = result_path / path_component
        
        # Normalize the final result
        final_path = result_path.resolve()
        
        # Ensure the final path is still within the base directory
        if not str(final_path).startswith(str(base_path)):
            raise ValidationError(
                "joined_path",
                ["Joined path escapes base directory"]
            )
        
        return final_path
        
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError("path_join", [f"Error joining paths: {str(e)}"])


def validate_file_access(file_path: Union[str, Path], 
                        base_directory: Optional[Path] = None,
                        check_exists: bool = True,
                        check_readable: bool = True) -> Path:
    """
    Validate that a file can be safely accessed.
    
    Args:
        file_path: Path to the file
        base_directory: Base directory to restrict access to
        check_exists: Whether to check if file exists
        check_readable: Whether to check if file is readable
        
    Returns:
        Validated Path object
        
    Raises:
        ResourceAccessError: If file cannot be safely accessed
    """
    try:
        # Normalize and validate path
        normalized_path = normalize_path(file_path)
        
        # Check if path is safe
        if not is_safe_path(normalized_path, base_directory):
            raise ResourceAccessError(
                f"Unsafe file path: {file_path}",
                str(file_path),
                [
                    "Use a path within the allowed directory",
                    "Avoid using .. or . in paths",
                    "Use relative paths when possible"
                ]
            )
        
        # Check if file exists
        if check_exists and not normalized_path.exists():
            raise ResourceAccessError(
                f"File does not exist: {normalized_path}",
                str(normalized_path),
                [
                    "Check if the file path is correct",
                    "Ensure the file exists",
                    "Verify file permissions"
                ]
            )
        
        # Check if file is readable
        if check_readable and normalized_path.exists():
            try:
                # Try to read file stats to check accessibility
                normalized_path.stat()
                
                # For files, check if we can open them
                if normalized_path.is_file():
                    with open(normalized_path, 'rb') as f:
                        # Just check if we can open it
                        pass
                        
            except (PermissionError, OSError) as e:
                raise ResourceAccessError(
                    f"Cannot access file: {normalized_path}",
                    str(normalized_path),
                    [
                        "Check file permissions",
                        "Ensure you have read access to the file",
                        "Verify the file is not locked by another process"
                    ]
                )
        
        return normalized_path
        
    except ResourceAccessError:
        raise
    except Exception as e:
        raise ResourceAccessError(
            f"Error validating file access: {str(e)}",
            str(file_path),
            [
                "Check if the file path is valid",
                "Ensure proper file permissions",
                "Verify the file system is accessible"
            ]
        )


def get_safe_temp_path(base_temp_dir: Optional[Path] = None, 
                      prefix: str = "docgen_",
                      suffix: str = "") -> Path:
    """
    Get a safe temporary file path.
    
    Args:
        base_temp_dir: Base temporary directory
        prefix: Filename prefix
        suffix: Filename suffix
        
    Returns:
        Safe temporary file path
    """
    import tempfile
    import uuid
    
    if base_temp_dir:
        temp_dir = base_temp_dir
    else:
        temp_dir = Path(tempfile.gettempdir())
    
    # Create a unique filename
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{prefix}{unique_id}{suffix}"
    
    # Ensure the temp directory exists and is safe
    temp_dir = normalize_path(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    return temp_dir / filename


def cleanup_temp_files(temp_paths: list, ignore_errors: bool = True) -> None:
    """
    Safely cleanup temporary files.
    
    Args:
        temp_paths: List of temporary file paths to cleanup
        ignore_errors: Whether to ignore cleanup errors
    """
    for temp_path in temp_paths:
        try:
            if isinstance(temp_path, (str, Path)):
                path_obj = Path(temp_path)
                if path_obj.exists():
                    if path_obj.is_file():
                        path_obj.unlink()
                    elif path_obj.is_dir():
                        import shutil
                        shutil.rmtree(path_obj)
                    
                    logger.debug(f"Cleaned up temporary file: {path_obj}")
                    
        except Exception as e:
            if not ignore_errors:
                raise
            logger.warning(f"Failed to cleanup temporary file {temp_path}: {e}")


def restrict_file_permissions(file_path: Union[str, Path], 
                            owner_only: bool = True) -> None:
    """
    Restrict file permissions for security.
    
    Args:
        file_path: Path to the file
        owner_only: Whether to restrict access to owner only
    """
    try:
        path_obj = Path(file_path)
        
        if owner_only:
            # Set permissions to owner read/write only (600)
            path_obj.chmod(0o600)
        else:
            # Set permissions to owner read/write, group/others read (644)
            path_obj.chmod(0o644)
            
        logger.debug(f"Set secure permissions for: {path_obj}")
        
    except Exception as e:
        logger.warning(f"Failed to set file permissions for {file_path}: {e}")
        # Don't raise exception as this might not be critical
