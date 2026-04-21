"""
config.py — Central configuration for AI Study Assistant
All tunable parameters live here. Edit this file to customize behavior.
"""

import os

# ─────────────────────────────────────────────
#  SCREEN CAPTURE
# ─────────────────────────────────────────────
# Capture region: (left, top, width, height)
# Set to None to capture the full primary monitor.
CAPTURE_REGION = None  # e.g. (0, 0, 1280, 720)

# How often (seconds) the main loop grabs a frame
POLL_INTERVAL = 0.75

# Minimum seconds between two AI calls (cooldown)
ANSWER_COOLDOWN = 4.0

# Seconds the screen must remain completely static before triggering OCR
STABILITY_DELAY = 0.5

# ─────────────────────────────────────────────
#  CHANGE DETECTION
# ─────────────────────────────────────────────
# Fraction (0-1) of pixels that must differ to count as "changed"
CHANGE_THRESHOLD = 0.04

# Resize factor applied before diffing (smaller = faster, less precise)
CHANGE_RESIZE_FACTOR = 0.25

# Pixel intensity delta (0-255) below which a pixel is considered "same"
CHANGE_DIFF_THRESHOLD = 25

# Absolute minimum changed-pixel count (guards against near-zero fraction)
CHANGE_MIN_AREA = 200

# ─────────────────────────────────────────────
#  OCR
# ─────────────────────────────────────────────
# Path to Tesseract executable (Windows default)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Tesseract language(s). Use "eng+fra" for multi-language, etc.
OCR_LANGUAGE = "eng"

# Upscale factor to improve OCR on small text (e.g. 2 or 3)
OCR_RESIZE_FACTOR = 3

# Use EasyOCR as fallback if Tesseract fails or returns garbage
USE_EASYOCR_FALLBACK = True

# Confidence threshold below which OCR text is discarded (EasyOCR)
EASYOCR_MIN_CONFIDENCE = 0.4

# ─────────────────────────────────────────────
#  MCQ PARSER
# ─────────────────────────────────────────────
# Minimum chars for a detected question
MIN_QUESTION_LEN = 15

# Minimum number of options to consider it an MCQ
MIN_OPTIONS = 2

# ─────────────────────────────────────────────
#  AI ANSWER ENGINE
# ─────────────────────────────────────────────
# Which AI plugin to use: "openai" | "ollama" | "groq" | "mock"
AI_PLUGIN = "ollama"

# OpenAI / Groq API key (also reads from env var)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY",   "YOUR_GROQ_API_KEY_HERE")

# OpenAI model name
OPENAI_MODEL = "gpt-4o-mini"

# Groq model name
GROQ_MODEL = "llama3-70b-8192"

# Ollama local server
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "llama3"

# Timeout (seconds) for AI API requests
AI_TIMEOUT = 15

# ─────────────────────────────────────────────
#  OVERLAY UI
# ─────────────────────────────────────────────
# Initial position of the overlay window (x, y)
OVERLAY_POSITION = (30, 30)

# Overlay dimensions
OVERLAY_WIDTH  = 460
OVERLAY_HEIGHT = 160

# How long (ms) the overlay stays visible per answer
OVERLAY_DURATION_MS = 8000

# Fade animation steps
OVERLAY_FADE_STEPS = 20
OVERLAY_FADE_DELAY = 18  # ms between steps

# ─────────────────────────────────────────────
#  LOGGING & HISTORY
# ─────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
LOG_DIR     = os.path.join(BASE_DIR, "logs")
HISTORY_DIR = os.path.join(BASE_DIR, "history")
HISTORY_FILE = os.path.join(HISTORY_DIR, "qa_history.json")
LOG_FILE     = os.path.join(LOG_DIR,     "study_assistant.log")

# ─────────────────────────────────────────────
#  KEYBOARD SHORTCUTS
# ─────────────────────────────────────────────
HOTKEY_TOGGLE = "ctrl+alt+s"   # Start / Stop monitoring
HOTKEY_EXIT   = "ctrl+q"       # Quit application
HOTKEY_HIDE   = "ctrl+alt+h"   # Hide / Show overlay
HOTKEY_REGION = "ctrl+alt+r"   # Draw a custom capture region
