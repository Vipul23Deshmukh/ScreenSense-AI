import requests
import json
import random
import config

logger = config.setup_logger("answer_engine")

SYSTEM_PROMPT = """You are an expert study assistant. Analyze the MCQ carefully.
Rules:
- Read question carefully.
- Identify tricky words like: NOT, EXCEPT, FALSE, INCORRECT.
- Use elimination method.
- If confidence is low, set confidence to "Low".
Return ONLY JSON:
{"letter": "A/B/C/D", "text": "exact option text", "explanation": "short explanation", "confidence": "High/Low"}"""

def check_connection() -> bool:
    """Check if the AI service is reachable."""
    if config.AI_PLUGIN == "ollama":
        try:
            resp = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=2)
            return resp.status_code == 200
        except:
            return False
    return True # Mock is always connected

def get_answer(question: str, options: list) -> dict:
    """Main entry point for answer generation."""
    if config.AI_PLUGIN == "ollama":
        return solve_with_ollama(question, options)
    return solve_with_mock(question, options)

def solve_with_ollama(question: str, options: list) -> dict:
    url = f"{config.OLLAMA_BASE_URL}/api/generate"
    prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {question}\nOptions:\n" + "\n".join(options)
    
    try:
        resp = requests.post(url, json={
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=config.AI_TIMEOUT)
        data = resp.json()
        raw_res = data.get("response", "{}")
        logger.info(f"Ollama Raw: {raw_res}")
        
        res = json.loads(raw_res)
        # Add "Low confidence" warning to explanation if flagged
        if res.get("confidence") == "Low":
            res["explanation"] = "⚠️ [Low Confidence] " + res.get("explanation", "")
            
        return res
    except Exception as e:
        logger.error(f"Ollama Error: {e}")
        return {"error": str(e)}

def solve_with_mock(question: str, options: list) -> dict:
    logger.info("Using Mock AI")
    letter = random.choice(["A", "B", "C", "D"])
    return {
        "letter": letter,
        "text": f"Mock Option {letter}",
        "explanation": "This is a mock answer for testing."
    }