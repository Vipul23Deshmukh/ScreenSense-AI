"""
utils.py — Shared helper utilities for AI Study Assistant
"""

import os
import re
import json
import logging
import hashlib
import datetime
from typing import Any, Dict, Optional

import config


# ─────────────────────────────────────────────
#  LOGGER SETUP
# ─────────────────────────────────────────────

def setup_logger(name: str = "StudyAssistant") -> logging.Logger:
    """
    Create and return a logger that writes to both console and a rotating log file.
    """
    os.makedirs(config.LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%H:%M:%S"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # File handler
    fh = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


logger = setup_logger()


# ─────────────────────────────────────────────
#  TEXT UTILITIES
# ─────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Normalise OCR output:
    - Remove non-printable characters
    - Collapse multiple blank lines
    - Strip trailing whitespace per line
    """
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)      # keep printable ASCII + newline
    text = re.sub(r"[ \t]+", " ", text)               # collapse inline spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)            # max 2 consecutive newlines
    lines = [ln.rstrip() for ln in text.splitlines()]
    return "\n".join(lines).strip()


def text_hash(text: str) -> str:
    """Return a short SHA-256 hex digest for deduplication."""
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def truncate(text: str, max_len: int = 300) -> str:
    """Truncate long text for display/logging."""
    return text[:max_len] + "…" if len(text) > max_len else text


# ─────────────────────────────────────────────
#  HISTORY / PERSISTENCE
# ─────────────────────────────────────────────

def ensure_dirs() -> None:
    """Create output directories if they don't exist."""
    os.makedirs(config.LOG_DIR, exist_ok=True)
    os.makedirs(config.HISTORY_DIR, exist_ok=True)


def save_qa_history(entry: Dict[str, Any]) -> None:
    """
    Append a Q&A entry to the JSON history file.
    Each entry contains timestamp, question, options, answer.
    Avoids saving duplicate questions.
    """
    ensure_dirs()
    history = load_qa_history()
    
    new_q = entry.get("question", "").strip()
    for item in history:
        if item.get("question", "").strip() == new_q:
            logger.debug("Duplicate question found in history. Skipping save.")
            return

    entry["timestamp"] = datetime.datetime.now().isoformat()
    history.append(entry)
    try:
        with open(config.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        logger.error("Failed to save history: %s", exc)


def load_qa_history() -> list:
    """Load the full Q&A history list from disk."""
    if not os.path.exists(config.HISTORY_FILE):
        return []
    try:
        with open(config.HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_history_summary() -> str:
    """Return a human-readable summary of the session history."""
    history = load_qa_history()
    if not history:
        return "No history yet."
    lines = [f"Total Q&A logged: {len(history)}\n"]
    for i, h in enumerate(history[-5:], 1):           # show last 5
        ts  = h.get("timestamp", "")[:19]
        ans = h.get("answer", {}).get("letter", "?")
        q   = truncate(h.get("question", ""), 60)
        lines.append(f"  [{ts}]  {ans}  —  {q}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
#  CONFIDENCE SCORING
# ─────────────────────────────────────────────

def compute_confidence(raw_response: str, answer_letter: str) -> float:
    """
    Heuristic confidence score (0-1) based on how clearly the model
    stated the answer letter in its response.
    """
    if not answer_letter or answer_letter == "?":
        return 0.0

    letter = answer_letter.strip().upper()
    text   = raw_response.upper()

    patterns = [
        rf"\bANSWER[:\s]+{letter}\b",
        rf"\b{letter}\b is correct",
        rf"correct answer is {letter}",
        rf"^{letter}[\.:\)]\s",
    ]
    for pat in patterns:
        if re.search(pat, text, re.MULTILINE):
            return 0.95

    # Fallback: letter appears at all
    if re.search(rf"\b{letter}\b", text):
        return 0.70

    return 0.40


# ─────────────────────────────────────────────
#  MISC
# ─────────────────────────────────────────────

def timestamp_str() -> str:
    """Return current time as 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp a numeric value between lo and hi."""
    return max(lo, min(hi, value))
