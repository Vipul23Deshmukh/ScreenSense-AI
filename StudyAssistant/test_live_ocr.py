import mss
import numpy as np
import cv2
import pytesseract

# SET THIS PATH (already done earlier)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 🔥 PUT YOUR REGION HERE
REGION = {
    "left": 320,
    "top": 180,
    "width": 960,
    "height": 500
}

with mss.mss() as sct:
    print("Live OCR started... Press ESC to stop")

    while True:
        screenshot = sct.grab(REGION)
        frame = np.array(screenshot)

        # Convert to grayscale (improves OCR)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply threshold (important for clarity)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # OCR
        text = pytesseract.image_to_string(thresh)

        print("\nDetected Text:\n", text[:200])  # print first 200 chars

        # Show region being captured
        cv2.imshow("OCR Region", frame)

        if cv2.waitKey(1) == 27:  # ESC
            break

cv2.destroyAllWindows()