import re
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def test_parse_questions(text: str):
    boilerplate_patterns = [
        r"enrollment\s*no", r"roll\s*no", r"department", r"subject",
        r"branch", r"semester", r"date", r"total\s*marks", r"time\s*allowed",
        r"learning\s*objectives", r"learning\s*outcomes", r"faculty\s*name",
        r"lecture\s*no", r"title\s*of\s*the\s*lecture"
    ]
    
    # Pass 1: Remove blocks of "Learning Objectives" and "Learning Outcomes" if they exist
    text = re.sub(
        r"(?:Learning\s*Objectives|Learning\s*Outcomes).*?(?=Q\s*\d+|Question\s*\d+|$)", 
        "", 
        text, 
        flags=re.IGNORECASE | re.DOTALL
    )

    lines = text.splitlines()
    filtered_lines = []
    for line in lines:
        if not any(re.search(p, line, re.IGNORECASE) for p in boilerplate_patterns):
            filtered_lines.append(line)
    
    clean_text = "\n".join(filtered_lines)
    print(f"--- CLEAN TEXT ---\n{clean_text}\n-------------------")
    
    questions = []
    has_q_marker = bool(re.search(r"Q\s*\d+", clean_text, re.IGNORECASE))
    
    if has_q_marker:
        q_prefix_pattern = r"(?:Q\.?\s*\d+[\.\):])"
    else:
        q_prefix_pattern = r"(?:\d+|[ivx]+|[a-z])[\.\):]"

    parts = re.split(f"(?:^|\n)\s*{q_prefix_pattern}", clean_text, flags=re.IGNORECASE)
    
    if len(parts) > 1:
        for part in parts[1:]:
            q = _clean(part)
            if q and len(q) > 10:
                if not any(re.search(bp, q[:50], re.IGNORECASE) for bp in boilerplate_patterns[:5]):
                    questions.append(q)
    return questions

sample_text = """
Department: Computer Science & Engineering Session: Jan-Jun 2026
Name of Faculty: Atul Barve Semester VI
Subject: Compiler Design Subject Code: CS603 (C)
Lecture No-28
Title of the Lecture: Introduction to Run Time Environment, Storage Organization, Activation Records
Learning Objectives: 
1. Explain the concept of run time environment in compiler design.
2. Describe different storage organization techniques used during program execution.
3. Understand the structure and purpose of activation records.
4. Analyze memory allocation during function calls.
5. Relate run time support with procedure execution.
Learning Outcomes: 
1. Identify the components of the run time environment.
2. Differentiate between static, stack, and heap storage allocation.
3. Draw and interpret activation record structures.
4. Explain how control is transferred during procedure calls.
5. Analyze memory usage for nested function calls.

Q1: Draw the activation record for the following function call and label all fields:
int sum(int a, int b)

Q2: What is the purpose of a display in compiler design?
"""

result = test_parse_questions(sample_text)
print("\n--- EXTRACTED QUESTIONS ---")
for i, q in enumerate(result, 1):
    print(f"{i}. {q}")
