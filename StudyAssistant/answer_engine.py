import logging
import random
from typing import List

# Safely import OpenAI so the app doesn't crash if it's not installed
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from config import AI_PLUGIN, OPENAI_API_KEY, OPENAI_MODEL, AI_TIMEOUT

logger = logging.getLogger(__name__)

# Strong prompt engineered for high accuracy and strict formatting constraints
SYSTEM_PROMPT = """You are an expert exam solver. 
You will be provided with a multiple-choice question and its options.
Your task is to determine the absolute correct answer.

CRITICAL INSTRUCTIONS:
- Return ONLY the exact letter or number of the correct option (e.g., A, B, C, D, 1, 2).
- Do NOT provide any explanation, period, or punctuation.
- Your entire response must be exactly one character/label long.
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

def solve_with_mock(question: str, options: List[str]) -> str:
    """Mock solver for offline mode or fallback. Returns a random option."""
    logger.info("Using MOCK answer engine.")
    if not options:
        return "A"
    
    labels = extract_labels(options)
    return random.choice(labels)

def solve_with_openai(question: str, options: List[str]) -> str:
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
            temperature=0.0, # 0.0 for highly deterministic/factual answers
            max_tokens=5,    # Constrain output length tightly
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Cleanup fallback: if the AI disobeys and gives "A." or "A)", clean it
        answer = answer.replace('.', '').replace(')', '').replace(':', '').strip()
        
        # Final safety check: if it still gave a long explanation, extract just the first letter
        if len(answer) > 2:
            answer = answer[0].upper()
            
        return answer
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}. Falling back to mock.")
        return solve_with_mock(question, options)

from functools import lru_cache

@lru_cache(maxsize=100)
def _cached_get_answer(question: str, options_tuple: tuple) -> str:
    """Cached inner function for get_answer."""
    options = list(options_tuple)
    plugin = AI_PLUGIN.lower()
    
    if plugin == "openai":
        return solve_with_openai(question, options)
    else:
        # Fallback to mock for ollama/groq for now if not implemented,
        # but user specifically asked for "OpenAI API or mock"
        if plugin not in ("openai", "mock"):
            logger.warning(f"Plugin '{plugin}' not implemented in answer_engine yet. Using mock fallback.")
            
        return solve_with_mock(question, options)

def get_answer(question: str, options: List[str]) -> str:
    """
    Main entry point for the answer engine.
    Routes to the appropriate plugin based on config.
    Uses LRU caching to return instant answers for previously seen questions.
    """
    return _cached_get_answer(question, tuple(options))