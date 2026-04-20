# 🎓 AI Study Assistant

A desktop application that watches your screen, detects multiple-choice questions in real-time using OCR, and displays the AI-generated answer in a floating overlay — all within seconds.

---

## ✨ Features

- **Real-time screen monitoring** — polls a configurable region of your screen
- **Smart change detection** — only processes frames when content actually changes
- **Dual-engine OCR** — Tesseract (primary) + EasyOCR (fallback)
- **MCQ-aware parser** — extracts question + options into a structured object
- **Pluggable AI backend** — Ollama (local), OpenAI, Groq, or Mock (offline testing)
- **Floating answer overlay** — borderless, draggable, fade-in/out, with confidence bar
- **Q&A history** — every answer saved to `history/qa_history.json`
- **Global hotkeys** — toggle monitoring, hide overlay, quit

---

## 📁 Project Structure

```
StudyAssistant/
├── main.py            # Entry point — wires everything together
├── capture.py         # Screen grabber (mss + pyautogui fallback)
├── change_detector.py # Frame-diff based change detection
├── ocr.py             # Text extraction (Tesseract + EasyOCR)
├── parser.py          # MCQ text → structured MCQuestion object
├── answer_engine.py   # AI backend plugins (Ollama/OpenAI/Groq/Mock)
├── overlay.py         # Floating Tkinter answer window
├── config.py          # ← ALL settings live here
├── utils.py           # Shared helpers (logger, text, history)
├── requirements.txt   # pip dependencies
├── logs/              # Auto-created at runtime
└── history/           # Auto-created at runtime
```

---

## 🚀 Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (Windows)

Download and install from:  
👉 https://github.com/UB-Mannheim/tesseract/wiki

Default install path expected: `C:\Program Files\Tesseract-OCR\tesseract.exe`  
Change `TESSERACT_CMD` in `config.py` if you installed elsewhere.

### 3. Set up your AI backend

**Option A — Ollama (local, free, recommended)**
```bash
# Install Ollama: https://ollama.com
ollama run llama3
```
In `config.py`: `AI_PLUGIN = "ollama"` _(already the default)_

**Option B — OpenAI**
```bash
set OPENAI_API_KEY=sk-...
```
In `config.py`: `AI_PLUGIN = "openai"`

**Option C — Groq**
```bash
set GROQ_API_KEY=gsk_...
```
In `config.py`: `AI_PLUGIN = "groq"`

**Option D — Mock (offline testing, no AI needed)**  
In `config.py`: `AI_PLUGIN = "mock"`

### 4. Configure your capture region

Open `config.py` and set:
```python
CAPTURE_REGION = (left, top, width, height)
# Example: (0, 0, 1280, 720)  — top-left quarter of a 2560×1440 screen
# Set to None for full primary monitor
```

> **Tip:** Run `find_region.py` to interactively draw your capture region.

### 5. Run

```bash
python main.py
```

---

## ⌨️ Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+Alt+S` | Toggle monitoring on / off |
| `Ctrl+Alt+H` | Hide / show overlay |
| `Ctrl+Q` | Quit |

All hotkeys are configurable in `config.py`.

---

## ⚙️ Configuration (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `CAPTURE_REGION` | `None` | Screen region `(left, top, w, h)` or `None` for full screen |
| `POLL_INTERVAL` | `0.75` | Seconds between screen grabs |
| `ANSWER_COOLDOWN` | `4.0` | Minimum seconds between AI calls |
| `CHANGE_THRESHOLD` | `0.04` | Pixel-fraction that must differ to trigger |
| `AI_PLUGIN` | `"ollama"` | `"ollama"` / `"openai"` / `"groq"` / `"mock"` |
| `OLLAMA_MODEL` | `"llama3"` | Local model name |
| `OVERLAY_DURATION_MS` | `8000` | How long the overlay stays visible |
| `OVERLAY_POSITION` | `(30, 30)` | Initial overlay position (x, y) |

---

## 🔌 Pipeline

```
Screen grab (capture.py)
    ↓  numpy frame
Change detection (change_detector.py)
    ↓  "yes, something changed"
OCR extraction (ocr.py)
    ↓  raw text string
MCQ parsing (parser.py)
    ↓  MCQuestion(question, options)
AI answering (answer_engine.py)
    ↓  {letter, option, why, confidence}
Floating overlay (overlay.py)
    ↓  shown on screen + saved to history
```

---

## 📜 License

MIT — use freely, contribute back!
