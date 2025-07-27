"""
File processing system for the MCP Document Generator.

This module contains processors for different file formats and the registry
system that manages them.
"""

from .base import FileProcessor
from .registry import FileProcessorRegistry
from .markdown import MarkdownProcessor
from .text import TextProcessor
from .json_processor import JSONProcessor
from .yaml_processor import YAMLProcessor
from .pdf import PDFProcessor
from .image import ImageProcessor

__all__ = [
    "FileProcessor",
    "FileProcessorRegistry",
    "MarkdownProcessor",
    "TextProcessor", 
    "JSONProcessor",
    "YAMLProcessor",
    "PDFProcessor",
    "ImageProcessor",
]
