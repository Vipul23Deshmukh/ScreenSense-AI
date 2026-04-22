import re
import config

logger = config.setup_logger("parser")

def parse_mcq(raw_text: str) -> dict:
    if not raw_text: return None
    
    lines = raw_text.split('\n')
    question_lines, options = [], []
    current_opt = []
    
    # Pattern for A) or A. or (A)
    opt_pattern = re.compile(r'^\s*\(?([a-eA-E]|[1-5])\)?[\.\:\)]\s*(.*)')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        match = opt_pattern.match(line)
        if match:
            if current_opt: options.append(" ".join(current_opt))
            current_opt = [f"{match.group(1).upper()}) {match.group(2).strip()}"]
        else:
            if current_opt: current_opt.append(line)
            else: question_lines.append(line)
            
    if current_opt: options.append(" ".join(current_opt))
    
    question = " ".join(question_lines).strip()
    if len(question) < 10 or len(options) < 2:
        return None
        
    return {"question": question, "options": options}
