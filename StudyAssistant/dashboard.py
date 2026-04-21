import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
import cv2
from datetime import datetime

class ModernButton(tk.Canvas):
    """A custom-styled rounded button using Tkinter Canvas."""
    def __init__(self, parent, text, command=None, width=150, height=45, bg="#0d0d1a", fg="#ffffff", active_bg="#7289da", corner_radius=10, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.command = command
        self.width = width
        self.height = height
        self.bg = bg
        self.fg = fg
        self.active_bg = active_bg
        self.corner_radius = corner_radius
        self.text = text
        
        self.rect = self._draw_rounded_rect(2, 2, width-2, height-2, corner_radius, fill=active_bg)
        self.label = self.create_text(width/2, height/2, text=text, fill=fg, font=("Segoe UI", 11, "bold"))
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [x1+radius, y1,
                  x1+radius, y1,
                  x2-radius, y1,
                  x2-radius, y1,
                  x2, y1,
                  x2, y1+radius,
                  x2, y1+radius,
                  x2, y2-radius,
                  x2, y2-radius,
                  x2, y2,
                  x2-radius, y2,
                  x2-radius, y2,
                  x1+radius, y2,
                  x1+radius, y2,
                  x1, y2,
                  x1, y2-radius,
                  x1, y2-radius,
                  x1, y1+radius,
                  x1, y1+radius,
                  x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_click(self, event):
        if self.command:
            self.command()

    def _on_enter(self, event):
        self.itemconfig(self.rect, fill="#8e9fef")

    def _on_leave(self, event):
        self.itemconfig(self.rect, fill=self.active_bg)
        
    def configure_button(self, text=None, bg=None):
        if text:
            self.itemconfig(self.label, text=text)
        if bg:
            self.active_bg = bg
            self.itemconfig(self.rect, fill=bg)

class StudyAssistantDashboard:
    def __init__(self, toggle_callback=None, region_callback=None, scan_callback=None):
        self.root = tk.Tk()
        self.root.title("Study Assistant")
        self.root.geometry("450x850") # Increased size for log area
        self.root.configure(bg="#0d0d1a")
        
        # Window properties
        self.root.resizable(False, False)
        
        # State
        self.is_running = False
        self.toggle_callback = toggle_callback
        self.region_callback = region_callback
        self.scan_callback = scan_callback
        
        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        self.title_font = tkfont.Font(family="Segoe UI", size=22, weight="bold")
        self.status_font = tkfont.Font(family="Segoe UI", size=10)
        self.status_val_font = tkfont.Font(family="Segoe UI", size=14, weight="bold")

    def _build_ui(self):
        # Main Container
        self.main_frame = tk.Frame(self.root, bg="#0d0d1a", padx=40, pady=40)
        self.main_frame.pack(expand=True, fill="both")
        
        # Title
        self.title_label = tk.Label(
            self.main_frame, 
            text="Study Assistant", 
            fg="#ffffff", 
            bg="#0d0d1a",
            font=self.title_font
        )
        self.title_label.pack(pady=(0, 25))
        
        # Status Card
        self.status_card = tk.Frame(self.main_frame, bg="#16162a", padx=25, pady=20)
        self.status_card.pack(fill="x", pady=10)
        
        self.status_label = tk.Label(
            self.status_card, 
            text="SYSTEM STATUS", 
            fg="#6c7086", 
            bg="#16162a",
            font=self.status_font
        )
        self.status_label.pack(anchor="w")
        
        self.status_value = tk.Label(
            self.status_card, 
            text="IDLE", 
            fg="#00d2ff", 
            bg="#16162a",
            font=self.status_val_font
        )
        self.status_value.pack(anchor="w", pady=(5, 0))
        
        # Control Section
        self.control_frame = tk.Frame(self.main_frame, bg="#0d0d1a")
        self.control_frame.pack(pady=35)
        
        self.toggle_btn = ModernButton(
            self.control_frame, 
            text="START MONITORING", 
            command=self.toggle_engine,
            active_bg="#2ecc71",
            width=220
        )
        self.toggle_btn.pack(pady=10)
        
        self.region_btn = ModernButton(
            self.control_frame, 
            text="ADJUST REGION", 
            command=self.show_region_box,
            active_bg="#7289da",
            width=220
        )
        self.region_btn.pack(pady=10)
        
        self.scan_btn = ModernButton(
            self.control_frame, 
            text="SCAN NOW", 
            command=self.trigger_scan,
            active_bg="#f1c40f", # Yellow
            width=220
        )
        self.scan_btn.pack(pady=10)
        
        # Preview Section
        self.preview_container = tk.Frame(self.main_frame, bg="#16162a", padx=5, pady=5)
        self.preview_container.pack(fill="x", pady=(10, 0))
        
        self.preview_label = tk.Label(
            self.preview_container, 
            text="PREVIEW WILL APPEAR HERE", 
            fg="#6c7086", 
            bg="#16162a",
            font=("Segoe UI", 9, "italic")
        )
        self.preview_label.pack(expand=True, fill="both")
        
        # OCR Results Title
        self.ocr_label = tk.Label(
            self.main_frame, 
            text="DETECTED TEXT", 
            fg="#6c7086", 
            bg="#0d0d1a",
            font=self.status_font
        )
        self.ocr_label.pack(anchor="w", pady=(20, 5))
        
        # Scrollable OCR Text Box
        self.text_frame = tk.Frame(self.main_frame, bg="#16162a", padx=2, pady=2)
        self.text_frame.pack(fill="both", expand=True)
        
        self.ocr_text = tk.Text(
            self.text_frame,
            height=8,
            bg="#16162a",
            fg="#ffffff",
            insertbackground="#ffffff", # Cursor color
            relief="flat",
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        self.ocr_text.pack(side="left", fill="both", expand=True)
        
        # Scrollbar for the text box
        self.scrollbar = tk.Scrollbar(self.text_frame, command=self.ocr_text.yview, bg="#16162a", troughcolor="#0d0d1a")
        self.scrollbar.pack(side="right", fill="y")
        self.ocr_text.config(yscrollcommand=self.scrollbar.set)
        
        # System Logs Section
        self.log_label = tk.Label(
            self.main_frame, 
            text="SYSTEM LOGS", 
            fg="#6c7086", 
            bg="#0d0d1a",
            font=self.status_font
        )
        self.log_label.pack(anchor="w", pady=(20, 5))
        
        self.log_frame = tk.Frame(self.main_frame, bg="#0b0b14", padx=2, pady=2)
        self.log_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(
            self.log_frame,
            height=6,
            bg="#0b0b14",
            fg="#a9b1d6",
            relief="flat",
            font=("Consolas", 9),
            padx=10,
            pady=10,
            state="disabled"
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        
        self.log_scrollbar = tk.Scrollbar(self.log_frame, command=self.log_text.yview, bg="#0b0b14")
        self.log_scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)
        
        # Log Tags for Colors
        self.log_text.tag_configure("INFO", foreground="#a9b1d6")
        self.log_text.tag_configure("SUCCESS", foreground="#2ecc71")
        self.log_text.tag_configure("ERROR", foreground="#e74c3c")
        self.log_text.tag_configure("WARNING", foreground="#f1c40f")
        self.log_text.tag_configure("TIMESTAMP", foreground="#565f89")

    def toggle_engine(self):
        if self.toggle_callback:
            self.is_running = self.toggle_callback()
        else:
            self.is_running = not self.is_running
            
        if self.is_running:
            self.update_status("SCANNING", "#2ecc71")
            self.toggle_btn.configure_button(text="STOP MONITORING", bg="#e74c3c")
        else:
            self.update_status("IDLE", "#00d2ff")
            self.toggle_btn.configure_button(text="START MONITORING", bg="#2ecc71")

    def show_region_box(self):
        if self.region_callback:
            self.region_callback()

    def trigger_scan(self):
        if self.scan_callback:
            self.scan_callback()

    def update_ocr_results(self, text):
        self.ocr_text.delete("1.0", tk.END)
        self.ocr_text.insert(tk.END, text)
        self.ocr_text.see(tk.END)

    def update_preview(self, bgr_image):
        """Update the preview label with the latest capture."""
        if bgr_image is None:
            return
            
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_image)
            
            # Max dimensions for preview (fit within dashboard)
            max_w, max_h = 350, 180
            pil_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            
            # Update Tkinter Image
            self.tk_preview = ImageTk.PhotoImage(pil_img)
            self.preview_label.config(image=self.tk_preview, text="")
            
            # Force update
            self.preview_label.update_idletasks()
        except Exception as e:
            self.add_log(f"Preview error: {e}", "ERROR")

    def add_log(self, message, level="INFO"):
        """Add a timestamped message to the system logs."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "TIMESTAMP")
        self.log_text.insert(tk.END, f"{level}: ", level)
        self.log_text.insert(tk.END, f"{message}\n", "INFO")
        self.log_text.config(state="disabled")
        
        self.log_text.see(tk.END)

    def display_answer(self, result):
        """
        result: {"letter": "A", "text": "...", "explanation": "..."}
        """
        # Create or update Answer Card
        if not hasattr(self, 'answer_card'):
            self.answer_card = tk.Frame(self.main_frame, bg="#1a1a3a", padx=20, pady=15, bd=1, relief="ridge")
            self.answer_card.pack(fill="x", pady=(20, 0))
            
            self.ans_letter_label = tk.Label(self.answer_card, text="", fg="#A6E3A1", bg="#1a1a3a", font=("Segoe UI", 24, "bold"))
            self.ans_letter_label.pack(side="left", padx=(0, 15))
            
            self.ans_text_label = tk.Label(self.answer_card, text="", fg="#ffffff", bg="#1a1a3a", font=("Segoe UI", 12), wraplength=250, justify="left")
            self.ans_text_label.pack(side="left", fill="both", expand=True)
            
            self.exp_label = tk.Label(self.main_frame, text="EXPLANATION", fg="#6c7086", bg="#0d0d1a", font=self.status_font)
            self.exp_label.pack(anchor="w", pady=(15, 5))
            
            self.exp_text = tk.Label(self.main_frame, text="", fg="#CDD6F4", bg="#0d0d1a", font=("Segoe UI", 10, "italic"), wraplength=350, justify="left")
            self.exp_text.pack(anchor="w")

        self.ans_letter_label.config(text=result.get("letter", "?"))
        self.ans_text_label.config(text=result.get("text", "No option text provided."))
        self.exp_text.config(text=result.get("explanation", "No explanation available."))

    def update_status(self, text, color="#00d2ff"):
        """Update status with a clean, centered look."""
        self.status_value.config(text=text.upper(), fg=color)
        # Subtle flash effect
        orig_bg = self.status_card.cget("bg")
        self.status_card.config(bg="#21213d")
        self.root.after(100, lambda: self.status_card.config(bg=orig_bg))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = StudyAssistantDashboard()
    app.run()
