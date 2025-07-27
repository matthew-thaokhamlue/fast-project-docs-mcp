"""
File processor registry for the MCP Document Generator.

This module manages the registration and lookup of file processors
based on file extensions and provides a unified interface for file processing.
"""

from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import logging
import asyncio

from .base import FileProcessor
from .markdown import MarkdownProcessor
from .text import TextProcessor
from .json_processor import JSONProcessor
from .yaml_processor import YAMLProcessor
from .pdf import PDFProcessor
from .image import ImageProcessor
from ..models.core import FileContent
from ..exceptions import UnsupportedFormatError, FileProcessingError


logger = logging.getLogger(__name__)


class FileProcessorRegistry:
    """Registry for managing file processors."""
    
    def __init__(self):
        """Initialize the registry with default processors."""
        self._processors: Dict[str, FileProcessor] = {}
        self._extension_map: Dict[str, str] = {}
        
        # Register default processors
        self._register_default_processors()
    
    def _register_default_processors(self) -> None:
        """Register all default file processors."""
        default_processors = [
            ('markdown', MarkdownProcessor()),
            ('text', TextProcessor()),
            ('json', JSONProcessor()),
            ('yaml', YAMLProcessor()),
            ('pdf', PDFProcessor()),
            ('image', ImageProcessor()),
        ]
        
        for name, processor in default_processors:
            try:
                self.register_processor(name, processor)
                logger.debug(f"Registered processor: {name}")
            except Exception as e:
                logger.error(f"Failed to register processor {name}: {e}")
    
    def register_processor(self, name: str, processor: FileProcessor) -> None:
        """Register a file processor."""
        if not isinstance(processor, FileProcessor):
            raise ValueError(f"Processor must be an instance of FileProcessor, got {type(processor)}")
        
        self._processors[name] = processor
        
        # Map extensions to processor name
        for ext in processor.supported_extensions:
            if ext in self._extension_map:
                logger.warning(f"Extension {ext} already mapped to {self._extension_map[ext]}, overriding with {name}")
            self._extension_map[ext] = name
        
        logger.info(f"Registered processor '{name}' for extensions: {processor.supported_extensions}")
    
    def unregister_processor(self, name: str) -> None:
        """Unregister a file processor."""
        if name not in self._processors:
            raise ValueError(f"Processor '{name}' is not registered")
        
        processor = self._processors[name]
        
        # Remove extension mappings
        for ext in processor.supported_extensions:
            if self._extension_map.get(ext) == name:
                del self._extension_map[ext]
        
        del self._processors[name]
        logger.info(f"Unregistered processor: {name}")
    
    def get_processor(self, file_path: Path) -> FileProcessor:
        """Get the appropriate processor for a file."""
        extension = file_path.suffix.lower()
        
        if extension not in self._extension_map:
            raise UnsupportedFormatError(str(file_path), extension)
        
        processor_name = self._extension_map[extension]
        return self._processors[processor_name]
    
    def can_process(self, file_path: Path) -> bool:
        """Check if a file can be processed."""
        extension = file_path.suffix.lower()
        return extension in self._extension_map
    
    async def process_file(self, file_path: Path) -> FileContent:
        """Process a file using the appropriate processor."""
        try:
            processor = self.get_processor(file_path)
            return await processor.process_file(file_path)
        except UnsupportedFormatError:
            raise
        except Exception as e:
            raise FileProcessingError(
                f"Failed to process file {file_path}: {str(e)}",
                str(file_path),
                [
                    "Check if the file is corrupted or locked",
                    "Verify file permissions",
                    "Try with a different file",
                    "Check processor-specific requirements"
                ]
            )
    
    async def process_files(self, file_paths: List[Path], 
                           max_concurrent: int = 5) -> List[FileContent]:
        """Process multiple files concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_file(file_path: Path) -> Optional[FileContent]:
            async with semaphore:
                try:
                    return await self.process_file(file_path)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    return None
        
        # Process files concurrently
        tasks = [process_single_file(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        successful_results = []
        for result in results:
            if isinstance(result, FileContent):
                successful_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"File processing exception: {result}")
        
        return successful_results
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions."""
        return list(self._extension_map.keys())
    
    def get_processor_info(self, processor_name: str) -> Dict[str, Any]:
        """Get information about a specific processor."""
        if processor_name not in self._processors:
            raise ValueError(f"Processor '{processor_name}' is not registered")
        
        return self._processors[processor_name].get_processor_info()
    
    def get_all_processors_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered processors."""
        return {
            name: processor.get_processor_info()
            for name, processor in self._processors.items()
        }
    
    def get_processor_for_extension(self, extension: str) -> Optional[str]:
        """Get processor name for a specific extension."""
        return self._extension_map.get(extension.lower())
    
    def list_processors(self) -> List[str]:
        """List all registered processor names."""
        return list(self._processors.keys())
    
    def validate_processors(self) -> Dict[str, List[str]]:
        """Validate all processors and return any issues."""
        issues = {}
        
        for name, processor in self._processors.items():
            processor_issues = []
            
            # Check if processor has required methods
            required_methods = ['process_file', 'can_process', '_extract_content']
            for method in required_methods:
                if not hasattr(processor, method):
                    processor_issues.append(f"Missing required method: {method}")
            
            # Check if supported extensions are valid
            if not processor.supported_extensions:
                processor_issues.append("No supported extensions defined")
            
            for ext in processor.supported_extensions:
                if not ext.startswith('.'):
                    processor_issues.append(f"Invalid extension format: {ext} (should start with '.')")
            
            if processor_issues:
                issues[name] = processor_issues
        
        return issues
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            'total_processors': len(self._processors),
            'total_extensions': len(self._extension_map),
            'processors': list(self._processors.keys()),
            'extensions': list(self._extension_map.keys()),
            'extension_mapping': dict(self._extension_map)
        }


# Global registry instance
_global_registry: Optional[FileProcessorRegistry] = None


def get_registry() -> FileProcessorRegistry:
    """Get the global file processor registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = FileProcessorRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    _global_registry = None
