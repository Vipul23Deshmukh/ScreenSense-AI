# Tesseract OCR Setup Guide

To ensure the `ocr.py` module works correctly, Tesseract OCR must be installed on your Windows machine.

## 1. Install Tesseract for Windows

The easiest way to install Tesseract on Windows is via the precompiled installer provided by UB Mannheim.

1. Download the latest Windows installer:
   * [Tesseract at UB Mannheim (64-bit)](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the `.exe` installer.
3. During the installation:
   * It's highly recommended to keep the default installation path: `C:\Program Files\Tesseract-OCR`
   * Expand the "Additional language data" section and check any other languages you might want to extract text from (e.g., French, Spanish, Math equations).

## 2. Configure Your Application

The Study Assistant needs to know where Tesseract is installed.

In `config.py`, verify that `TESSERACT_CMD` points to the correct installation path:

```python
# config.py
# Path to Tesseract executable (Windows default)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Tesseract language(s). Use "eng" for English.
OCR_LANGUAGE = "eng"
```

*Note: If you installed Tesseract somewhere else (e.g., `C:\Users\Name\AppData\Local\Tesseract-OCR`), update `config.py` accordingly.*

## 3. Verify the Installation

I've created a test script called `test_ocr.py` which:
1. Generates a dummy MCQ question image
2. Adds simulated noise to the image
3. Preprocesses the image (grayscale, noise removal, binarization)
4. Runs the Tesseract OCR engine
5. Prints the extracted clean text

To test it, run:
```cmd
python test_ocr.py
```

If it successfully prints the question and options (like London, Berlin, Paris, Madrid), your OCR setup is complete and ready to use!
