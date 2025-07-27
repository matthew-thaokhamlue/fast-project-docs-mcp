"""
YAML file processor for the MCP Document Generator.

This processor handles .yaml and .yml files, extracting structured data
and converting it to readable text format.
"""

from pathlib import Path
from typing import Any, Dict, List
import logging

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .base import FileProcessor
from ..exceptions import FileProcessingError


logger = logging.getLogger(__name__)


class YAMLProcessor(FileProcessor):
    """Processor for YAML files (.yaml, .yml)."""
    
    def __init__(self):
        super().__init__(['.yaml', '.yml'])
        self.max_depth = 10  # Prevent infinite recursion
    
    async def _extract_content(self, file_path: Path) -> str:
        """Extract content from YAML file and convert to readable text."""
        if not YAML_AVAILABLE:
            # Fall back to treating as text file
            logger.warning("PyYAML not available, treating YAML as plain text")
            content = await self._read_text_file(file_path)
            return self._clean_extracted_text(content)
        
        try:
            raw_content = await self._read_text_file(file_path)
            
            # Parse YAML (handle multiple documents)
            documents = list(yaml.safe_load_all(raw_content))
            
            if len(documents) == 1:
                # Single document
                readable_text = self._yaml_to_text(documents[0])
            else:
                # Multiple documents
                doc_texts = []
                for i, doc in enumerate(documents):
                    doc_texts.append(f"--- Document {i + 1} ---")
                    doc_texts.append(self._yaml_to_text(doc))
                readable_text = "\n\n".join(doc_texts)
            
            return self._clean_extracted_text(readable_text)
            
        except yaml.YAMLError as e:
            raise FileProcessingError(
                f"Invalid YAML format in {file_path}: {str(e)}",
                str(file_path),
                [
                    "Validate YAML syntax using a YAML validator",
                    "Check indentation (use spaces, not tabs)",
                    "Ensure proper quoting of special characters",
                    "Verify list and dictionary structure"
                ]
            )
        except Exception as e:
            raise FileProcessingError(
                f"Failed to process YAML file {file_path}: {str(e)}",
                str(file_path)
            )
    
    async def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from YAML file including structure analysis."""
        metadata = await super()._extract_metadata(file_path)
        
        if not YAML_AVAILABLE:
            metadata['yaml_available'] = False
            return metadata
        
        try:
            raw_content = await self._read_text_file(file_path)
            documents = list(yaml.safe_load_all(raw_content))
            
            metadata['yaml_available'] = True
            metadata['document_count'] = len(documents)
            
            # Analyze structure of all documents
            if documents:
                structure_info = self._analyze_yaml_structure(documents)
                metadata.update(structure_info)
                
                # Store first document for potential use
                if documents[0] is not None:
                    metadata['first_document'] = documents[0]
            
        except Exception as e:
            logger.warning(f"Failed to extract YAML metadata from {file_path}: {e}")
        
        return metadata
    
    def _yaml_to_text(self, data: Any, depth: int = 0, key: str = None) -> str:
        """Convert YAML data to readable text format."""
        if depth > self.max_depth:
            return "[Maximum depth reached]"
        
        if data is None:
            return "null"
        
        indent = "  " * depth
        result = []
        
        if key:
            result.append(f"{indent}{key}:")
            indent += "  "
        
        if isinstance(data, dict):
            if not data:
                result.append(f"{indent}(empty mapping)")
            else:
                for k, v in data.items():
                    if isinstance(v, (dict, list)):
                        result.append(self._yaml_to_text(v, depth + 1, k))
                    else:
                        result.append(f"{indent}{k}: {self._format_yaml_value(v)}")
        
        elif isinstance(data, list):
            if not data:
                result.append(f"{indent}(empty sequence)")
            else:
                for i, item in enumerate(data):
                    if isinstance(item, (dict, list)):
                        result.append(f"{indent}- Item {i + 1}:")
                        result.append(self._yaml_to_text(item, depth + 1))
                    else:
                        result.append(f"{indent}- {self._format_yaml_value(item)}")
        
        else:
            result.append(f"{indent}{self._format_yaml_value(data)}")
        
        return "\n".join(result)
    
    def _format_yaml_value(self, value: Any) -> str:
        """Format a YAML value for text output."""
        if isinstance(value, str):
            # Truncate very long strings
            if len(value) > 200:
                return f'"{value[:200]}..."'
            # Check if string needs quoting
            if any(char in value for char in ['\n', '\t', '"', "'"]) or value.strip() != value:
                return f'"{value}"'
            return value
        elif isinstance(value, bool):
            return str(value).lower()
        elif value is None:
            return "null"
        else:
            return str(value)
    
    def _analyze_yaml_structure(self, documents: List[Any]) -> Dict[str, Any]:
        """Analyze YAML structure and return statistics."""
        stats = {
            'total_keys': 0,
            'max_depth': 0,
            'mapping_count': 0,
            'sequence_count': 0,
            'string_count': 0,
            'number_count': 0,
            'boolean_count': 0,
            'null_count': 0,
            'key_patterns': [],
            'value_types': set(),
            'sequence_lengths': [],
            'has_anchors': False,
            'has_tags': False
        }
        
        for doc in documents:
            if doc is not None:
                self._analyze_yaml_node(doc, stats, 0)
        
        # Convert set to list for JSON serialization
        stats['value_types'] = list(stats['value_types'])
        
        # Analyze key patterns
        if stats['key_patterns']:
            stats['unique_keys'] = len(set(stats['key_patterns']))
            stats['common_keys'] = self._get_common_keys(stats['key_patterns'])
        
        # Sequence statistics
        if stats['sequence_lengths']:
            stats['avg_sequence_length'] = (
                sum(stats['sequence_lengths']) / len(stats['sequence_lengths'])
            )
            stats['max_sequence_length'] = max(stats['sequence_lengths'])
        
        return stats
    
    def _analyze_yaml_node(self, node: Any, stats: Dict[str, Any], depth: int) -> None:
        """Recursively analyze a YAML node."""
        stats['max_depth'] = max(stats['max_depth'], depth)
        
        if isinstance(node, dict):
            stats['mapping_count'] += 1
            stats['total_keys'] += len(node)
            
            for key, value in node.items():
                stats['key_patterns'].append(str(key))
                self._analyze_yaml_node(value, stats, depth + 1)
        
        elif isinstance(node, list):
            stats['sequence_count'] += 1
            stats['sequence_lengths'].append(len(node))
            
            for item in node:
                self._analyze_yaml_node(item, stats, depth + 1)
        
        else:
            # Scalar values
            if isinstance(node, str):
                stats['string_count'] += 1
                stats['value_types'].add('string')
            elif isinstance(node, (int, float)):
                stats['number_count'] += 1
                stats['value_types'].add('number')
            elif isinstance(node, bool):
                stats['boolean_count'] += 1
                stats['value_types'].add('boolean')
            elif node is None:
                stats['null_count'] += 1
                stats['value_types'].add('null')
    
    def _get_common_keys(self, keys: List[str]) -> List[Dict[str, Any]]:
        """Get most common keys and their frequencies."""
        from collections import Counter
        
        key_counts = Counter(keys)
        # Return top 10 most common keys
        return [
            {'key': key, 'count': count}
            for key, count in key_counts.most_common(10)
        ]
