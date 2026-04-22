"""
config.py — Central configuration for AI Study Assistant
Lightweight version.
"""

import os
import logging

# ─────────────────────────────────────────────
#  SCREEN CAPTURE
# ─────────────────────────────────────────────
# Default Capture region: (left, top, width, height)
CAPTURE_REGION = (100, 100, 600, 400)

# ─────────────────────────────────────────────
#  OCR
# ─────────────────────────────────────────────
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
OCR_LANGUAGE = "eng"
OCR_RESIZE_FACTOR = 2

# ─────────────────────────────────────────────
#  AI ANSWER ENGINE
# ─────────────────────────────────────────────
AI_PLUGIN = "ollama"  # "openai" | "ollama" | "mock"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:1b"
AI_TIMEOUT = 60

# ─────────────────────────────────────────────
#  OVERLAY UI
# ─────────────────────────────────────────────
OVERLAY_DURATION_MS = 8000
OVERLAY_WIDTH = 460
OVERLAY_HEIGHT = 160

# ─────────────────────────────────────────────
#  HOTKEYS
# ─────────────────────────────────────────────
HOTKEY_SCAN = "ctrl+shift+a"
HOTKEY_EXIT = "ctrl+q"

# ─────────────────────────────────────────────
#  LOGGING & PATHS
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "study_assistant.log")

def setup_logger(name: str = "StudyAssistant") -> logging.Logger:
    """Simplified logger setup."""
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
        
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)
        
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger
