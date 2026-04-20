"""
AI answer generation via Groq API.
Model: llama-3.3-70b-versatile
"""
import os
import re
import logging
from groq import Groq

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")
        _client = Groq(api_key=api_key)
    return _client


def generate_answers(subject_name: str, questions: list[str]) -> dict:
    """
    Send questions to Groq and return {question: answer} dict.
    Falls back gracefully on API errors.
    """
    if not questions:
        return {}

    logger.info(f"[ai_service] Generating answers for {len(questions)} questions in '{subject_name}'")

    formatted_questions = "\n".join(
        [f"Q{i + 1}. {q}" for i, q in enumerate(questions)]
    )

    prompt = f"""You are an expert academic tutor helping a B.Tech engineering student at an Indian university.

Subject: {subject_name}

Answer ALL of the following assignment questions. For each question:
- Write a clear, complete, academic-quality answer.
- Use proper technical terminology appropriate for B.Tech level.
- Aim for 3-6 paragraphs per answer depending on complexity.
- Structure answers with well-formed sentences and paragraphs.
- Do NOT add any preamble or introduction. Go directly to answering.

Format your response EXACTLY as follows (do not deviate from this format):
ANSWER_1:
[your answer here]

ANSWER_2:
[your answer here]

Continue for all questions.

Questions:
{formatted_questions}
"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content
        logger.info(f"[ai_service] Received {len(raw)} chars from Groq")
        return _parse_answers(questions, raw)

    except Exception as exc:
        logger.error(f"[ai_service] Groq API error: {exc}")
        # Return a fallback dict so the pipeline can still produce a document
        return {
            q: "AI answer generation failed for this question. Please answer manually."
            for q in questions
        }


def _parse_answers(questions: list[str], raw_text: str) -> dict:
    """Parse ANSWER_N: blocks from Groq response."""
    parts = re.split(r"ANSWER_\d+:", raw_text)
    answers = [p.strip() for p in parts if p.strip()]

    result = {}
    for i, q in enumerate(questions):
        if i < len(answers):
            result[q] = answers[i]
        else:
            result[q] = "Answer not generated for this question."
            logger.warning(f"[ai_service] No answer parsed for question {i + 1}")

    return result
