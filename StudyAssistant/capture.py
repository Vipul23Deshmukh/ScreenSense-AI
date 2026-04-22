"""
capture.py — Simplified screen capture and region selection.
"""

import tkinter as tk
import numpy as np
import mss
import cv2
import ctypes
from typing import Optional, Tuple
import config

logger = config.setup_logger("capture")

try:
    # Make Tkinter DPI aware for consistent coordinates
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class CaptureRegionBox:
    """A semi-transparent, draggable/resizable window to define the capture area."""
    def __init__(self, root=None, initial_region=None, on_change=None):
        self.root = tk.Toplevel(root) if root else tk.Tk()
        self.root.title("Capture Region")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.5)
        
        self.bg_color = "#000001"
        self.border_color = "#2ecc71"
        
        self.on_change = on_change
        self.dragging = False
        self.resizing = False
        
        x, y, w, h = initial_region or config.CAPTURE_REGION
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        self.canvas = tk.Canvas(self.root, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self._bind_events()
        self._update_canvas()
        self.hide() # Hidden by default

    def _update_canvas(self):
        self.canvas.delete("all")
        w, h = self.root.winfo_width(), self.root.winfo_height()
        self.canvas.create_rectangle(2, 2, w-2, h-2, outline=self.border_color, width=2)
        self.canvas.create_text(10, 15, text=f"REGION: {w}x{h}", fill=self.border_color, anchor="w")

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._initial_x = self.root.winfo_x()
        self._initial_y = self.root.winfo_y()
        self._initial_w = self.root.winfo_width()
        self._initial_h = self.root.winfo_height()
        
        # Simple resize if clicking bottom-right corner
        if event.x > self._initial_w - 20 and event.y > self._initial_h - 20:
            self.resizing = True
        else:
            self.dragging = True

    def _on_motion(self, event):
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        
        if self.dragging:
            self.root.geometry(f"+{self._initial_x + dx}+{self._initial_y + dy}")
        elif self.resizing:
            w = max(100, self._initial_w + dx)
            h = max(100, self._initial_h + dy)
            self.root.geometry(f"{w}x{h}")
            
        self._update_canvas()
        if self.on_change:
            self.on_change(self.get_region())

    def _on_release(self, event):
        self.dragging = False
        self.resizing = False

    def get_region(self):
        return (self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height())

    def show(self):
        self.root.deiconify()
        self._update_canvas()

    def hide(self):
        self.root.withdraw()

class ScreenCapture:
    """Minimal mss-based screen capture."""
    def grab(self, region: Tuple[int, int, int, int]) -> np.ndarray:
        """Capture region (x, y, w, h) and return BGR NumPy array."""
        try:
            with mss.mss() as sct:
                monitor = {"left": region[0], "top": region[1], "width": region[2], "height": region[3]}
                sct_img = sct.grab(monitor)
                img = np.array(sct_img)
                # Convert BGRA to BGR
                return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            logger.error(f"Capture failed: {e}")
            raise e

    def close(self):
        pass # No persistent resources to close anymore