# 🎓 ScreenSense AI: Study Assistant

A professional, high-performance desktop application that automates the process of identifying, capturing, and solving multiple-choice questions (MCQs) from your screen in real-time. Powered by Tesseract OCR and Local AI (Ollama).

![Dashboard Preview](debug.png) *(Placeholder for actual dashboard screenshot)*

---

## ✨ Features

- **📺 Centralized Dashboard** — A sleek, modern Tkinter control panel to manage the entire pipeline.
- **🔍 Live OCR Preview** — See exactly what the AI is scanning with real-time visual confirmation.
- **🎯 Interactive Region Selection** — Draw your capture area directly on the screen with a transparent, draggable box.
- **⚡ Real-time Monitoring** — Smart change detection ensures processing only happens when the screen content changes.
- **🤖 Local AI Integration** — Privacy-focused answer generation using **Ollama** (Llama 3/Phi-3). Supports OpenAI & Groq fallbacks.
- **🪄 Floating Overlay** — A borderless, non-intrusive window that displays answers directly over your study material.
- **📜 Live System Logs** — Real-time event tracking (Ollama status, OCR accuracy, AI response times) visible in the dashboard.
- **⌨️ Global Hotkeys** — Control the app from anywhere without switching windows.

---

## 📁 Project Structure

```text
StudyAssistant/
├── main.py            # Main entry point & Orchestrator
├── dashboard.py       # Modern Tkinter Control Panel UI
├── capture_box.py     # Interactive "Draw-to-Select" Region Tool
├── overlay.py         # Floating, semi-transparent answer window
├── ocr.py             # Image preprocessing + Tesseract/EasyOCR logic
├── answer_engine.py   # AI Backend (Ollama, OpenAI, Groq, Mock)
├── change_detector.py # Pixel-diff based optimization
├── config.py          # Central configuration & constants
├── requirements.txt   # Python dependencies
└── history/           # Persistent Q&A history (JSON)
```

---

## 🚀 Quick Start

### 1. Requirements
- **Python 3.10+**
- **Tesseract OCR**: [Download & Install](https://github.com/UB-Mannheim/tesseract/wiki)
- **Ollama**: [Download & Install](https://ollama.com/) (For local AI)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/Vipul23Deshmukh/ScreenSense-AI.git
cd ScreenSense-AI/StudyAssistant

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Open `config.py` to customize the behavior:
- Set `TESSERACT_CMD` to your Tesseract path (default: `C:\Program Files\Tesseract-OCR\tesseract.exe`).
- Choose your `AI_PLUGIN` (`"ollama"`, `"openai"`, `"groq"`, or `"mock"`).
- Customize `HOTKEYS` and `OVERLAY_DURATION`.

### 4. Run
```bash
python main.py
```

---

## ⌨️ Global Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl + Alt + S` | **Toggle Monitoring** (Start/Stop scanning) |
| `Ctrl + Alt + R` | **Adjust Region** (Show/Hide interactive capture box) |
| `Ctrl + Shift + A` | **Scan Now** (Force a manual scan & solve) |
| `Ctrl + Alt + H` | **Hide/Show Overlay** (Toggle floating window) |
| `Ctrl + Q` | **Quit** (Safe exit) |

---

## 🛠️ How it Works

1. **Capture**: The app monitors a specific region of your screen (defined by you).
2. **Detect**: It uses a change detector to wait until the screen becomes "stable" (no movement).
3. **OCR**: Once stable, it captures the frame and extracts text using Tesseract.
4. **Parse**: A specialized MCQ parser separates the Question from Option A, B, C, D.
5. **Solve**: The parsed data is sent to the AI (Ollama/GPT-4) to determine the correct answer.
6. **Display**: The result appears instantly on your dashboard and a floating overlay.

---

## 🔌 AI Backends

| Backend | Speed | Privacy | Setup |
|---------|-------|---------|-------|
| **Ollama** | Fast | 🔒 High | `ollama run llama3` |
| **Groq** | ⚡ Ultra | ☁️ Med | `set GROQ_API_KEY=...` |
| **OpenAI** | Med | ☁️ Med | `set OPENAI_API_KEY=...` |
| **Mock** | Instant | 🔒 High | No setup (for testing) |

---

## 📜 License
MIT License - Developed by Vipul Deshmukh. Use responsibly!
