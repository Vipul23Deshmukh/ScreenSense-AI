import cv2
import pytesseract
import numpy as np
import logging
from config import TESSERACT_CMD, OCR_LANGUAGE

# Configure pytesseract path based on config.py
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

logger = logging.getLogger(__name__)

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess the image to improve OCR accuracy.
    Includes grayscale conversion, noise removal, and thresholding.
    """
    # 1. Convert to grayscale if it's a color image
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 2. Noise removal (median blur is good for salt-and-pepper noise)
    blurred = cv2.medianBlur(gray, 3)

    # 3. Thresholding (Otsu's binarization automatically calculates the threshold)
    # Using THRESH_BINARY + THRESH_OTSU
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh

def extract_text(image: np.ndarray) -> str:
    """
    Extract readable text from an image using Tesseract OCR.
    """
    try:
        # Preprocess the image
        processed_img = preprocess_image(image)
        
        # Custom config for Tesseract:
        # --oem 3: Default OCR Engine Mode
        # --psm 6: Assume a single uniform block of text (often better for formatted blocks than default 3)
        custom_config = r'--oem 3 --psm 6'
        
        text = pytesseract.image_to_string(
            processed_img, 
            lang=OCR_LANGUAGE, 
            config=custom_config
        )
        
        # Clean up extracted text
        cleaned_text = text.strip()
        return cleaned_text
    except pytesseract.TesseractNotFoundError:
        logger.error(f"Tesseract not found at {TESSERACT_CMD}. Please ensure it is installed.")
        return ""
    except Exception as e:
        logger.error(f"Error during OCR extraction: {e}")
        return ""