import pyautogui
import time

print("Move mouse to TOP-LEFT corner of the question...")
time.sleep(5)
x1, y1 = pyautogui.position()
print(f"Top-left: {x1}, {y1}")

print("Now move mouse to BOTTOM-RIGHT of the answer options...")
time.sleep(5)
x2, y2 = pyautogui.position()
print(f"Bottom-right: {x2}, {y2}")

width = x2 - x1
height = y2 - y1

print("\n✅ Your REGION is:")
print(f"({x1}, {y1}, {width}, {height})")