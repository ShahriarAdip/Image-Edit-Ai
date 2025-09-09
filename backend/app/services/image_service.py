# /backend/app/services/image_service.py
import io
import uuid
from PIL import Image, ImageEnhance
from rembg import remove
from ..config import config

class ImageService:
    @staticmethod
    def validate_extension(filename: str) -> bool:
        """Validate if file extension is allowed"""
        if not filename or '.' not in filename:
            return False
            
        extension = filename.split('.')[-1].lower()
        return extension in config.ALLOWED_EXTENSIONS

    @staticmethod
    def generate_filename(original_filename: str, suffix: str = "") -> str:
        """Generate unique filename with proper extension"""
        if '.' in original_filename:
            name, extension = original_filename.rsplit('.', 1)
            extension = extension.lower()
        else:
            name, extension = original_filename, "jpg"
            
        # Ensure extension is allowed
        if extension not in config.ALLOWED_EXTENSIONS:
            extension = "jpg"
            
        return f"{uuid.uuid4()}{suffix}.{extension}"

    @staticmethod
    def apply_adjustments(
        image: Image.Image, 
        brightness: float = 1.0, 
        contrast: float = 1.0, 
        saturation: float = 1.0
    ) -> Image.Image:
        """
        Apply image adjustments with bounds checking
        Returns a new image with adjustments applied
        """
        # Create a copy to avoid modifying the original
        result_image = image.copy()
        
        # Apply brightness adjustment
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(result_image)
            # Clamp brightness to prevent extreme values
            adjusted_brightness = max(0.0, min(3.0, brightness))
            result_image = enhancer.enhance(adjusted_brightness)

        # Apply contrast adjustment
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(result_image)
            adjusted_contrast = max(0.0, min(3.0, contrast))
            result_image = enhancer.enhance(adjusted_contrast)

        # Apply saturation adjustment
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(result_image)
            adjusted_saturation = max(0.0, min(3.0, saturation))
            result_image = enhancer.enhance(adjusted_saturation)

        return result_image

    @staticmethod
    def remove_background(image: Image.Image) -> Image.Image:
        """
        Remove the background from an image using rembg
        Returns a new image with transparent background
        """
        try:
            # Convert input image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Remove background
            result_bytes = remove(img_byte_arr)
            
            # Convert bytes back to PIL Image
            return Image.open(io.BytesIO(result_bytes))
            
        except Exception as e:
            raise ValueError(f"Background removal failed: {str(e)}")