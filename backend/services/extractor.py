"""
Question paper extractor.
Supports: PDF (via PyMuPDF) and DOCX (via python-docx).
Returns a clean list of question strings.
"""
import os
import re
import logging

logger = logging.getLogger(__name__)


def extract_questions(filepath: str) -> list[str]:
    """
    Auto-detect file type and extract questions.
    Returns a list of question strings.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        raw_text = _extract_text_from_pdf(filepath)
    elif ext in (".docx", ".doc"):
        raw_text = _extract_text_from_docx(filepath)
    elif ext == ".txt":
        raw_text = _extract_text_from_txt(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return _parse_questions(raw_text)


# ── Extractors ────────────────────────────────────────────────────────────────

def _extract_text_from_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        full_text = f.read()
    logger.debug(f"[extractor] TXT extracted {len(full_text)} chars from {filepath}")
    return full_text


def _extract_text_from_pdf(filepath: str) -> str:
    import fitz  # PyMuPDF
    text_parts = []
    with fitz.open(filepath) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    full_text = "\n".join(text_parts)
    logger.debug(f"[extractor] PDF extracted {len(full_text)} chars from {filepath}")
    return full_text


def _extract_text_from_docx(filepath: str) -> str:
    from docx import Document
    doc = Document(filepath)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    # Also pull text from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text:
                    paragraphs.append(cell_text)
    full_text = "\n".join(paragraphs)
    logger.debug(f"[extractor] DOCX extracted {len(full_text)} chars from {filepath}")
    return full_text


# ── Parser ─────────────────────────────────────────────────────────────────────

def _parse_questions(text: str) -> list[str]:
    """
    Attempts multiple strategies to identify questions from raw text.
    """
    # 0. Pre-filter boilerplate (Common in PIEMR papers)
    boilerplate_patterns = [
        r"enrollment\s*no", r"roll\s*no", r"department", r"subject",
        r"branch", r"semester", r"date", r"total\s*marks", r"time\s*allowed",
        r"learning\s*objectives", r"learning\s*outcomes", r"faculty\s*name",
        r"lecture\s*no", r"title\s*of\s*the\s*lecture"
    ]
    
    # Pass 1: Remove blocks of "Learning Objectives" and "Learning Outcomes" if they exist
    # These often contain numbered lists that look like questions but aren't.
    # We strip until the first "Q" or "Question" is seen.
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
    questions = []

    # Strategy 1: Numbered/Lettered questions
    # Handles: Q1., 1., (1), i., (a), etc.
    # We prefer Q prefixes if they are present.
    has_q_marker = bool(re.search(r"Q\s*\d+", clean_text, re.IGNORECASE))
    
    if has_q_marker:
        # If the paper uses "Q1", "Q.1", etc., we should ONLY look for those
        q_prefix_pattern = r"(?:Q\.?\s*\d+[\.\):])"
    else:
        # Fallback to general numbering if no Q markers exist
        q_prefix_pattern = r"(?:\d+|[ivx]+|[a-z])[\.\):]"

    # Prepend newline for split pattern if needed
    parts = re.split(fr"(?:^|\n)\s*{q_prefix_pattern}", clean_text, flags=re.IGNORECASE)
    
    if len(parts) > 1:
        # parts[0] is usually header text before the first question
        for part in parts[1:]:
            q = _clean(part)
            # Basic sanity check: must be long enough and not just boilerplate
            if q and len(q) > 10:
                # Double check we didn't catch a footer/header fragment
                if not any(re.search(bp, q[:50], re.IGNORECASE) for bp in boilerplate_patterns[:5]):
                    questions.append(q)
        
        if questions:
            logger.debug(f"[extractor] Found {len(questions)} questions via split pattern (has_q={has_q_marker})")
            return questions

    # Strategy 2: Fallback — interrogative words or lines ending in ?
    for line in filtered_lines:
        stripped = line.strip()
        if (
            stripped.endswith("?")
            or re.match(r"^(what|how|why|when|where|explain|describe|define|list|discuss|compare|analyze|write|state|derive|draw)", stripped, re.IGNORECASE)
        ):
            q = _clean(stripped)
            if q and len(q) > 15:
                questions.append(q)

    if questions:
        logger.debug(f"[extractor] Found {len(questions)} questions via fallback pattern")
        return questions

    # Strategy 3: Last resort — treat non-empty blocks as questions
    logger.warning("[extractor] Could not detect structured questions — treating paragraphs as questions")
    for block in re.split(r"\n{2,}", clean_text):
        q = _clean(block)
        if q and len(q) > 25:
            questions.append(q)

    return questions[:15]


def _clean(text: str) -> str:
    """Normalise whitespace in a string."""
    return re.sub(r"\s+", " ", text).strip()
