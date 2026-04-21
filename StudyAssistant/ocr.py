import cv2
import pytesseract
import numpy as np
import logging
import os

from config import TESSERACT_CMD, OCR_LANGUAGE, OCR_RESIZE_FACTOR

logger = logging.getLogger(__name__)

# Configure pytesseract path based on config.py
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
else:
    logger.error(f"Tesseract not found at {TESSERACT_CMD}")

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess the image to improve OCR accuracy.
    Pipeline: Grayscale -> Resize (2x) -> Threshold
    """
    # 1. Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 2. Resize (Upscale 2x) - Tesseract works better on larger text
    h, w = gray.shape[:2]
    resized = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

    # 3. Threshold (Simple + Otsu's)
    # This creates a high-contrast black and white image
    _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Save debug image
    cv2.imwrite("ocr_debug_processed.png", thresh)
    
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