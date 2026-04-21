import tkinter as tk
from typing import Optional, Tuple
import ctypes

try:
    # Make Tkinter DPI aware to match mss coordinate system
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class RegionSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes("-topmost", True)
        self.root.configure(cursor="cross")
        
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        self.selected_region = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", self.on_escape)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, 1, 1, outline='red', width=3, fill="black", stipple="gray12"
        )

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        
        # Calculate proper top-left, width, height
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)
        
        if width > 10 and height > 10:
            self.selected_region = (left, top, width, height)
        
        self.root.quit()

    def on_escape(self, event):
        self.root.quit()

def select_region() -> Optional[Tuple[int, int, int, int]]:
    """
    Opens a fullscreen transparent overlay to let the user draw a box.
    Returns (left, top, width, height) or None if canceled.
    """
    selector = RegionSelector()
    selector.root.mainloop()
    region = selector.selected_region
    selector.root.destroy()
    return region

if __name__ == "__main__":
    region = select_region()
    # No print in production mode
