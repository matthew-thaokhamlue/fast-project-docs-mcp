"""
JSON file processor for the MCP Document Generator.

This processor handles .json files, extracting structured data
and converting it to readable text format.
"""

from pathlib import Path
from typing import Any, Dict, List, Union
import json
import logging

from .base import FileProcessor
from ..exceptions import FileProcessingError


logger = logging.getLogger(__name__)


class JSONProcessor(FileProcessor):
    """Processor for JSON files (.json)."""
    
    def __init__(self):
        super().__init__(['.json'])
        self.max_depth = 10  # Prevent infinite recursion
    
    async def _extract_content(self, file_path: Path) -> str:
        """Extract content from JSON file and convert to readable text."""
        try:
            raw_content = await self._read_text_file(file_path)
            data = json.loads(raw_content)
            
            # Convert JSON to readable text format
            readable_text = self._json_to_text(data)
            return self._clean_extracted_text(readable_text)
            
        except json.JSONDecodeError as e:
            raise FileProcessingError(
                f"Invalid JSON format in {file_path}: {str(e)}",
                str(file_path),
                [
                    "Validate JSON syntax using a JSON validator",
                    "Check for missing commas, brackets, or quotes",
                    "Ensure proper escaping of special characters"
                ]
            )
        except Exception as e:
            raise FileProcessingError(
                f"Failed to process JSON file {file_path}: {str(e)}",
                str(file_path)
            )
    
    async def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from JSON file including structure analysis."""
        metadata = await super()._extract_metadata(file_path)
        
        try:
            raw_content = await self._read_text_file(file_path)
            data = json.loads(raw_content)
            
            # Analyze JSON structure
            structure_info = self._analyze_json_structure(data)
            metadata.update(structure_info)
            
            # Store original data for potential use
            metadata['json_data'] = data
            
        except Exception as e:
            logger.warning(f"Failed to extract JSON metadata from {file_path}: {e}")
        
        return metadata
    
    def _json_to_text(self, data: Any, depth: int = 0, key: str = None) -> str:
        """Convert JSON data to readable text format."""
        if depth > self.max_depth:
            return "[Maximum depth reached]"
        
        indent = "  " * depth
        result = []
        
        if key:
            result.append(f"{indent}{key}:")
            indent += "  "
        
        if isinstance(data, dict):
            if not data:
                result.append(f"{indent}(empty object)")
            else:
                for k, v in data.items():
                    if isinstance(v, (dict, list)):
                        result.append(self._json_to_text(v, depth + 1, k))
                    else:
                        result.append(f"{indent}{k}: {self._format_value(v)}")
        
        elif isinstance(data, list):
            if not data:
                result.append(f"{indent}(empty list)")
            else:
                for i, item in enumerate(data):
                    if isinstance(item, (dict, list)):
                        result.append(f"{indent}[{i}]:")
                        result.append(self._json_to_text(item, depth + 1))
                    else:
                        result.append(f"{indent}[{i}]: {self._format_value(item)}")
        
        else:
            result.append(f"{indent}{self._format_value(data)}")
        
        return "\n".join(result)
    
    def _format_value(self, value: Any) -> str:
        """Format a JSON value for text output."""
        if isinstance(value, str):
            # Truncate very long strings
            if len(value) > 200:
                return f'"{value[:200]}..."'
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        elif value is None:
            return "null"
        else:
            return str(value)
    
    def _analyze_json_structure(self, data: Any, depth: int = 0) -> Dict[str, Any]:
        """Analyze JSON structure and return statistics."""
        if depth == 0:
            # Initialize counters for root analysis
            self._structure_stats = {
                'total_keys': 0,
                'max_depth': 0,
                'object_count': 0,
                'array_count': 0,
                'string_count': 0,
                'number_count': 0,
                'boolean_count': 0,
                'null_count': 0,
                'key_patterns': [],
                'value_types': set(),
                'array_lengths': []
            }
        
        # Update max depth
        self._structure_stats['max_depth'] = max(self._structure_stats['max_depth'], depth)
        
        if isinstance(data, dict):
            self._structure_stats['object_count'] += 1
            self._structure_stats['total_keys'] += len(data)
            
            for key, value in data.items():
                # Collect key patterns
                self._structure_stats['key_patterns'].append(key)
                
                # Recursively analyze nested structures
                self._analyze_json_structure(value, depth + 1)
        
        elif isinstance(data, list):
            self._structure_stats['array_count'] += 1
            self._structure_stats['array_lengths'].append(len(data))
            
            for item in data:
                self._analyze_json_structure(item, depth + 1)
        
        else:
            # Leaf values
            if isinstance(data, str):
                self._structure_stats['string_count'] += 1
                self._structure_stats['value_types'].add('string')
            elif isinstance(data, (int, float)):
                self._structure_stats['number_count'] += 1
                self._structure_stats['value_types'].add('number')
            elif isinstance(data, bool):
                self._structure_stats['boolean_count'] += 1
                self._structure_stats['value_types'].add('boolean')
            elif data is None:
                self._structure_stats['null_count'] += 1
                self._structure_stats['value_types'].add('null')
        
        # Return stats only at root level
        if depth == 0:
            # Convert set to list for JSON serialization
            self._structure_stats['value_types'] = list(self._structure_stats['value_types'])
            
            # Analyze key patterns
            key_patterns = self._structure_stats['key_patterns']
            self._structure_stats['unique_keys'] = len(set(key_patterns))
            self._structure_stats['common_keys'] = self._get_common_keys(key_patterns)
            
            # Array statistics
            if self._structure_stats['array_lengths']:
                self._structure_stats['avg_array_length'] = (
                    sum(self._structure_stats['array_lengths']) / 
                    len(self._structure_stats['array_lengths'])
                )
                self._structure_stats['max_array_length'] = max(self._structure_stats['array_lengths'])
            
            return self._structure_stats
        
        return {}
    
    def _get_common_keys(self, keys: List[str]) -> List[Dict[str, Any]]:
        """Get most common keys and their frequencies."""
        from collections import Counter
        
        key_counts = Counter(keys)
        # Return top 10 most common keys
        return [
            {'key': key, 'count': count}
            for key, count in key_counts.most_common(10)
        ]
