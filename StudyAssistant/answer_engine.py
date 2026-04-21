import logging
import random
from typing import List

# Safely import OpenAI so the app doesn't crash if it's not installed
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

import requests
import json

from config import AI_PLUGIN, OPENAI_API_KEY, OPENAI_MODEL, AI_TIMEOUT, OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

# Enhanced prompt for structured response
SYSTEM_PROMPT = """You are an expert exam solver. 
You will be provided with a multiple-choice question and its options.
Your task is to determine the correct answer and provide a brief explanation.

RESPONSE FORMAT:
You MUST return a JSON object with the following fields:
1. "letter": The exact letter of the correct option (e.g., "A").
2. "text": The full text of the correct option.
3. "explanation": A one-sentence explanation of why this answer is correct.

Example Response:
{
  "letter": "B",
  "text": "Paris",
  "explanation": "Paris is the capital of France and its most populous city."
}

Do NOT provide any text outside of the JSON block.
"""

def extract_labels(options: List[str]) -> List[str]:
    """Helper to extract option labels (A, B, 1, 2) from option strings."""
    labels = []
    for opt in options:
        # If format is "A) Option text", split by ')'
        if ')' in opt:
            label = opt.split(')')[0].strip()
        # If format is "A. Option text", split by '.'
        elif '.' in opt:
            label = opt.split('.')[0].strip()
        # Fallback to the very first character
        else:
            label = opt[0]
            
        labels.append(label.upper())
    return labels

def solve_with_ollama(question: str, options: List[str]) -> dict:
    """Solves the MCQ using a local Ollama instance."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    options_text = "\n".join(options)
    prompt = f"{SYSTEM_PROMPT}\n\nQuestion:\n{question}\n\nOptions:\n{options_text}\n\nJSON Response:"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json" # Ollama supports forced JSON format
    }
    
    try:
        response = requests.post(url, json=payload, timeout=AI_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        raw_resp_text = data.get("response", "{}")
        # Parse the JSON string from response
        result = json.loads(raw_resp_text)
        result["raw_response"] = raw_resp_text
        return result
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return {"error": str(e), "raw_response": "No response"}

def check_ollama_status() -> bool:
    """Verifies if the Ollama server is reachable."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def solve_with_openai(question: str, options: List[str]) -> dict:
    """Solves the MCQ using OpenAI's API."""
    if not OpenAI:
        logger.error("OpenAI package not installed. Falling back to mock.")
        return solve_with_mock(question, options)
        
    if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE" or not OPENAI_API_KEY:
        logger.error("OpenAI API Key not configured. Falling back to mock.")
        return solve_with_mock(question, options)

    client = OpenAI(api_key=OPENAI_API_KEY, timeout=AI_TIMEOUT)
    
    options_text = "\n".join(options)
    user_prompt = f"Question:\n{question}\n\nOptions:\n{options_text}"
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        return result
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}. Falling back to mock.")
        return solve_with_mock(question, options)

def solve_with_mock(question: str, options: List[str]) -> dict:
    """Mock solver for offline mode or fallback. Returns a structured dummy response."""
    logger.info("Using MOCK answer engine.")
    if not options:
        return {"letter": "A", "text": "Mock Option", "explanation": "This is a mock answer."}
    
    labels = extract_labels(options)
    letter = random.choice(labels)
    # Find the option text that matches the letter
    text = "Unknown Option"
    for opt in options:
        if opt.startswith(letter):
            text = opt.split(')', 1)[-1].strip() if ')' in opt else opt
            break
            
    return {
        "letter": letter,
        "text": text,
        "explanation": "This is a simulated explanation for testing purposes."
    }

from functools import lru_cache

@lru_cache(maxsize=100)
def _cached_get_answer(question: str, options_tuple: tuple) -> dict:
    """Cached inner function for get_answer."""
    options = list(options_tuple)
    plugin = AI_PLUGIN.lower()
    
    if plugin == "openai":
        return solve_with_openai(question, options)
    elif plugin == "ollama":
        return solve_with_ollama(question, options)
    else:
        if plugin != "mock":
            logger.warning(f"Plugin '{plugin}' not implemented in answer_engine yet. Using mock fallback.")
        return solve_with_mock(question, options)

def get_answer(question: str, options: List[str]) -> dict:
    """
    Main entry point for the answer engine.
    Returns a dict: {"letter": "A", "text": "...", "explanation": "..."}
    """
    return _cached_get_answer(question, tuple(options))