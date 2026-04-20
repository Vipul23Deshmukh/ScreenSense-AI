import time
import threading
import numpy as np
import mss
import cv2
import logging
from typing import Optional

from config import POLL_INTERVAL, CAPTURE_REGION, OVERLAY_DURATION_MS, ANSWER_COOLDOWN
from change_detector import ChangeDetector
from ocr import extract_text
from parser import parse_mcq
from answer_engine import get_answer
from overlay import StudyOverlay

# Set up logging for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("main")

class StudyAssistantCore:
    def __init__(self):
        self.detector = ChangeDetector()
        self.overlay = StudyOverlay()
        self.is_running = True
        
        self.last_parsed_question = ""
        self.last_answer_time = 0.0

    def get_monitor_dict(self, sct):
        """Parses the config CAPTURE_REGION into a dictionary for mss."""
        if CAPTURE_REGION:
            return {
                "left": CAPTURE_REGION[0],
                "top": CAPTURE_REGION[1],
                "width": CAPTURE_REGION[2],
                "height": CAPTURE_REGION[3]
            }
        # Default to primary monitor if not specified
        return sct.monitors[1]

    def capture_screen(self, sct) -> Optional[np.ndarray]:
        """Captures the target screen region and returns a BGR numpy array."""
        try:
            monitor = self.get_monitor_dict(sct)
            sct_img = sct.grab(monitor)
            
            # Convert mss image (BGRA) to standard OpenCV format (BGR)
            img = np.array(sct_img)
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None

    def processing_loop(self):
        """Background thread loop to continuously monitor the screen without freezing the UI."""
        logger.info("Starting background screen monitoring loop...")
        
        with mss.mss() as sct:
            while self.is_running:
                # 1. Loop with Delay
                time.sleep(POLL_INTERVAL)
                
                # 2. Capture Screen
                frame = self.capture_screen(sct)
                if frame is None:
                    continue
                    
                # 3. Detect Changes
                if not self.detector.has_changed(frame):
                    continue
                    
                logger.debug("Screen change detected. Running OCR...")
                
                # Enforce Answer Cooldown
                if time.time() - self.last_answer_time < ANSWER_COOLDOWN:
                    logger.debug("In cooldown period. Skipping AI check.")
                    continue

                # 4. Extract Text
                raw_text = extract_text(frame)
                if not raw_text:
                    continue
                    
                # 5. Parse MCQ
                parsed = parse_mcq(raw_text)
                if not parsed:
                    continue
                    
                question = parsed["question"]
                options = parsed["options"]
                
                # 6. Avoid duplicate processing
                if question == self.last_parsed_question:
                    logger.debug("Duplicate question detected on screen. Skipping.")
                    continue
                    
                logger.info(f"New MCQ Detected! Question: '{question}'")
                self.last_parsed_question = question
                
                # Notify user that AI is working (needs to be safely scheduled to UI thread if strictly required, but config allows direct calls mostly)
                self.overlay.set_status("Analyzing...")
                
                # 7. Get Answer from AI
                answer = get_answer(question, options)
                logger.info(f"AI Selected Answer: {answer}")
                self.last_answer_time = time.time()
                
                # 8. Display Overlay
                self.overlay.display_answer(answer)
                
                # Schedule the overlay to hide automatically after OVERLAY_DURATION_MS
                self.overlay.root.after(OVERLAY_DURATION_MS, self.overlay.hide)

    def start(self):
        """Starts the background processing thread and blocks on the Tkinter UI loop."""
        # Daemon thread closes automatically when the main UI thread exits
        thread = threading.Thread(target=self.processing_loop, daemon=True)
        thread.start()
        
        logger.info("AI Study Assistant is initialized and listening!")
        self.overlay.hide() # Keep hidden until the first question is found
        
        try:
            # Block the main thread with the UI loop
            self.overlay.run()
        finally:
            # When the user closes the overlay, shut down the background loop gracefully
            self.is_running = False
            logger.info("Study Assistant shutting down.")

if __name__ == "__main__":
    app = StudyAssistantCore()
    app.start()