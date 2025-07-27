"""
Markdown file processor for the MCP Document Generator.

This processor handles .md files, extracting content and metadata including
frontmatter, headers, and structured content.
"""

from pathlib import Path
from typing import Any, Dict, List
import re
import logging

try:
    import frontmatter
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

from .base import FileProcessor
from ..exceptions import FileProcessingError


logger = logging.getLogger(__name__)


class MarkdownProcessor(FileProcessor):
    """Processor for Markdown files (.md)."""
    
    def __init__(self):
        super().__init__(['.md', '.markdown'])
        self.markdown_extensions = [
            'extra',
            'codehilite',
            'toc',
            'tables',
            'fenced_code'
        ]
    
    async def _extract_content(self, file_path: Path) -> str:
        """Extract content from Markdown file."""
        # Read the raw markdown content
        raw_content = await self._read_text_file(file_path)
        
        if MARKDOWN_AVAILABLE:
            try:
                # Parse frontmatter if present
                post = frontmatter.loads(raw_content)
                content = post.content
                
                # Store frontmatter in metadata for later use
                self._frontmatter = post.metadata
                
                return self._clean_extracted_text(content)
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter in {file_path}: {e}")
                # Fall back to raw content
                return self._clean_extracted_text(raw_content)
        else:
            logger.warning("frontmatter library not available, using raw content")
            return self._clean_extracted_text(raw_content)
    
    async def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from Markdown file including frontmatter."""
        metadata = await super()._extract_metadata(file_path)
        
        # Add frontmatter if available
        if hasattr(self, '_frontmatter') and self._frontmatter:
            metadata['frontmatter'] = self._frontmatter
        
        # Extract headers and structure
        try:
            raw_content = await self._read_text_file(file_path)
            headers = self._extract_headers(raw_content)
            metadata['headers'] = headers
            metadata['header_count'] = len(headers)
            
            # Extract code blocks
            code_blocks = self._extract_code_blocks(raw_content)
            metadata['code_blocks'] = len(code_blocks)
            metadata['code_languages'] = list(set(block['language'] for block in code_blocks if block['language']))
            
            # Extract links
            links = self._extract_links(raw_content)
            metadata['links'] = links
            metadata['link_count'] = len(links)
            
        except Exception as e:
            logger.warning(f"Failed to extract markdown metadata from {file_path}: {e}")
        
        return metadata
    
    def _extract_headers(self, content: str) -> List[Dict[str, Any]]:
        """Extract headers from markdown content."""
        headers = []
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        for match in header_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            headers.append({
                'level': level,
                'text': text,
                'anchor': self._create_anchor(text)
            })
        
        return headers
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract code blocks from markdown content."""
        code_blocks = []
        
        # Fenced code blocks (```language)
        fenced_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
        for match in fenced_pattern.finditer(content):
            language = match.group(1) or 'text'
            code = match.group(2)
            code_blocks.append({
                'type': 'fenced',
                'language': language,
                'code': code.strip()
            })
        
        # Indented code blocks
        indented_pattern = re.compile(r'^( {4}|\t)(.+)$', re.MULTILINE)
        indented_blocks = []
        current_block = []
        
        for line in content.split('\n'):
            if indented_pattern.match(line):
                current_block.append(line[4:] if line.startswith('    ') else line[1:])
            else:
                if current_block:
                    indented_blocks.append('\n'.join(current_block))
                    current_block = []
        
        if current_block:
            indented_blocks.append('\n'.join(current_block))
        
        for block in indented_blocks:
            if block.strip():
                code_blocks.append({
                    'type': 'indented',
                    'language': 'text',
                    'code': block.strip()
                })
        
        return code_blocks
    
    def _extract_links(self, content: str) -> List[Dict[str, Any]]:
        """Extract links from markdown content."""
        links = []
        
        # Markdown links [text](url)
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        for match in link_pattern.finditer(content):
            text = match.group(1)
            url = match.group(2)
            links.append({
                'type': 'markdown',
                'text': text,
                'url': url,
                'is_internal': not url.startswith(('http://', 'https://'))
            })
        
        # Reference links [text][ref]
        ref_pattern = re.compile(r'\[([^\]]+)\]\[([^\]]+)\]')
        for match in ref_pattern.finditer(content):
            text = match.group(1)
            ref = match.group(2)
            links.append({
                'type': 'reference',
                'text': text,
                'reference': ref
            })
        
        # Auto links <url>
        auto_pattern = re.compile(r'<(https?://[^>]+)>')
        for match in auto_pattern.finditer(content):
            url = match.group(1)
            links.append({
                'type': 'auto',
                'text': url,
                'url': url,
                'is_internal': False
            })
        
        return links
    
    def _create_anchor(self, text: str) -> str:
        """Create URL anchor from header text."""
        # Convert to lowercase and replace spaces with hyphens
        anchor = text.lower().replace(' ', '-')
        # Remove non-alphanumeric characters except hyphens
        anchor = re.sub(r'[^a-z0-9-]', '', anchor)
        # Remove multiple consecutive hyphens
        anchor = re.sub(r'-+', '-', anchor)
        # Remove leading/trailing hyphens
        anchor = anchor.strip('-')
        return anchor
