import io
from PIL import Image
from rembg import remove
import logging

# setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_background(input_image):
    """
    Remove the background from an image using the rembg library.
    """
    try:
        logger.info("Starting background removal process.")

        # Convert input image to bytes
        img_byte_arr = io.BytesIO()
        input_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        logger.info("Image converted to bytes. Calling rembg...")

        # Remove background
        result_bytes = remove(img_byte_arr)
        logger.info("Background removal completed.")

        # Convert bytes back to PIL Image
        result_image = Image.open(io.BytesIO(result_bytes))


        logger.info("Converted result bytes back to PIL Image.")
        return result_image
    
    except Exception as e:
        logger.error(f"Error during background removal: {str(e)}")

        raise Exception(f"Background removal failed. Error: {str(e)}")