"""
Resource analyzer service for the MCP Document Generator.

This service analyzes reference resources, categorizes files by type,
and extracts relevant information for document generation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import logging
import asyncio
from datetime import datetime

from ..models.core import ResourceAnalysis, FileContent
from ..processors.registry import get_registry
from ..exceptions import ResourceAccessError, FileProcessingError


logger = logging.getLogger(__name__)


class ResourceAnalyzerService:
    """Service for analyzing reference resources."""
    
    def __init__(self, max_concurrent_files: int = 10):
        """Initialize the resource analyzer service."""
        self.file_registry = get_registry()
        self.max_concurrent_files = max_concurrent_files
        
        # File categorization keywords
        self.category_keywords = {
            'requirements': [
                'requirement', 'req', 'prd', 'product', 'feature', 'user story',
                'acceptance criteria', 'functional', 'non-functional', 'business'
            ],
            'technical': [
                'api', 'schema', 'database', 'architecture', 'technical', 'spec',
                'specification', 'interface', 'endpoint', 'service', 'component'
            ],
            'design': [
                'design', 'ui', 'ux', 'mockup', 'wireframe', 'prototype',
                'style', 'brand', 'visual', 'layout', 'interface'
            ],
            'documentation': [
                'doc', 'documentation', 'readme', 'guide', 'manual', 'help',
                'tutorial', 'example', 'reference', 'wiki'
            ],
            'configuration': [
                'config', 'configuration', 'settings', 'env', 'environment',
                'deployment', 'docker', 'kubernetes', 'yaml', 'json'
            ],
            'data': [
                'data', 'dataset', 'sample', 'example', 'test', 'fixture',
                'seed', 'migration', 'sql', 'csv', 'excel'
            ]
        }
    
    async def analyze_folder(self, folder_path: Path) -> ResourceAnalysis:
        """Analyze reference resources in a folder."""
        try:
            if not folder_path.exists():
                raise ResourceAccessError(
                    f"Reference folder does not exist: {folder_path}",
                    str(folder_path),
                    [
                        "Create the reference_resources folder",
                        "Check the folder path spelling",
                        "Ensure proper permissions"
                    ]
                )
            
            if not folder_path.is_dir():
                raise ResourceAccessError(
                    f"Path is not a directory: {folder_path}",
                    str(folder_path),
                    ["Provide a valid directory path"]
                )
            
            logger.info(f"Starting analysis of folder: {folder_path}")
            
            # Find all files recursively
            all_files = self._find_files(folder_path)
            logger.info(f"Found {len(all_files)} files to analyze")
            
            # Filter processable files
            processable_files = [f for f in all_files if self.file_registry.can_process(f)]
            skipped_files = len(all_files) - len(processable_files)
            
            if skipped_files > 0:
                logger.info(f"Skipping {skipped_files} files with unsupported formats")
            
            # Process files concurrently
            processed_files = await self._process_files(processable_files)
            
            # Categorize processed files
            categorized_files = await self._categorize_files(processed_files)
            
            # Generate content summary
            content_summary = self._generate_content_summary(categorized_files)
            
            # Collect processing errors
            processing_errors = self._collect_processing_errors(processed_files)
            
            analysis = ResourceAnalysis(
                total_files=len(all_files),
                categorized_files=categorized_files,
                content_summary=content_summary,
                processing_errors=processing_errors,
                supported_formats=self.file_registry.get_supported_extensions(),
                analysis_time=datetime.now()
            )
            
            logger.info(f"Analysis complete: {len(processed_files)} files processed, "
                       f"{len(categorized_files)} categories found")
            
            return analysis
            
        except ResourceAccessError:
            raise
        except Exception as e:
            logger.error(f"Resource analysis failed: {e}")
            raise ResourceAccessError(
                f"Failed to analyze folder {folder_path}: {str(e)}",
                str(folder_path),
                [
                    "Check folder permissions",
                    "Verify folder exists and is accessible",
                    "Try with a different folder path",
                    "Check available disk space"
                ]
            )
    
    def _find_files(self, folder_path: Path) -> List[Path]:
        """Find all files in the folder recursively."""
        files = []
        
        try:
            for item in folder_path.rglob("*"):
                if item.is_file():
                    # Skip hidden files and common non-content files
                    if not self._should_skip_file(item):
                        files.append(item)
        except PermissionError as e:
            logger.warning(f"Permission denied accessing some files in {folder_path}: {e}")
        except Exception as e:
            logger.error(f"Error finding files in {folder_path}: {e}")
        
        return files
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during analysis."""
        # Skip hidden files
        if file_path.name.startswith('.'):
            return True
        
        # Skip common non-content files
        skip_patterns = {
            # System files
            'thumbs.db', 'desktop.ini', '.ds_store',
            # Temporary files
            '~$', '.tmp', '.temp',
            # Lock files
            '.lock', '.lck',
            # Backup files
            '.bak', '.backup', '.old'
        }
        
        file_name_lower = file_path.name.lower()
        for pattern in skip_patterns:
            if pattern in file_name_lower:
                return True
        
        # Skip very large files (>100MB)
        try:
            if file_path.stat().st_size > 100 * 1024 * 1024:
                logger.warning(f"Skipping large file: {file_path} ({file_path.stat().st_size} bytes)")
                return True
        except OSError:
            pass
        
        return False
    
    async def _process_files(self, files: List[Path]) -> List[FileContent]:
        """Process files concurrently."""
        if not files:
            return []
        
        logger.info(f"Processing {len(files)} files with max concurrency {self.max_concurrent_files}")
        
        # Process files in batches to avoid overwhelming the system
        processed_files = []
        batch_size = self.max_concurrent_files
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}: {len(batch)} files")
            
            batch_results = await self.file_registry.process_files(
                batch, 
                max_concurrent=self.max_concurrent_files
            )
            processed_files.extend(batch_results)
        
        logger.info(f"Successfully processed {len(processed_files)} out of {len(files)} files")
        return processed_files
    
    async def _categorize_files(self, files: List[FileContent]) -> Dict[str, List[FileContent]]:
        """Categorize files based on content and filename analysis."""
        categorized = {category: [] for category in self.category_keywords.keys()}
        categorized['uncategorized'] = []
        
        for file_content in files:
            categories = self._classify_file(file_content)
            
            if categories:
                # File can belong to multiple categories
                for category in categories:
                    categorized[category].append(file_content)
            else:
                categorized['uncategorized'].append(file_content)
        
        # Remove empty categories
        categorized = {k: v for k, v in categorized.items() if v}
        
        return categorized
    
    def _classify_file(self, file_content: FileContent) -> List[str]:
        """Classify a file into categories based on content and filename."""
        categories = []
        
        # Analyze filename
        filename_lower = file_content.file_path.name.lower()
        
        # Analyze content (first 1000 characters for efficiency)
        content_sample = file_content.extracted_text[:1000].lower()
        
        # Check each category
        for category, keywords in self.category_keywords.items():
            score = 0
            
            # Check filename
            for keyword in keywords:
                if keyword in filename_lower:
                    score += 2  # Filename matches are weighted higher
            
            # Check content
            for keyword in keywords:
                if keyword in content_sample:
                    score += 1
            
            # Threshold for category assignment
            if score >= 2:
                categories.append(category)
        
        return categories
    
    def _generate_content_summary(self, categorized_files: Dict[str, List[FileContent]]) -> str:
        """Generate a summary of the analyzed content."""
        summary_parts = []
        
        total_files = sum(len(files) for files in categorized_files.values())
        summary_parts.append(f"Analyzed {total_files} files across {len(categorized_files)} categories.")
        
        for category, files in categorized_files.items():
            if files:
                file_types = {}
                total_chars = 0
                
                for file_content in files:
                    ext = file_content.file_path.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
                    total_chars += len(file_content.extracted_text)
                
                type_summary = ", ".join([f"{count} {ext}" for ext, count in file_types.items()])
                avg_size = total_chars // len(files) if files else 0
                
                summary_parts.append(
                    f"- {category.title()}: {len(files)} files ({type_summary}), "
                    f"avg {avg_size} characters"
                )
        
        return "\n".join(summary_parts)
    
    def _collect_processing_errors(self, processed_files: List[FileContent]) -> List[str]:
        """Collect any processing errors from the file processing."""
        # This would be enhanced to collect actual errors from processing
        # For now, return empty list as errors are handled during processing
        return []
