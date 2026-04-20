import cv2
import numpy as np
from ocr import extract_text, preprocess_image

def create_test_image(filename="test_ocr_input.png"):
    """
    Creates a sample image with MCQ text and noise to test OCR extraction and preprocessing.
    """
    # Create a white canvas
    img = np.ones((300, 700, 3), dtype=np.uint8) * 255
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Add text to the image
    cv2.putText(img, '1. What is the capital of France?', (20, 50), font, 1.2, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, 'A) London', (40, 110), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, 'B) Berlin', (40, 160), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, 'C) Paris', (40, 210), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, 'D) Madrid', (40, 260), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    
    # Add some light random noise to simulate a screen capture or compressed image
    noise = np.random.randint(0, 30, (300, 700, 3), dtype=np.uint8)
    img = cv2.subtract(img, noise)
    
    # Save the original test image
    cv2.imwrite(filename, img)
    return filename, img

if __name__ == "__main__":
    print("1. Creating test image...")
    filename, original_img = create_test_image()
    print(f"   Saved test image to '{filename}'.")
    
    print("\n2. Testing Image Preprocessing...")
    processed_img = preprocess_image(original_img)
    cv2.imwrite("test_ocr_processed.png", processed_img)
    print("   Saved preprocessed image to 'test_ocr_processed.png'.")
    
    print("\n3. Running OCR extraction...")
    extracted_text = extract_text(original_img)
    
    print("\n" + "="*40)
    print("EXTRACTED TEXT RESULTS:")
    print("="*40)
    if extracted_text:
        print(extracted_text)
    else:
        print("[No text found or Tesseract is not installed/configured properly]")
    print("="*40)
