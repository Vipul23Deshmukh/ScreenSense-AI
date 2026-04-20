import os
from answer_engine import get_answer
import config

def run_tests():
    question = "Which planet is known as the Red Planet?"
    options = [
        "A) Earth",
        "B) Mars",
        "C) Jupiter",
        "D) Venus"
    ]
    
    print("\n" + "="*50)
    print("TESTING ANSWER ENGINE")
    print("="*50)
    
    print(f"Question: {question}")
    for opt in options:
        print(f"  {opt}")
    
    print("\n--- 1. Testing MOCK Fallback Engine ---")
    # Override config for testing mock
    config.AI_PLUGIN = "mock"
    mock_answer = get_answer(question, options)
    print(f"Result (Mock returns random): {mock_answer}")
    
    print("\n--- 2. Testing Plugin Fallback Warning ---")
    config.AI_PLUGIN = "ollama" # Since it's not implemented, should fallback to mock
    mock_answer2 = get_answer(question, options)
    print(f"Result (Ollama Fallback): {mock_answer2}")
    
    print("\n--- 3. Testing OpenAI Engine (Graceful Failure) ---")
    # Test OpenAI without setting API key to ensure the fallback works gracefully without crashing
    config.AI_PLUGIN = "openai"
    # Temporarily remove API key from environment if it exists just for this specific test
    original_key = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"
    
    fallback_answer = get_answer(question, options)
    print(f"Result (Graceful Fallback): {fallback_answer}")
    
    # Restore key
    config.OPENAI_API_KEY = original_key
    
    print("\n" + "="*50)
    print("Tests Completed Successfully!")
    print("="*50)

if __name__ == "__main__":
    run_tests()
