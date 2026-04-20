import re
import logging
from typing import Dict, List, Optional
from config import MIN_QUESTION_LEN, MIN_OPTIONS

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Removes excessive whitespace and common OCR artifacts."""
    # Replace multiple spaces/newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove weird OCR artifact characters at the boundaries
    text = text.strip(' |_-\\/~`')
    return text.strip()

def parse_mcq(raw_text: str) -> Optional[Dict[str, any]]:
    """
    Parses raw OCR text into a structured MCQ dictionary.
    Handles multiple formats (A), A., A:), multi-line text, and filters noise.
    
    Returns:
        {"question": "...", "options": ["...", "..."]} or None if invalid.
    """
    if not raw_text:
        return None
        
    lines = raw_text.split('\n')
    question_lines = []
    options = []
    current_option_lines = []
    current_option_label = None
    
    # Regex to match option markers like: A), a), A., a., A:, (A), 1), 1., etc.
    # Groups:
    # 1: The label (A-E or 1-5)
    # 2: The actual option text
    # The \s* handles missing spaces like 'A)London' vs 'A) London'
    option_pattern = re.compile(r'^\s*\(?([a-eA-E]|[1-5])\)?[\.\:\)]\s*(.*)')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
            
        # Ignore obvious noise lines (e.g., a single random character like '|' or '_')
        # However, we don't skip short lines if they are part of a valid option marker.
        if len(line) < 3 and not option_pattern.match(line):
            continue
            
        match = option_pattern.match(line)
        
        if match:
            # We found a new option marker!
            # Save the previous option if one exists
            if current_option_lines:
                options.append(clean_text(" ".join(current_option_lines)))
                current_option_lines = []
            
            # Start a new option
            label = match.group(1).upper() # Standardize label to uppercase
            option_text = match.group(2).strip()
            
            # Include the standardized label in the output for consistency (e.g., "A) Paris")
            current_option_lines.append(f"{label}) {option_text}")
            
        else:
            # Not an option marker. 
            # Does it belong to an ongoing option (multi-line option)?
            if current_option_lines:
                current_option_lines.append(line)
            # Or does it belong to the question?
            else:
                question_lines.append(line)
                
    # Save the very last option
    if current_option_lines:
        options.append(clean_text(" ".join(current_option_lines)))
        
    question_text = clean_text(" ".join(question_lines))
    
    # Validation against config thresholds to ensure it's actually an MCQ
    if len(question_text) < MIN_QUESTION_LEN:
        logger.warning(f"Extracted question is too short ({len(question_text)} chars). Ignoring.")
        return None
        
    if len(options) < MIN_OPTIONS:
        logger.warning(f"Not enough options found (Found {len(options)}, Required {MIN_OPTIONS}). Ignoring.")
        return None
        
    return {
        "question": question_text,
        "options": options
    }
