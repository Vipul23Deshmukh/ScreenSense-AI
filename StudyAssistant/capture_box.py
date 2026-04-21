import tkinter as tk
from typing import Optional, Tuple
import ctypes

try:
    # Make Tkinter DPI aware to match mss coordinate system
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class CaptureRegionBox:
    def __init__(self, initial_region=(100, 100, 400, 300), on_change=None):
        self.root = tk.Tk()
        self.root.title("Capture Region")
        
        # Window attributes
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.6)  # Semi-transparent
        
        # Color configuration
        self.bg_color = "#000001" # Near-black
        self.border_color = "#2ecc71" # Vibrant green
        self.glow_color = "#27ae60" # Darker green for glow
        
        # State
        self.on_change = on_change
        self.dragging = False
        self.resizing = False
        self.resize_side = None # 'n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'
        
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._initial_window_x = 0
        self._initial_window_y = 0
        self._initial_window_w = 0
        self._initial_window_h = 0

        # Set initial geometry (fallback to default if None)
        if not initial_region:
            initial_region = (100, 100, 400, 300)
            
        x, y, w, h = initial_region
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        self.canvas = tk.Canvas(self.root, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Draw initial border
        self._update_canvas()

    def _update_canvas(self):
        self.canvas.delete("all")
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        
        # Outer glow
        self.canvas.create_rectangle(0, 0, w, h, outline=self.glow_color, width=8)
        # Inner sharp border
        self.canvas.create_rectangle(2, 2, w-2, h-2, outline=self.border_color, width=2)
        
        # Add a small label in the corner
        self.canvas.create_text(
            10, 15, 
            text=f"Capture Region: {w}x{h}", 
            fill=self.border_color, 
            anchor="w",
            font=("Segoe UI", 9, "bold")
        )

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._update_cursor)

    def _on_press(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._initial_window_x = self.root.winfo_x()
        self._initial_window_y = self.root.winfo_y()
        self._initial_window_w = self.root.winfo_width()
        self._initial_window_h = self.root.winfo_height()
        
        cursor_type = self.canvas.cget("cursor")
        if cursor_type and cursor_type != "arrow":
            self.resizing = True
            self.resize_side = self._get_side_from_cursor(cursor_type)
        else:
            self.dragging = True

    def _on_motion(self, event):
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        
        if self.dragging:
            new_x = self._initial_window_x + dx
            new_y = self._initial_window_y + dy
            self.root.geometry(f"+{new_x}+{new_y}")
            
        elif self.resizing:
            new_x = self._initial_window_x
            new_y = self._initial_window_y
            new_w = self._initial_window_w
            new_h = self._initial_window_h
            
            if 'e' in self.resize_side: new_w += dx
            if 'w' in self.resize_side: 
                new_x += dx
                new_w -= dx
            if 's' in self.resize_side: new_h += dy
            if 'n' in self.resize_side: 
                new_y += dy
                new_h -= dy
            
            # Minimum size
            new_w = max(new_w, 100)
            new_h = max(new_h, 80)
            
            self.root.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")
            
        self._update_canvas()
        if self.on_change:
            self.on_change(self.get_region())

    def _on_release(self, event):
        self.dragging = False
        self.resizing = False
        if self.on_change:
            self.on_change(self.get_region())

    def _update_cursor(self, event):
        if self.dragging or self.resizing: return
        
        x, y = event.x, event.y
        w, h = self.root.winfo_width(), self.root.winfo_height()
        margin = 10
        
        cursor = ""
        if x < margin: cursor += "w"
        elif x > w - margin: cursor += "e"
        
        if y < margin: cursor += "n"
        elif y > h - margin: cursor += "s"
        
        if cursor:
            # Tkinter cursor names are slightly different
            tk_cursor = {
                "n": "sb_v_double_arrow",
                "s": "sb_v_double_arrow",
                "e": "sb_h_double_arrow",
                "w": "sb_h_double_arrow",
                "nw": "top_left_corner",
                "ne": "top_right_corner",
                "sw": "bottom_left_corner",
                "se": "bottom_right_corner"
            }.get(cursor, "arrow")
            self.canvas.config(cursor=tk_cursor)
        else:
            self.canvas.config(cursor="arrow")

    def _get_side_from_cursor(self, cursor):
        mapping = {
            "sb_v_double_arrow": "n" if self._drag_start_y < self._initial_window_y + 20 else "s",
            "sb_h_double_arrow": "w" if self._drag_start_x < self._initial_window_x + 20 else "e",
            "top_left_corner": "nw",
            "top_right_corner": "ne",
            "bottom_left_corner": "sw",
            "bottom_right_corner": "se"
        }
        # Refine vertical/horizontal choice
        res = mapping.get(cursor, "")
        if res in ["n", "s"]:
            # Check if we were actually closer to top or bottom
            dist_top = abs(self._drag_start_y - self._initial_window_y)
            dist_bottom = abs(self._drag_start_y - (self._initial_window_y + self._initial_window_h))
            res = "n" if dist_top < dist_bottom else "s"
        if res in ["w", "e"]:
            dist_left = abs(self._drag_start_x - self._initial_window_x)
            dist_right = abs(self._drag_start_x - (self._initial_window_x + self._initial_window_w))
            res = "w" if dist_left < dist_right else "e"
        return res

    def set_border_color(self, color):
        self.border_color = color
        self._update_canvas()

    def get_region(self):
        return (self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height())

    def show(self):
        self.root.deiconify()
        self._update_canvas()

    def hide(self):
        self.root.withdraw()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    def print_region(r): print(f"New Region: {r}")
    box = CaptureRegionBox(on_change=print_region)
    box.run()
