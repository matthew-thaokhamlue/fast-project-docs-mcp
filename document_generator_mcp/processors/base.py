"""
Base file processor interface for the MCP Document Generator.

This module defines the abstract base class that all file processors must implement,
providing a consistent interface for content extraction and metadata handling.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
import asyncio
from datetime import datetime

from ..models.core import FileContent
from ..exceptions import FileProcessingError, UnsupportedFormatError
from ..security import (
    validate_file_access,
    get_security_logger,
    log_file_access,
    log_security_event,
    get_secure_defaults,
)


logger = get_security_logger(__name__)


class FileProcessor(ABC):
    """Abstract base class for file processors."""
    
    def __init__(self, supported_extensions: List[str]):
        """Initialize processor with supported file extensions."""
        self.supported_extensions = [ext.lower() for ext in supported_extensions]

        # Get security configuration
        security_config = get_secure_defaults()
        self.max_file_size = security_config.max_file_size
        self.encoding_fallbacks = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        self.security_config = security_config
    
    def can_process(self, file_path: Path) -> bool:
        """Check if this processor can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions
    
    async def process_file(self, file_path: Path) -> FileContent:
        """Process a file and extract its content."""
        try:
            # Security validation
            validated_path = validate_file_access(
                file_path,
                base_directory=Path.cwd() if self.security_config.restrict_to_base_directory else None,
                check_exists=True,
                check_readable=True
            )

            log_file_access(validated_path, "read", success=True)

            # Validate file
            await self._validate_file(validated_path)

            # Log security event
            log_security_event("file_processing_start", {
                "file_path": str(validated_path),
                "file_size": validated_path.stat().st_size,
                "processor_type": self.__class__.__name__
            })

            # Extract content using specific processor implementation
            extracted_text = await self._extract_content(validated_path)

            # Extract metadata
            metadata = await self._extract_metadata(validated_path)

            # Create FileContent object
            file_content = FileContent(
                file_path=validated_path,
                extracted_text=extracted_text,
                metadata=metadata,
                processing_time=datetime.now(),
                file_size=validated_path.stat().st_size,
                encoding=metadata.get('encoding', 'utf-8')
            )

            log_security_event("file_processing_success", {
                "file_path": str(validated_path),
                "content_length": len(extracted_text),
                "processor_type": self.__class__.__name__
            })

            logger.debug(f"Successfully processed file: {validated_path}")
            return file_content

        except Exception as e:
            log_file_access(file_path, "read", success=False, error_message=str(e))
            log_security_event("file_processing_error", {
                "file_path": str(file_path),
                "error_type": type(e).__name__,
                "error_message": str(e)[:200]
            }, severity="ERROR")

            logger.error(f"Failed to process file {file_path}: {e}")
            raise FileProcessingError(
                f"Failed to process file {file_path}: {str(e)}",
                str(file_path),
                [
                    "Check if the file is corrupted or locked",
                    "Verify file permissions",
                    "Ensure the file format is supported",
                    "Try with a different file"
                ]
            )
    
    async def _validate_file(self, file_path: Path) -> None:
        """Validate file before processing."""
        if not file_path.exists():
            raise FileProcessingError(f"File does not exist: {file_path}")
        
        if not file_path.is_file():
            raise FileProcessingError(f"Path is not a file: {file_path}")
        
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise FileProcessingError(
                f"File too large: {file_size} bytes (max: {self.max_file_size})",
                str(file_path),
                [
                    f"Reduce file size to under {self.max_file_size // (1024*1024)}MB",
                    "Split large files into smaller chunks",
                    "Use a different file format"
                ]
            )
        
        if file_size == 0:
            raise FileProcessingError(f"File is empty: {file_path}")
        
        if not self.can_process(file_path):
            raise UnsupportedFormatError(str(file_path), file_path.suffix)
    
    @abstractmethod
    async def _extract_content(self, file_path: Path) -> str:
        """Extract text content from the file. Must be implemented by subclasses."""
        pass
    
    async def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from the file. Can be overridden by subclasses."""
        stat = file_path.stat()
        return {
            'file_name': file_path.name,
            'file_extension': file_path.suffix,
            'file_size': stat.st_size,
            'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'processor_type': self.__class__.__name__,
        }
    
    async def _read_text_file(self, file_path: Path, encoding: Optional[str] = None) -> str:
        """Read text file with encoding detection and fallback."""
        if encoding:
            encodings_to_try = [encoding]
        else:
            encodings_to_try = self.encoding_fallbacks
        
        for enc in encodings_to_try:
            try:
                async with asyncio.to_thread(open, file_path, 'r', encoding=enc) as f:
                    content = await asyncio.to_thread(f.read)
                    logger.debug(f"Successfully read {file_path} with encoding {enc}")
                    return content
            except UnicodeDecodeError:
                logger.debug(f"Failed to read {file_path} with encoding {enc}")
                continue
            except Exception as e:
                logger.error(f"Error reading {file_path} with encoding {enc}: {e}")
                continue
        
        raise FileProcessingError(
            f"Could not read file with any supported encoding: {file_path}",
            str(file_path),
            [
                "Check if the file is corrupted",
                "Try converting the file to UTF-8 encoding",
                "Use a different file format"
            ]
        )
    
    async def _read_binary_file(self, file_path: Path) -> bytes:
        """Read binary file content."""
        try:
            async with asyncio.to_thread(open, file_path, 'rb') as f:
                content = await asyncio.to_thread(f.read)
                return content
        except Exception as e:
            raise FileProcessingError(
                f"Could not read binary file: {file_path}: {str(e)}",
                str(file_path)
            )
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip whitespace from each line
            cleaned_line = line.strip()
            cleaned_lines.append(cleaned_line)
        
        # Join lines and remove excessive empty lines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove more than 2 consecutive newlines
        import re
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        return cleaned_text.strip()
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about this processor."""
        return {
            'name': self.__class__.__name__,
            'supported_extensions': self.supported_extensions,
            'max_file_size': self.max_file_size,
            'description': self.__doc__ or "File processor"
        }
