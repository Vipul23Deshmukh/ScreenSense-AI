import json
from parser import parse_mcq

def run_tests():
    # 1. Standard format
    text1 = """
    12. Which planet is known as the Red Planet?
    A) Earth
    B) Mars
    C) Jupiter
    D) Venus
    """
    
    # 2. Alternative markers (dot, colon, parenthesis) and no space
    text2 = """
    What is the largest ocean on Earth?
    A.Atlantic Ocean
    B: Indian Ocean
    (C) Pacific Ocean
    D)Arctic
    """
    
    # 3. Multi-line question, Multi-line options, and Noise
    text3 = """
    |
    In the context of computer science, 
    what does the acronym CPU stand for?
    _
    A) Central Process Unit
    which is an old term
    B) Central Processing Unit
    the brain of the computer
    C) Computer Personal Unit
    ~
    """
    
    # 4. Numbered options with extra spaces
    text4 = """
    Who wrote 'Romeo and Juliet'?
       1)   William Shakespeare
       2. Charles Dickens
       3:   Jane Austen
    """
    
    # 5. Invalid / Too short (Edge case)
    text5 = """
    Hi
    A) Yes
    B) No
    """
    
    tests = [
        ("Standard Format", text1),
        ("Alternative Markers & Missing Spaces", text2),
        ("Multi-line & Noise Removal", text3),
        ("Numbered Options", text4),
        ("Edge Case (Too Short, should return None)", text5)
    ]
    
    for name, raw_text in tests:
        print(f"\n--- Testing: {name} ---")
        print("RAW TEXT:")
        print(raw_text.strip())
        print("-" * 20)
        
        result = parse_mcq(raw_text)
        
        print("PARSED RESULT:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("None (Did not pass MCQ validation thresholds)")

if __name__ == "__main__":
    run_tests()
