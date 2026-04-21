import tkinter as tk
from PIL import Image, ImageTk
import cv2

class CapturePreview:
    def __init__(self, parent_root, bgr_image, duration_ms=2500):
        self.root = tk.Toplevel(parent_root)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.0) # Start invisible for fade-in if desired
        
        # Style
        self.root.configure(bg="#2ecc71") # Green border color
        
        # Process image (BGR to RGB and Resize)
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_image)
        
        # Max dimensions for preview
        max_w, max_h = 300, 200
        pil_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        
        self.tk_img = ImageTk.PhotoImage(pil_img)
        
        # UI Elements
        self.frame = tk.Frame(self.root, bg="#0d0d1a", bd=2)
        self.frame.pack(padx=2, pady=2)
        
        self.label = tk.Label(self.frame, image=self.tk_img, bg="#0d0d1a")
        self.label.pack()
        
        self.info_label = tk.Label(
            self.frame, 
            text="CAPTURE SAVED", 
            fg="#2ecc71", 
            bg="#0d0d1a",
            font=("Segoe UI", 8, "bold")
        )
        self.info_label.pack(pady=2)

        # Position (Bottom-Left above taskbar)
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        
        x = 20
        y = screen_h - h - 60
        self.root.geometry(f"+{x}+{y}")
        
        # Fade in and Auto-close
        self._fade_in()
        self.root.after(duration_ms, self._close)

    def _fade_in(self):
        alpha = self.root.attributes("-alpha")
        if alpha < 0.95:
            alpha += 0.1
            self.root.attributes("-alpha", alpha)
            self.root.after(20, self._fade_in)

    def _close(self):
        self._fade_out()

    def _fade_out(self):
        alpha = self.root.attributes("-alpha")
        if alpha > 0.05:
            alpha -= 0.1
            self.root.attributes("-alpha", alpha)
            self.root.after(20, self._fade_out)
        else:
            self.root.destroy()

def show_preview(parent, image):
    CapturePreview(parent, image)
