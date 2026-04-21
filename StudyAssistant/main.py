
import time
import threading
import queue
import numpy as np
import mss
import cv2
import logging
import ctypes
from typing import Optional

from config import (
    POLL_INTERVAL, CAPTURE_REGION, OVERLAY_DURATION_MS, ANSWER_COOLDOWN, 
    STABILITY_DELAY, HOTKEY_TOGGLE, HOTKEY_EXIT, HOTKEY_HIDE, HOTKEY_REGION
)
from change_detector import ChangeDetector
from ocr import extract_text
from parser import parse_mcq
from answer_engine import get_answer, check_ollama_status
from overlay import StudyOverlay
from dashboard import StudyAssistantDashboard
from capture_box import CaptureRegionBox
from preview import show_preview

# Set up logging for debugging
from utils import setup_logger
logger = setup_logger("main")

class StudyAssistantCore:
    def __init__(self):
        # 1. Initialize Dashboard
        self.dashboard = StudyAssistantDashboard(
            toggle_callback=self.toggle_monitoring,
            region_callback=self.toggle_region_box,
            scan_callback=self.trigger_manual_scan
        )
        
        # 2. Initialize Overlay (as child of dashboard)
        self.overlay = StudyOverlay(root=self.dashboard.root)
        
        # 3. Initialize Capture Region Box
        self.region_box = CaptureRegionBox(
            initial_region=CAPTURE_REGION,
            on_change=self.update_capture_region
        )
        self.region_box.hide() # Hide by default
        
        self.detector = ChangeDetector()
        self.is_running = True
        self.is_monitoring = False # Start in Idle state
        self.capture_region = CAPTURE_REGION if CAPTURE_REGION else self.region_box.get_region()
        
        self.last_parsed_question = ""
        self.last_answer_time = 0.0
        self.last_change_time = 0.0
        self.last_processed_time = 0.0
        
        # 4. Thread-safe UI queue
        self.ui_queue = queue.Queue()
        
        self.setup_hotkeys()

    def queue_ui_task(self, task):
        """Push a UI update task (callable) into the thread-safe queue."""
        self.ui_queue.put(task)

    def process_ui_queue(self):
        """Process all pending UI tasks in the queue. Runs on the main thread."""
        try:
            while True:
                # Get all tasks currently in queue
                task = self.ui_queue.get_nowait()
                try:
                    if callable(task):
                        task()
                    elif isinstance(task, tuple):
                        # Handle structured messages for sensitive components (like region_box)
                        msg_type = task[0]
                        if msg_type == "set_border_color":
                            self.region_box.set_border_color(task[1])
                        elif msg_type == "set_border_color_delayed":
                            delay_ms, color = task[1], task[2]
                            # CRITICAL: Use the main dashboard root to schedule the delay
                            self.dashboard.root.after(delay_ms, lambda: self.region_box.set_border_color(color))
                except Exception as e:
                    logger.error(f"Error executing UI task: {e}")
        except queue.Empty:
            pass
        finally:
            # Check the queue again after a short delay
            if self.is_running:
                self.dashboard.root.after(50, self.process_ui_queue)

    def setup_hotkeys(self):
        try:
            import keyboard
            keyboard.add_hotkey(HOTKEY_TOGGLE, lambda: self.queue_ui_task(self.toggle_monitoring))
            keyboard.add_hotkey(HOTKEY_EXIT, lambda: self.queue_ui_task(self.exit_app))
            keyboard.add_hotkey(HOTKEY_HIDE, lambda: self.queue_ui_task(self.toggle_overlay))
            keyboard.add_hotkey(HOTKEY_REGION, lambda: self.queue_ui_task(self.start_region_selection))
            keyboard.add_hotkey("ctrl+shift+a", lambda: self.queue_ui_task(self.trigger_manual_scan))
            logger.info(f"Hotkeys: Toggle({HOTKEY_TOGGLE}), Exit({HOTKEY_EXIT}), Hide({HOTKEY_HIDE}), Region({HOTKEY_REGION}), Scan(ctrl+shift+a)")
        except ImportError:
            logger.warning("Keyboard module not found. Hotkeys disabled.")
        except Exception as e:
            logger.error(f"Failed to register hotkeys: {e}")

    def toggle_monitoring(self):
        self.is_monitoring = not self.is_monitoring
        status = "Resumed" if self.is_monitoring else "Paused"
        logger.info(f"Monitoring {status}")
        
        # Update UI
        if self.is_monitoring:
            self.dashboard.update_status("Scanning", "#2ecc71")
            self.dashboard.add_log("Monitoring Resumed", "SUCCESS")
        else:
            self.dashboard.update_status("Idle", "#00d2ff")
            self.dashboard.add_log("Monitoring Paused", "WARNING")
            
        self.overlay.root.after(0, lambda: self.overlay.set_status(f"Monitoring {status}"))
        if not self.is_monitoring:
            self.overlay.root.after(2000, self.overlay.hide)
            
        return self.is_monitoring

    def exit_app(self):
        logger.info("Exit app triggered.")
        self.is_running = False
        self.dashboard.root.quit()

    def toggle_overlay(self):
        self._safe_toggle_overlay()

    def _safe_toggle_overlay(self):
        if self.overlay.root.winfo_viewable():
            self.overlay.hide()
        else:
            self.overlay.show()

    def toggle_region_box(self):
        if self.region_box.root.winfo_viewable():
            self.region_box.hide()
        else:
            self.region_box.show()

    def update_capture_region(self, region):
        self.capture_region = region
        logger.debug(f"Capture region updated: {region}")

    def trigger_manual_scan(self):
        """Manually trigger a screen capture with visual feedback."""
        logger.info("Manual scan triggered.")
        
        def do_scan():
            # 1. Visual Feedback (Change color to yellow)
            self.ui_queue.put(("set_border_color", "#f1c40f"))
            
            # 2. Capture
            with mss.mss() as sct:
                frame = self.capture_screen(sct)
                if frame is not None:
                    # 1. Show Preview in Dashboard immediately
                    self.queue_ui_task(lambda: self.dashboard.update_preview(frame))
                    
                    # For now, just save a debug image to verify capture works
                    logger.info("Capture successful. Saved to debug.png")
                    
                    # 2. Run OCR
                    self.queue_ui_task(lambda: self.dashboard.update_status("Scanning", "#f1c40f"))
                    self.queue_ui_task(lambda: self.dashboard.add_log("Running OCR...", "INFO"))
                    raw_text = extract_text(frame)
                    
                    # 5. Update UI with results
                    if raw_text:
                        self.queue_ui_task(lambda: self.dashboard.add_log(f"OCR Success: {len(raw_text)} chars", "SUCCESS"))
                        self.queue_ui_task(lambda: self.dashboard.update_ocr_results(raw_text))
                        
                        # 6. Parse MCQ and Get Answer
                        parsed = parse_mcq(raw_text)
                        if parsed:
                            # Still "Scanning" or "Processing"
                            self.queue_ui_task(lambda: self.dashboard.update_status("Scanning...", "#7289da"))
                            
                            # Get Answer (runs in this background thread)
                            self.queue_ui_task(lambda: self.dashboard.add_log("Fetching AI answer...", "INFO"))
                            result = get_answer(parsed["question"], parsed["options"])
                            
                            if result and "error" not in result:
                                self.queue_ui_task(lambda: self.dashboard.add_log(f"Answer received: {result.get('letter')}", "SUCCESS"))
                                if "raw_response" in result:
                                    self.queue_ui_task(lambda: self.dashboard.add_log(f"Raw AI: {result['raw_response']}", "INFO"))
                                
                                # Display Answer in both UI components
                                self.queue_ui_task(lambda: self.overlay.display_answer(result))
                                self.queue_ui_task(lambda: self.dashboard.display_answer(result))
                                self.queue_ui_task(lambda: self.dashboard.update_status("Answer Ready", "#A6E3A1"))
                                self.ui_queue.put(("set_border_color", "#2ecc71"))
                            else:
                                err = result.get("error", "Unknown error") if result else "No response"
                                self.queue_ui_task(lambda: self.dashboard.add_log(f"AI Error: {err}", "ERROR"))
                                self.queue_ui_task(lambda: self.dashboard.update_status("Idle", "#00d2ff"))
                                self.queue_ui_task(lambda: self.overlay.display_error(err))
                                self.ui_queue.put(("set_border_color", "#e74c3c"))
                            
                            # Return to Idle after 10 seconds
                            self.queue_ui_task(lambda: self.dashboard.root.after(10000, lambda: self.dashboard.update_status("Idle", "#00d2ff")))
                        else:
                            self.queue_ui_task(lambda: self.dashboard.add_log("No valid MCQ structure (question + options) found.", "WARNING"))
                            self.queue_ui_task(lambda: self.dashboard.update_ocr_results(f"PARSING FAILED. RAW TEXT:\n\n{raw_text}"))
                            self.queue_ui_task(lambda: self.dashboard.update_status("Idle", "#00d2ff"))
                            self.ui_queue.put(("set_border_color", "#f1c40f")) # Stay yellow for warning?
                    else:
                        self.queue_ui_task(lambda: self.dashboard.add_log("OCR failed or no text found.", "WARNING"))
                        self.queue_ui_task(lambda: self.dashboard.update_ocr_results("No text detected."))
                        self.queue_ui_task(lambda: self.dashboard.update_status("Idle", "#00d2ff"))
                        self.ui_queue.put(("set_border_color", "#e74c3c"))
            
            # Reset color after 2 seconds instead of 500ms
            self.ui_queue.put(("set_border_color_delayed", 2000, "#2ecc71"))
            
        # Run in a thread to avoid freezing the UI
        threading.Thread(target=do_scan, daemon=True).start()

    def start_region_selection(self):
        logger.info("Region selection triggered.")
        self._run_region_selector()

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
            logger.debug(f"Capturing region: {monitor}")
            
            sct_img = sct.grab(monitor)
            
            # Convert mss image (BGRA) to standard OpenCV format (BGR)
            img = np.array(sct_img)
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # 1. Debug: Save captured image as requested
            cv2.imwrite("debug.png", img)
            
            # 2. Check for blank/black image (average pixel value)
            if np.mean(img) < 2.0:
                logger.warning("Captured image is almost entirely black!")
                self.queue_ui_task(lambda: self.dashboard.add_log("Capture: Image is black/blank!", "ERROR"))
            
            # Log success for manual scans
            if threading.current_thread() != threading.main_thread():
                self.queue_ui_task(lambda: self.dashboard.add_log(f"Capture Success: {img.shape[1]}x{img.shape[0]}", "SUCCESS"))
            return img
        except Exception as e:
            self.queue_ui_task(lambda: self.dashboard.add_log(f"Capture Error: {e}", "ERROR"))
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
                
                # Always update preview in dashboard for visual confirmation
                self.queue_ui_task(lambda: self.dashboard.update_preview(frame))
                    
                logger.debug("Screen is stable. Running OCR...")
                self.ui_queue.put(("set_border_color", "#f1c40f")) # Flash yellow
                self.ui_queue.put(("set_border_color_delayed", 1000, "#2ecc71"))
                
                # Enforce Answer Cooldown
                if time.time() - self.last_answer_time < ANSWER_COOLDOWN:
                    logger.debug("In cooldown period. Skipping AI check.")
                    continue

                # 4. Extract Text
                raw_text = extract_text(frame)
                if not raw_text:
                    self.queue_ui_task(lambda: self.dashboard.add_log("Auto-scan: No text detected.", "INFO"))
                    self.queue_ui_task(lambda: self.dashboard.update_ocr_results("No text detected."))
                    continue
                    
                # 5. Parse MCQ
                raw_text_content = raw_text # Local copy for lambda
                parsed = parse_mcq(raw_text)
                if not parsed:
                    self.queue_ui_task(lambda: self.dashboard.add_log("Auto-scan: No valid MCQ found.", "INFO"))
                    self.queue_ui_task(lambda: self.dashboard.update_ocr_results(f"PARSING FAILED. RAW TEXT:\n\n{raw_text_content}"))
                    continue
                    
                question = parsed["question"]
                options = parsed["options"]
                
                # 6. Avoid duplicate processing
                if question == self.last_parsed_question:
                    continue
                    
                self.queue_ui_task(lambda: self.dashboard.add_log(f"Auto-scan: New MCQ detected!", "SUCCESS"))
                self.queue_ui_task(lambda: self.dashboard.update_ocr_results(raw_text_content))
                
                logger.info(f"New MCQ Detected! Question: '{question}'")
                self.last_parsed_question = question
                
                # Notify user that AI is working
                self.queue_ui_task(lambda: self.overlay.set_status("Analyzing..."))
                
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
            
            # 8. Display Answer safely in both UI components
            self.queue_ui_task(lambda: self.overlay.display_answer(answer))
            self.queue_ui_task(lambda: self.dashboard.display_answer(answer))
            self.queue_ui_task(lambda: self.overlay.root.after(OVERLAY_DURATION_MS, self.overlay.hide))
            
        threading.Thread(target=worker, daemon=True).start()

    def start(self):
        """Starts the background processing thread and blocks on the Tkinter UI loop."""
        # 1. Start UI Queue Processor
        self.dashboard.root.after(50, self.process_ui_queue)
        
        # 2. Start Background Monitor (Daemon thread closes automatically)
        thread = threading.Thread(target=self.processing_loop, daemon=True)
        thread.start()
        
        logger.info("AI Study Assistant is initialized and listening!")
        self.overlay.hide() # Keep hidden until the first question is found
        
        try:
            # Block the main thread with the Dashboard UI loop
            self.dashboard.run()
        finally:
            # When the user closes the overlay, shut down the background loop gracefully
            self.is_running = False
            logger.info("Study Assistant shutting down.")

if __name__ == "__main__":
    try:
        # Make process DPI aware for consistent screen coordinates
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    app = StudyAssistantCore()
    
    # Check Ollama status on startup if configured
    from config import AI_PLUGIN
    if AI_PLUGIN.lower() == "ollama":
        if check_ollama_status():
            app.dashboard.add_log("Ollama server connected", "SUCCESS")
        else:
            app.dashboard.add_log("Ollama server NOT found. Ensure it is running.", "ERROR")
            
    app.start()