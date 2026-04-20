import time
import threading
import numpy as np
import mss
import cv2
import logging
from typing import Optional

from config import (
    POLL_INTERVAL, CAPTURE_REGION, OVERLAY_DURATION_MS, ANSWER_COOLDOWN, 
    STABILITY_DELAY, HOTKEY_TOGGLE, HOTKEY_EXIT, HOTKEY_HIDE, HOTKEY_REGION
)
from change_detector import ChangeDetector
from ocr import extract_text
from parser import parse_mcq
from answer_engine import get_answer
from overlay import StudyOverlay

# Set up logging for debugging
from utils import setup_logger
logger = setup_logger("main")

class StudyAssistantCore:
    def __init__(self):
        self.detector = ChangeDetector()
        self.overlay = StudyOverlay()
        self.is_running = True
        self.is_monitoring = True
        self.capture_region = CAPTURE_REGION
        
        self.last_parsed_question = ""
        self.last_answer_time = 0.0
        self.last_change_time = 0.0
        self.last_processed_time = 0.0
        
        self.setup_hotkeys()

    def setup_hotkeys(self):
        try:
            import keyboard
            keyboard.add_hotkey(HOTKEY_TOGGLE, self.toggle_monitoring)
            keyboard.add_hotkey(HOTKEY_EXIT, self.exit_app)
            keyboard.add_hotkey(HOTKEY_HIDE, self.toggle_overlay)
            keyboard.add_hotkey(HOTKEY_REGION, self.start_region_selection)
            logger.info(f"Hotkeys: Toggle({HOTKEY_TOGGLE}), Exit({HOTKEY_EXIT}), Hide({HOTKEY_HIDE}), Region({HOTKEY_REGION})")
        except ImportError:
            logger.warning("Keyboard module not found. Hotkeys disabled.")
        except Exception as e:
            logger.error(f"Failed to register hotkeys: {e}")

    def toggle_monitoring(self):
        self.is_monitoring = not self.is_monitoring
        status = "Resumed" if self.is_monitoring else "Paused"
        logger.info(f"Monitoring {status}")
        self.overlay.root.after(0, lambda: self.overlay.set_status(f"Monitoring {status}"))
        if not self.is_monitoring:
            self.overlay.root.after(2000, self.overlay.hide)

    def exit_app(self):
        logger.info("Exit hotkey pressed.")
        self.is_running = False
        self.overlay.root.after(0, self.overlay.root.quit)

    def toggle_overlay(self):
        self.overlay.root.after(0, self._safe_toggle_overlay)

    def _safe_toggle_overlay(self):
        if self.overlay.root.winfo_viewable():
            self.overlay.hide()
        else:
            self.overlay.show()

    def start_region_selection(self):
        logger.info("Region selection hotkey pressed.")
        self.overlay.root.after(0, self._run_region_selector)

    def _run_region_selector(self):
        from region_selector import select_region
        # Pause monitoring while selecting
        was_monitoring = self.is_monitoring
        self.is_monitoring = False
        self.overlay.hide()
        
        region = select_region()
        if region:
            self.capture_region = region
            logger.info(f"New capture region selected: {region}")
            self.overlay.set_status("Region updated!")
        else:
            logger.info("Region selection canceled.")
            self.overlay.set_status("Region unchanged")
            
        self.detector.reset() # Reset detector to avoid false positives
        self.overlay.root.after(2000, self.overlay.hide)
        self.is_monitoring = was_monitoring

    def get_monitor_dict(self, sct):
        """Parses the active capture_region into a dictionary for mss."""
        if self.capture_region:
            return {
                "left": self.capture_region[0],
                "top": self.capture_region[1],
                "width": self.capture_region[2],
                "height": self.capture_region[3]
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
                
                if not self.is_monitoring:
                    continue
                
                # 2. Capture Screen
                frame = self.capture_screen(sct)
                if frame is None:
                    continue
                    
                # 3. Detect Changes
                if self.detector.has_changed(frame):
                    self.last_change_time = time.time()
                    continue
                
                # Screen is stable.
                if time.time() - self.last_change_time < STABILITY_DELAY:
                    continue
                
                # Check if we already processed this stable frame
                if self.last_processed_time >= self.last_change_time and self.last_change_time > 0:
                    continue
                    
                self.last_processed_time = time.time()
                    
                logger.debug("Screen is stable. Running OCR...")
                
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
                
                # Notify user that AI is working
                self.overlay.root.after(0, lambda: self.overlay.set_status("Analyzing..."))
                
                # 7. Get Answer from AI (Async)
                self.fetch_answer_async(question, options)

    def fetch_answer_async(self, question, options):
        def worker():
            answer = get_answer(question, options)
            logger.info(f"AI Selected Answer: {answer}")
            self.last_answer_time = time.time()
            
            # Save history
            from utils import save_qa_history
            save_qa_history({
                "question": question,
                "options": options,
                "answer": {"letter": answer}
            })
            
            # 8. Display Overlay safely from main thread
            self.overlay.root.after(0, lambda: self.overlay.display_answer(answer))
            self.overlay.root.after(OVERLAY_DURATION_MS, self.overlay.hide)
            
        threading.Thread(target=worker, daemon=True).start()

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