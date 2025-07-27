"""
Image file processor for the MCP Document Generator.

This processor handles image files (.png, .jpg, .jpeg), extracting text
using OCR when available.
"""

from pathlib import Path
from typing import Any, Dict
import logging

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from .base import FileProcessor
from ..exceptions import FileProcessingError


logger = logging.getLogger(__name__)


class ImageProcessor(FileProcessor):
    """Processor for image files (.png, .jpg, .jpeg)."""
    
    def __init__(self):
        super().__init__(['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'])
        # Increase max file size for images
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    async def _extract_content(self, file_path: Path) -> str:
        """Extract text content from image file using OCR."""
        if not PIL_AVAILABLE:
            raise FileProcessingError(
                f"Pillow library not available for processing {file_path}",
                str(file_path),
                [
                    "Install Pillow: pip install Pillow",
                    "Convert image to text manually",
                    "Use a different file format"
                ]
            )
        
        if not TESSERACT_AVAILABLE:
            logger.warning(f"Tesseract OCR not available for {file_path}, returning image description only")
            return self._get_image_description(file_path)
        
        try:
            # Open and process image
            image = Image.open(file_path)
            
            # Convert to RGB if necessary (for better OCR)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            extracted_text = pytesseract.image_to_string(image)
            
            if not extracted_text.strip():
                # No text found, return image description
                description = self._get_image_description(file_path)
                return f"No text detected in image.\n\n{description}"
            
            # Clean and return extracted text
            cleaned_text = self._clean_extracted_text(extracted_text)
            
            # Add image description as context
            description = self._get_image_description(file_path)
            return f"{cleaned_text}\n\n--- Image Information ---\n{description}"
            
        except Exception as e:
            logger.error(f"OCR failed for {file_path}: {e}")
            # Fall back to image description
            description = self._get_image_description(file_path)
            return f"OCR processing failed: {str(e)}\n\n{description}"
    
    async def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from image file including EXIF data."""
        metadata = await super()._extract_metadata(file_path)
        
        if not PIL_AVAILABLE:
            metadata['pil_available'] = False
            return metadata
        
        try:
            image = Image.open(file_path)
            
            metadata['pil_available'] = True
            metadata['image_format'] = image.format
            metadata['image_mode'] = image.mode
            metadata['image_size'] = image.size
            metadata['width'] = image.width
            metadata['height'] = image.height
            
            # Calculate aspect ratio
            if image.height > 0:
                metadata['aspect_ratio'] = round(image.width / image.height, 2)
            
            # Extract EXIF data if available
            if hasattr(image, '_getexif') and image._getexif():
                exif_data = image._getexif()
                metadata['exif_data'] = self._process_exif_data(exif_data)
            
            # OCR availability and confidence
            metadata['tesseract_available'] = TESSERACT_AVAILABLE
            
            if TESSERACT_AVAILABLE:
                try:
                    # Get OCR confidence data
                    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                    
                    if confidences:
                        metadata['ocr_confidence'] = {
                            'average': sum(confidences) / len(confidences),
                            'min': min(confidences),
                            'max': max(confidences),
                            'word_count': len(confidences)
                        }
                    else:
                        metadata['ocr_confidence'] = {'average': 0, 'word_count': 0}
                        
                except Exception as e:
                    logger.debug(f"Failed to get OCR confidence for {file_path}: {e}")
                    metadata['ocr_error'] = str(e)
            
            # Image analysis
            analysis = self._analyze_image_content(image)
            metadata.update(analysis)
            
        except Exception as e:
            logger.warning(f"Failed to extract image metadata from {file_path}: {e}")
            metadata['image_processing_error'] = str(e)
        
        return metadata
    
    def _get_image_description(self, file_path: Path) -> str:
        """Get basic description of image when OCR is not available."""
        try:
            if PIL_AVAILABLE:
                image = Image.open(file_path)
                return (f"Image file: {file_path.name}\n"
                       f"Format: {image.format}\n"
                       f"Size: {image.width}x{image.height} pixels\n"
                       f"Mode: {image.mode}")
            else:
                return f"Image file: {file_path.name}\n(Image processing not available)"
        except Exception:
            return f"Image file: {file_path.name}\n(Could not read image properties)"
    
    def _process_exif_data(self, exif_data: dict) -> Dict[str, Any]:
        """Process EXIF data and extract relevant information."""
        from PIL.ExifTags import TAGS
        
        processed_exif = {}
        
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            
            # Convert bytes to string if necessary
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8')
                except UnicodeDecodeError:
                    value = str(value)
            
            processed_exif[tag] = value
        
        # Extract commonly useful EXIF fields
        useful_fields = {
            'camera_make': processed_exif.get('Make', ''),
            'camera_model': processed_exif.get('Model', ''),
            'datetime': processed_exif.get('DateTime', ''),
            'orientation': processed_exif.get('Orientation', ''),
            'x_resolution': processed_exif.get('XResolution', ''),
            'y_resolution': processed_exif.get('YResolution', ''),
            'software': processed_exif.get('Software', ''),
        }
        
        return {
            'useful_fields': useful_fields,
            'all_fields': processed_exif
        }
    
    def _analyze_image_content(self, image: 'Image.Image') -> Dict[str, Any]:
        """Analyze image content for additional insights."""
        analysis = {}
        
        try:
            # Color analysis
            if image.mode == 'RGB':
                # Get dominant colors (simplified)
                colors = image.getcolors(maxcolors=256*256*256)
                if colors:
                    # Sort by frequency
                    colors.sort(key=lambda x: x[0], reverse=True)
                    dominant_color = colors[0][1]  # RGB tuple
                    analysis['dominant_color'] = {
                        'rgb': dominant_color,
                        'hex': '#{:02x}{:02x}{:02x}'.format(*dominant_color)
                    }
                    
                    # Check if image is mostly grayscale
                    is_grayscale = all(abs(dominant_color[0] - dominant_color[1]) < 10 and 
                                     abs(dominant_color[1] - dominant_color[2]) < 10 
                                     for _, color in colors[:5])
                    analysis['is_grayscale'] = is_grayscale
            
            # Size classification
            pixel_count = image.width * image.height
            if pixel_count < 100000:  # < 100K pixels
                size_class = 'small'
            elif pixel_count < 2000000:  # < 2M pixels
                size_class = 'medium'
            else:
                size_class = 'large'
            
            analysis['size_classification'] = size_class
            analysis['pixel_count'] = pixel_count
            
            # Aspect ratio classification
            aspect_ratio = image.width / image.height if image.height > 0 else 1
            if 0.9 <= aspect_ratio <= 1.1:
                aspect_class = 'square'
            elif aspect_ratio > 1.5:
                aspect_class = 'wide'
            elif aspect_ratio < 0.67:
                aspect_class = 'tall'
            else:
                aspect_class = 'standard'
            
            analysis['aspect_classification'] = aspect_class
            
        except Exception as e:
            logger.debug(f"Image analysis failed: {e}")
            analysis['analysis_error'] = str(e)
        
        return analysis
