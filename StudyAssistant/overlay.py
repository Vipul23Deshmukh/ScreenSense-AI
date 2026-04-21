import tkinter as tk
from config import OVERLAY_WIDTH, OVERLAY_HEIGHT, OVERLAY_POSITION

class StudyOverlay:
    def __init__(self, root=None):
        if root:
            self.root = tk.Toplevel(root)
        else:
            self.root = tk.Tk()
        self.root.title("Study Assistant Overlay")
        
        # 1. Always-on-top window
        self.root.attributes("-topmost", True)
        
        # 2. Transparent background (Alpha transparency)
        self.root.attributes("-alpha", 0.90)
        
        # Remove standard OS window borders for a clean look
        self.root.overrideredirect(True)
        
        # Minimal and clean modern color palette
        self.bg_color = "#1E1E2E"       # Deep dark blue/gray
        self.text_color = "#A6E3A1"     # Vibrant pastel green
        self.header_color = "#CDD6F4"   # Light text
        
        self.root.configure(bg=self.bg_color)
        
        # Calculate Position (Bottom-Right Corner)
        self.root.update_idletasks() # Ensure accurate screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 20px padding from the right, 60px padding from the bottom (taskbar clearance)
        x = screen_width - OVERLAY_WIDTH - 20
        y = screen_height - OVERLAY_HEIGHT - 60
        
        self.root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+{x}+{y}")
        
        # Dragging State
        self._drag_data = {"x": 0, "y": 0}
        
        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        """Creates a minimal and clean UI layout for structured answers."""
        # Main container
        self.frame = tk.Frame(self.root, bg=self.bg_color, bd=0, relief="flat")
        self.frame.pack(expand=True, fill="both", padx=20, pady=15)
        
        # Top row: Letter and Option Text
        self.top_row = tk.Frame(self.frame, bg=self.bg_color)
        self.top_row.pack(fill="x", anchor="w")
        
        self.letter_label = tk.Label(
            self.top_row,
            text="?",
            font=("Segoe UI", 32, "bold"),
            fg=self.text_color,
            bg=self.bg_color
        )
        self.letter_label.pack(side="left", padx=(0, 15))
        
        self.option_label = tk.Label(
            self.top_row,
            text="Waiting for scan...",
            font=("Segoe UI", 12, "bold"),
            fg=self.header_color,
            bg=self.bg_color,
            wraplength=350,
            justify="left"
        )
        self.option_label.pack(side="left", fill="x", expand=True)
        
        # Bottom row: Explanation
        self.explanation_label = tk.Label(
            self.frame,
            text="",
            font=("Segoe UI", 10, "italic"),
            fg="#9499B0",
            bg=self.bg_color,
            wraplength=420,
            justify="left"
        )
        self.explanation_label.pack(fill="x", pady=(10, 0), anchor="w")

    def _bind_events(self):
        """4. Draggable window logic and shortcuts."""
        # Left click and drag to move
        self.root.bind("<ButtonPress-1>", self._on_drag_start)
        self.root.bind("<B1-Motion>", self._on_drag_motion)
        
        # Right click to instantly hide the overlay
        self.root.bind("<Button-3>", lambda e: self.hide())

    def _on_drag_start(self, event):
        """Record the start position for dragging."""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        """Calculate the new position and move the window."""
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        
        new_x = self.root.winfo_x() + delta_x
        new_y = self.root.winfo_y() + delta_y
        
        self.root.geometry(f"+{new_x}+{new_y}")

    def display_answer(self, result: dict):
        """Update the UI with structured answer and show with fade-in."""
        if not isinstance(result, dict):
            return
            
        self.letter_label.config(text=result.get("letter", "?"), fg=self.text_color)
        self.option_label.config(text=result.get("text", "No option text"), fg=self.header_color)
        self.explanation_label.config(text=result.get("explanation", "No explanation available."))
        
        self.show()
        self._fade_in()
        
        # Auto-hide after 8 seconds
        self.root.after(8000, self._fade_out)

    def display_error(self, message: str):
        """Show an error message in the overlay."""
        self.letter_label.config(text="!", fg="#e74c3c")
        self.option_label.config(text="AI ERROR", fg="#e74c3c")
        self.explanation_label.config(text=message)
        
        self.show()
        self._fade_in()
        self.root.after(5000, self._fade_out)
        
    def set_status(self, text: str):
        self.option_label.config(text=text)
        self.explanation_label.config(text="")
        self.letter_label.config(text="...")
        self.show()

    def _fade_in(self):
        alpha = self.root.attributes("-alpha")
        if alpha < 0.95:
            alpha += 0.05
            self.root.attributes("-alpha", alpha)
            self.root.after(20, self._fade_in)

    def _fade_out(self):
        alpha = self.root.attributes("-alpha")
        if alpha > 0.05:
            alpha -= 0.05
            self.root.attributes("-alpha", alpha)
            self.root.after(20, self._fade_out)
        else:
            self.hide()

    def show(self):
        """Make the overlay visible."""
        self.root.deiconify()
        
    def hide(self):
        """Hide the overlay."""
        self.root.attributes("-alpha", 0.0)
        self.root.withdraw()

    def update(self):
        """Update Tkinter manually (useful if running in a custom main loop without threading)."""
        self.root.update()

    def run(self):
        """Start the standard Tkinter blocking event loop."""
        self.root.mainloop()

# Quick test logic allowing the user to run the file directly
if __name__ == "__main__":
    print("Launching test overlay. Drag the window to move it, right-click to hide it.")
    app = StudyOverlay()
    app.display_answer({
        "letter": "B",
        "text": "Berlin",
        "explanation": "Berlin is the capital of Germany."
    })
    app.run()