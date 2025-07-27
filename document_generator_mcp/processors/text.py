"""
Text file processor for the MCP Document Generator.

This processor handles plain text files (.txt), extracting content
and basic text statistics.
"""

from pathlib import Path
from typing import Any, Dict
import re
import logging

from .base import FileProcessor


logger = logging.getLogger(__name__)


class TextProcessor(FileProcessor):
    """Processor for plain text files (.txt)."""
    
    def __init__(self):
        super().__init__(['.txt', '.text'])
    
    async def _extract_content(self, file_path: Path) -> str:
        """Extract content from text file."""
        content = await self._read_text_file(file_path)
        return self._clean_extracted_text(content)
    
    async def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from text file including statistics."""
        metadata = await super()._extract_metadata(file_path)
        
        try:
            content = await self._read_text_file(file_path)
            
            # Basic text statistics
            lines = content.split('\n')
            words = content.split()
            
            metadata.update({
                'line_count': len(lines),
                'word_count': len(words),
                'character_count': len(content),
                'character_count_no_spaces': len(content.replace(' ', '')),
                'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
                'average_words_per_line': len(words) / len(lines) if lines else 0,
            })
            
            # Detect potential structure
            structure_info = self._analyze_structure(content)
            metadata.update(structure_info)
            
        except Exception as e:
            logger.warning(f"Failed to extract text metadata from {file_path}: {e}")
        
        return metadata
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze text structure and patterns."""
        structure = {
            'has_numbered_lists': False,
            'has_bullet_points': False,
            'has_headers': False,
            'has_code_blocks': False,
            'indentation_levels': 0,
            'common_patterns': []
        }
        
        lines = content.split('\n')
        
        # Check for numbered lists
        numbered_pattern = re.compile(r'^\s*\d+\.\s+')
        if any(numbered_pattern.match(line) for line in lines):
            structure['has_numbered_lists'] = True
            structure['common_patterns'].append('numbered_lists')
        
        # Check for bullet points
        bullet_pattern = re.compile(r'^\s*[-*+]\s+')
        if any(bullet_pattern.match(line) for line in lines):
            structure['has_bullet_points'] = True
            structure['common_patterns'].append('bullet_points')
        
        # Check for potential headers (lines followed by dashes or equals)
        for i, line in enumerate(lines[:-1]):
            next_line = lines[i + 1]
            if (line.strip() and 
                next_line.strip() and 
                all(c in '-=' for c in next_line.strip()) and
                len(next_line.strip()) >= len(line.strip()) * 0.8):
                structure['has_headers'] = True
                structure['common_patterns'].append('underlined_headers')
                break
        
        # Check for code-like blocks (consistent indentation)
        indented_lines = [line for line in lines if line.startswith('    ') or line.startswith('\t')]
        if len(indented_lines) > 3:
            structure['has_code_blocks'] = True
            structure['common_patterns'].append('code_blocks')
        
        # Calculate indentation levels
        indentations = set()
        for line in lines:
            if line.strip():  # Skip empty lines
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    indentations.add(leading_spaces)
        
        structure['indentation_levels'] = len(indentations)
        
        # Check for common document patterns
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['table of contents', 'toc', 'contents:']):
            structure['common_patterns'].append('table_of_contents')
        
        if any(keyword in content_lower for keyword in ['abstract:', 'summary:', 'overview:']):
            structure['common_patterns'].append('structured_document')
        
        if any(keyword in content_lower for keyword in ['todo:', 'fixme:', 'note:', 'warning:']):
            structure['common_patterns'].append('annotations')
        
        # Check for email-like structure
        if '@' in content and any(keyword in content_lower for keyword in ['from:', 'to:', 'subject:']):
            structure['common_patterns'].append('email_format')
        
        # Check for log-like structure
        timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}')
        if len(timestamp_pattern.findall(content)) > 5:
            structure['common_patterns'].append('log_format')
        
        return structure
