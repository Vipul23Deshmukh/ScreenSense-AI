import cv2
import pytesseract
import numpy as np
import os
import config

logger = config.setup_logger("ocr")

if os.path.exists(config.TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

def preprocess_image(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
        
    # Resize 2x for better OCR
    h, w = gray.shape[:2]
    resized = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    
    # Adaptive Thresholding for better contrast in various lighting/colors
    thresh = cv2.adaptiveThreshold(
        resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Save debug image
    cv2.imwrite("processed_debug.png", thresh)
    return thresh

def extract_text(image: np.ndarray) -> str:
    try:
        processed_img = preprocess_image(image)
        text = pytesseract.image_to_string(processed_img, lang=config.OCR_LANGUAGE, config=r'--oem 3 --psm 6')
        return text.strip()
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        return ""