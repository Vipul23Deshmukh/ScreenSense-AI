from overlay import AnswerOverlay
import time

overlay = AnswerOverlay(position=(50, 50))

print("Showing overlay...")

overlay.show({
    "letter": "B",
    "option": "Motivation and reward",
    "why": "Dopamine drives motivation"
}, duration_ms=5000)

time.sleep(6)