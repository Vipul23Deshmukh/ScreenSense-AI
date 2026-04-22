import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
import config

class AssistantUI:
    def __init__(self, scan_callback, stop_callback, region_callback, test_callback=None):
        self.root = tk.Tk()
        self.root.title("Study AI")
        self.root.geometry("420x780")
        self.root.configure(bg="#0d0d1a")
        self.root.attributes("-topmost", True)
        
        # Make it draggable by background or header
        self.root.bind("<ButtonPress-1>", self._on_drag_start)
        self.root.bind("<B1-Motion>", self._on_drag_motion)
        
        self.scan_callback = scan_callback
        self.stop_callback = stop_callback
        self.region_callback = region_callback
        self.test_callback = test_callback
        
        self._build_ui()

    def _build_ui(self):
        # --- Top Controls ---
        top_bar = tk.Frame(self.root, bg="#16162a", padx=15, pady=10)
        top_bar.pack(fill="x")
        
        tk.Label(top_bar, text="Study AI", fg="#ffffff", bg="#16162a", font=("Segoe UI", 12, "bold")).pack(side="left")
        
        self.ai_dot = tk.Label(top_bar, text="●", fg="#6c7086", bg="#16162a", font=("Segoe UI", 12))
        self.ai_dot.pack(side="right", padx=5)
        
        # --- Buttons ---
        btn_frame = tk.Frame(self.root, bg="#0d0d1a", padx=20, pady=15)
        btn_frame.pack(fill="x")
        
        scan_stop_frame = tk.Frame(btn_frame, bg="#0d0d1a")
        scan_stop_frame.pack(fill="x", pady=(0, 10))
        
        self.scan_btn = tk.Button(
            scan_stop_frame, text="START SCAN", command=self.scan_callback,
            bg="#2ecc71", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", pady=8, activebackground="#27ae60"
        )
        self.scan_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.stop_btn = tk.Button(
            scan_stop_frame, text="STOP", command=self.stop_callback,
            bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", pady=8, activebackground="#c0392b"
        )
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        self.region_btn = tk.Button(
            btn_frame, text="SELECT REGION", command=self.region_callback,
            bg="#16162a", fg="#ffffff", font=("Segoe UI", 9),
            relief="flat", pady=5, activebackground="#21213d"
        )
        self.region_btn.pack(fill="x", pady=(0, 10))
        
        self.test_btn = tk.Button(
            btn_frame, text="TEST AI (2+2)", command=self.test_callback,
            bg="#16162a", fg="#6c7086", font=("Segoe UI", 8),
            relief="flat", pady=3, activebackground="#21213d"
        )
        self.test_btn.pack(fill="x")

        # --- Status Indicator ---
        self.status_frame = tk.Frame(self.root, bg="#0d0d1a", padx=20)
        self.status_frame.pack(fill="x")
        self.status_label = tk.Label(self.status_frame, text="READY", fg="#6c7086", bg="#0d0d1a", font=("Segoe UI", 8, "bold"))
        self.status_label.pack(anchor="w")

        # --- OCR Text (Middle) ---
        tk.Label(self.root, text="EXTRACTED OCR TEXT", fg="#6c7086", bg="#0d0d1a", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        self.ocr_box = tk.Text(
            self.root, height=6, bg="#050510", fg="#ffffff",
            font=("Consolas", 10), padx=12, pady=10, relief="flat",
            borderwidth=0, insertbackground="white"
        )
        self.ocr_box.pack(fill="x", padx=20)

        # --- Answer Card (Bottom) ---
        tk.Label(self.root, text="AI RESPONSE", fg="#6c7086", bg="#0d0d1a", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        self.ans_card = tk.Frame(self.root, bg="#16162a", padx=15, pady=15)
        self.ans_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        header = tk.Frame(self.ans_card, bg="#16162a")
        header.pack(fill="x")
        
        self.ans_letter = tk.Label(header, text="?", fg="#00d2ff", bg="#16162a", font=("Segoe UI", 32, "bold"))
        self.ans_letter.pack(side="left", padx=(0, 10))
        
        self.ans_text = tk.Label(header, text="Waiting for scan...", fg="#ffffff", bg="#16162a", font=("Segoe UI", 10, "bold"), wraplength=250, justify="left")
        self.ans_text.pack(side="left", fill="x", expand=True)
        
        self.ans_exp = tk.Label(self.ans_card, text="", fg="#6c7086", bg="#16162a", font=("Segoe UI", 9, "italic"), wraplength=340, justify="left")
        self.ans_exp.pack(fill="x", pady=(10, 0))
        
        # --- Raw Response (Hidden/Optional) ---
        tk.Label(self.root, text="RAW AI RESPONSE", fg="#3a3a5a", bg="#0d0d1a", font=("Segoe UI", 7, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        self.raw_box = tk.Text(
            self.root, height=4, bg="#050510", fg="#4a4a6a",
            font=("Consolas", 8), padx=10, pady=5, relief="flat",
            borderwidth=0, state="disabled"
        )
        self.raw_box.pack(fill="x", padx=20)

    def _on_drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag_motion(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def update_status(self, text, color="#6c7086"):
        self.status_label.config(text=text.upper(), fg=color)
        if "ERROR" in text.upper() or "FAILED" in text.upper():
            self.ans_card.config(highlightbackground="#e74c3c", highlightthickness=1)
        else:
            self.ans_card.config(highlightthickness=0)

    def update_ai_status(self, connected):
        self.ai_dot.config(fg="#2ecc71" if connected else "#e74c3c")

    def update_ocr(self, text):
        self.ocr_box.delete("1.0", tk.END)
        self.ocr_box.insert(tk.END, text)
        self.ocr_box.see(tk.END)

    def update_answer(self, letter, text, explanation=""):
        self.ans_letter.config(text=letter, fg="#00d2ff" if letter != "!" else "#e74c3c")
        self.ans_text.config(text=text)
        self.ans_exp.config(text=explanation)

    def update_raw_data(self, data):
        self.raw_box.config(state="normal")
        self.raw_box.delete("1.0", tk.END)
        self.raw_box.insert(tk.END, str(data))
        self.raw_box.config(state="disabled")
        self.raw_box.see(tk.END)

    def run(self):
        self.root.mainloop()
