"""
PDF file processor for the MCP Document Generator.

This processor handles .pdf files, extracting text content using PyPDF2.
"""

from pathlib import Path
from typing import Any, Dict
import logging

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from .base import FileProcessor
from ..exceptions import FileProcessingError


logger = logging.getLogger(__name__)


class PDFProcessor(FileProcessor):
    """Processor for PDF files (.pdf)."""
    
    def __init__(self):
        super().__init__(['.pdf'])
        # Increase max file size for PDFs
        self.max_file_size = 100 * 1024 * 1024  # 100MB
    
    async def _extract_content(self, file_path: Path) -> str:
        """Extract text content from PDF file."""
        if not PDF_AVAILABLE:
            raise FileProcessingError(
                f"PyPDF2 library not available for processing {file_path}",
                str(file_path),
                [
                    "Install PyPDF2: pip install PyPDF2",
                    "Convert PDF to text format manually",
                    "Use a different file format"
                ]
            )
        
        try:
            # Read PDF file
            binary_content = await self._read_binary_file(file_path)
            
            # Create PDF reader from bytes
            from io import BytesIO
            pdf_stream = BytesIO(binary_content)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                raise FileProcessingError(
                    f"PDF file is encrypted: {file_path}",
                    str(file_path),
                    [
                        "Decrypt the PDF file first",
                        "Provide the password if available",
                        "Use an unencrypted version of the PDF"
                    ]
                )
            
            # Extract text from all pages
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(f"--- Page {page_num + 1} ---")
                        text_content.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1} in {file_path}: {e}")
                    text_content.append(f"--- Page {page_num + 1} (extraction failed) ---")
            
            if not text_content:
                raise FileProcessingError(
                    f"No text content could be extracted from PDF: {file_path}",
                    str(file_path),
                    [
                        "PDF may contain only images or scanned content",
                        "Try using OCR tools for image-based PDFs",
                        "Check if PDF is corrupted"
                    ]
                )
            
            extracted_text = "\n\n".join(text_content)
            return self._clean_extracted_text(extracted_text)
            
        except FileProcessingError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise FileProcessingError(
                f"Failed to process PDF file {file_path}: {str(e)}",
                str(file_path),
                [
                    "Check if PDF file is corrupted",
                    "Ensure PDF is not password protected",
                    "Try with a different PDF file",
                    "Convert PDF to text format using external tools"
                ]
            )
    
    async def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from PDF file including document properties."""
        metadata = await super()._extract_metadata(file_path)
        
        if not PDF_AVAILABLE:
            metadata['pdf_available'] = False
            return metadata
        
        try:
            binary_content = await self._read_binary_file(file_path)
            
            from io import BytesIO
            pdf_stream = BytesIO(binary_content)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            metadata['pdf_available'] = True
            metadata['page_count'] = len(pdf_reader.pages)
            metadata['is_encrypted'] = pdf_reader.is_encrypted
            
            # Extract PDF metadata if available
            if pdf_reader.metadata:
                pdf_meta = pdf_reader.metadata
                metadata['pdf_metadata'] = {
                    'title': pdf_meta.get('/Title', ''),
                    'author': pdf_meta.get('/Author', ''),
                    'subject': pdf_meta.get('/Subject', ''),
                    'creator': pdf_meta.get('/Creator', ''),
                    'producer': pdf_meta.get('/Producer', ''),
                    'creation_date': str(pdf_meta.get('/CreationDate', '')),
                    'modification_date': str(pdf_meta.get('/ModDate', ''))
                }
            
            # Analyze page content
            page_stats = self._analyze_pages(pdf_reader)
            metadata.update(page_stats)
            
        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata from {file_path}: {e}")
            metadata['pdf_processing_error'] = str(e)
        
        return metadata
    
    def _analyze_pages(self, pdf_reader: 'PyPDF2.PdfReader') -> Dict[str, Any]:
        """Analyze PDF pages for content statistics."""
        stats = {
            'pages_with_text': 0,
            'pages_with_images': 0,
            'total_characters': 0,
            'average_chars_per_page': 0,
            'page_sizes': [],
            'text_extraction_errors': 0
        }
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                # Extract text and count characters
                text = page.extract_text()
                char_count = len(text.strip())
                
                if char_count > 0:
                    stats['pages_with_text'] += 1
                    stats['total_characters'] += char_count
                
                # Check for images (basic detection)
                if '/XObject' in page.get('/Resources', {}):
                    xobjects = page['/Resources']['/XObject'].get_object()
                    for obj in xobjects:
                        if xobjects[obj]['/Subtype'] == '/Image':
                            stats['pages_with_images'] += 1
                            break
                
                # Get page dimensions if available
                if '/MediaBox' in page:
                    media_box = page['/MediaBox']
                    width = float(media_box[2]) - float(media_box[0])
                    height = float(media_box[3]) - float(media_box[1])
                    stats['page_sizes'].append({'width': width, 'height': height})
                
            except Exception as e:
                logger.debug(f"Error analyzing page {page_num + 1}: {e}")
                stats['text_extraction_errors'] += 1
        
        # Calculate averages
        if stats['pages_with_text'] > 0:
            stats['average_chars_per_page'] = stats['total_characters'] / stats['pages_with_text']
        
        # Analyze page sizes
        if stats['page_sizes']:
            widths = [size['width'] for size in stats['page_sizes']]
            heights = [size['height'] for size in stats['page_sizes']]
            stats['average_page_width'] = sum(widths) / len(widths)
            stats['average_page_height'] = sum(heights) / len(heights)
            
            # Detect common page sizes
            common_sizes = self._detect_common_page_sizes(stats['page_sizes'])
            stats['common_page_sizes'] = common_sizes
        
        return stats
    
    def _detect_common_page_sizes(self, page_sizes: list) -> list:
        """Detect common page sizes (A4, Letter, etc.)."""
        common_sizes = []
        
        # Common page sizes in points (72 points = 1 inch)
        standard_sizes = {
            'A4': (595, 842),
            'Letter': (612, 792),
            'Legal': (612, 1008),
            'A3': (842, 1191),
            'A5': (420, 595),
            'Tabloid': (792, 1224)
        }
        
        for size in page_sizes:
            width, height = size['width'], size['height']
            
            # Check both orientations
            for name, (std_width, std_height) in standard_sizes.items():
                # Allow 5% tolerance
                tolerance = 0.05
                
                # Portrait orientation
                if (abs(width - std_width) / std_width < tolerance and 
                    abs(height - std_height) / std_height < tolerance):
                    common_sizes.append(f"{name} (Portrait)")
                    break
                
                # Landscape orientation
                elif (abs(width - std_height) / std_height < tolerance and 
                      abs(height - std_width) / std_width < tolerance):
                    common_sizes.append(f"{name} (Landscape)")
                    break
        
        # Return unique sizes
        return list(set(common_sizes))
