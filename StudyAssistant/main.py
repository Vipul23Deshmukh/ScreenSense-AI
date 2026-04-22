import threading
import queue
import time
import keyboard
import config
from capture import ScreenCapture, CaptureRegionBox
from ocr import extract_text
from parser import parse_mcq
from answer_engine import get_answer, check_connection
from dashboard import AssistantUI

logger = config.setup_logger("main")

class StudyAssistantCore:
    def __init__(self):
        # Control flags
        self.stop_event = threading.Event()
        
        # UI Components
        self.ui = AssistantUI(
            scan_callback=self.trigger_scan,
            stop_callback=self.stop_scan,
            region_callback=self.toggle_region_box,
            test_callback=self.test_ai
        )
        self.region_box = CaptureRegionBox(root=self.ui.root, on_change=self.on_region_change)
        
        # Logic Components
        self.capture = ScreenCapture()
        self.ui_queue = queue.Queue()
        self.current_region = config.CAPTURE_REGION
        
        self.setup_hotkeys()
        self.process_ui_queue()
        self.check_ai_status()

    def setup_hotkeys(self):
        keyboard.add_hotkey(config.HOTKEY_SCAN, self.trigger_scan)
        keyboard.add_hotkey(config.HOTKEY_EXIT, self.exit_app)

    def on_region_change(self, region):
        self.current_region = region

    def toggle_region_box(self):
        if self.region_box.root.winfo_viewable():
            self.region_box.hide()
        else:
            self.region_box.show()

    def check_ai_status(self):
        def check():
            connected = check_connection()
            self.ui_queue.put(lambda c=connected: self.ui.update_ai_status(c))
        threading.Thread(target=check, daemon=True).start()
        self.ui.root.after(10000, self.check_ai_status)

    def test_ai(self):
        logger.info("AI Test triggered.")
        self.stop_event.clear()
        threading.Thread(target=self.run_ai_task, args=("What is 2+2?", []), daemon=True).start()

    def trigger_scan(self):
        self.stop_event.clear()
        threading.Thread(target=self.run_full_scan, daemon=True).start()

    def stop_scan(self):
        logger.info("Stop requested.")
        self.stop_event.set()
        self.ui_queue.put(lambda: self.ui.update_status("Stopped", "#e74c3c"))
        self.ui_queue.put(lambda: self.ui.update_answer("!", "User Aborted", "Scan was manually stopped."))

    def run_full_scan(self):
        try:
            self.ui_queue.put(lambda: self.ui.update_status("Capturing Screen...", "#00d2ff"))
            if self.stop_event.is_set(): return
            
            # 1. Capture
            frame = self.capture.grab(self.current_region)
            if self.stop_event.is_set(): return
            
            # 2. OCR
            self.ui_queue.put(lambda: self.ui.update_status("OCR Running...", "#f1c40f"))
            raw_text = extract_text(frame)
            if self.stop_event.is_set(): return
            
            # DISPLAY OCR IMMEDIATELY
            self.ui_queue.put(lambda t=raw_text: self.ui.update_ocr(t))
            
            if not raw_text or len(raw_text.strip()) < 2:
                self.ui_queue.put(lambda: self.ui.update_status("No text detected", "#e74c3c"))
                self.ui_queue.put(lambda: self.ui.update_answer("!", "OCR Empty", "Check processed_debug.png to see what OCR saw."))
                return
            
            self.ui_queue.put(lambda: self.ui.update_status("OCR Complete", "#2ecc71"))
            if self.stop_event.is_set(): return
            
            # 3. Parse
            parsed = parse_mcq(raw_text)
            q = parsed["question"] if parsed else raw_text
            opts = parsed["options"] if parsed else []
            
            # 4. AI
            cleaned_input = f"Q: {q}\nOpts: {opts}"
            logger.info(f"Sending to AI: {cleaned_input}")
            self.ui_queue.put(lambda: self.ui.update_status("Sending to AI...", "#00d2ff"))
            
            if not self.stop_event.is_set():
                self.run_ai_task(q, opts)
            
        except Exception as e:
            if self.stop_event.is_set(): return
            err_msg = str(e)
            self.ui_queue.put(lambda m=err_msg: self.ui.update_answer("!", "System Error", m))
            self.ui_queue.put(lambda: self.ui.update_status("Fatal Error", "#e74c3c"))

    def run_ai_task(self, question, options):
        try:
            self.ui_queue.put(lambda: self.ui.update_status("AI Generating Answer...", "#00d2ff"))
            self.ui_queue.put(lambda: self.ui.update_answer("...", "Thinking...", "Waiting for AI response..."))
            
            if self.stop_event.is_set(): return
            
            start_time = time.time()
            # Note: get_answer is a blocking network call. 
            # It will finish but we won't show the result if stopped.
            answer = get_answer(question, options)
            duration = time.time() - start_time
            
            if self.stop_event.is_set(): return
            
            # Update RAW DATA
            self.ui_queue.put(lambda a=answer: self.ui.update_raw_data(a))
            
            if answer and "error" not in answer:
                self.ui_queue.put(lambda a=answer: self.ui.update_answer(
                    a.get("letter", "?"), 
                    a.get("text", "Result"), 
                    a.get("explanation", f"Duration: {duration:.1f}s")
                ))
                self.ui_queue.put(lambda: self.ui.update_status("Answer Ready", "#2ecc71"))
            else:
                err = answer.get("error", "AI generation failed") if answer else "No response from AI"
                if "timed out" in err.lower() or "timeout" in err.lower():
                    err = "AI response took too long. Please try again or use a smaller region."
                
                connected = check_connection()
                conn_msg = "AI Server reachable" if connected else "AI Server UNREACHABLE"
                full_err = f"{err}\n\nStatus: {conn_msg}\nTime: {duration:.1f}s"
                
                self.ui_queue.put(lambda e=full_err: self.ui.update_answer("!", "AI TIMEOUT", e))
                self.ui_queue.put(lambda: self.ui.update_status("AI Timeout", "#e74c3c"))

            time.sleep(3)
            if not self.stop_event.is_set():
                self.ui_queue.put(lambda: self.ui.update_status("Ready", "#6c7086"))
            
        except Exception as e:
            if self.stop_event.is_set(): return
            err_msg = f"Task Error: {str(e)}"
            self.ui_queue.put(lambda m=err_msg: self.ui.update_answer("!", "AI Execution Error", m))
            self.ui_queue.put(lambda: self.ui.update_status("AI Crash", "#e74c3c"))

    def process_ui_queue(self):
        try:
            while True:
                task = self.ui_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        finally:
            self.ui.root.after(100, self.process_ui_queue)

    def exit_app(self):
        self.capture.close()
        self.ui.root.quit()

    def start(self):
        self.ui.run()

if __name__ == "__main__":
    app = StudyAssistantCore()
    app.start()