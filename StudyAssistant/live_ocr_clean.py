import mss
import numpy as np
import cv2
import pytesseract
import time

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

REGION = {
    "left": 320,
    "top": 180,
    "width": 960,
    "height": 500
}

last_text = ""
last_time = 0

with mss.mss() as sct:
    print("Live OCR running... Press ESC to exit")

    while True:
        screenshot = sct.grab(REGION)
        frame = np.array(screenshot)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2)

        _, thresh = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)

        text = pytesseract.image_to_string(thresh, config="--psm 6").strip()

        current_time = time.time()

        # 🔥 ONLY PRINT WHEN TEXT CHANGES (NO SPAM)
        if text and text != last_text and (current_time - last_time > 2):
            print("\n📖 Detected Question:\n")
            print(text)
            last_text = text
            last_time = current_time

        # 🔹 Show stable window
        cv2.imshow("Study Assistant - Reading Area", frame)

        if cv2.waitKey(1) == 27:
            break

cv2.destroyAllWindows()