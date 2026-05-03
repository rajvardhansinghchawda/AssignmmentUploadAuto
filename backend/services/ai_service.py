"""
AI answer generation via Groq API.

Model Pool Strategy (two-tier fallback):
  Tier 1 (Primary): Tried in order until one succeeds.
    1. llama-3.3-70b-versatile   (current default)
    2. llama-3.1-8b-instant
    3. meta-llama/llama-prompt-guard-2-22m
    4. meta-llama/llama-prompt-guard-2-86m
    5. openai/gpt-oss-120b
    6. openai/gpt-oss-20b

  Tier 2 (Last-resort): Used only when ALL Tier 1 models fail.
    7. groq/compound-mini
    8. groq/compound
"""
import os
import re
import time
import logging
from groq import Groq, RateLimitError, APIStatusError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model pools
# ---------------------------------------------------------------------------
PRIMARY_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "meta-llama/llama-prompt-guard-2-22m",
    "meta-llama/llama-prompt-guard-2-86m",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

FALLBACK_MODELS = [
    "groq/compound-mini",
    "groq/compound",
]

# ---------------------------------------------------------------------------
# Groq client (lazy singleton)
# ---------------------------------------------------------------------------
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")
        _client = Groq(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Internal: try a single model call
# ---------------------------------------------------------------------------
def _call_model(client: Groq, model: str, prompt: str) -> str:
    """
    Attempt to generate a completion with *model*.
    Returns the raw text content on success.
    Raises the original exception on failure so the caller can try the next model.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=4096,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Internal: iterate over a list of models, return first success
# ---------------------------------------------------------------------------
def _try_models(client: Groq, models: list[str], prompt: str, tier_label: str) -> str | None:
    """
    Try each model in *models* in order.
    Returns the raw response text from the first model that succeeds.
    Returns None if every model in the list fails.
    """
    for model in models:
        try:
            logger.info(f"[ai_service] [{tier_label}] Trying model: {model}")
            raw = _call_model(client, model, prompt)
            logger.info(f"[ai_service] [{tier_label}] Success with model: {model} ({len(raw)} chars)")
            return raw

        except RateLimitError as exc:
            logger.warning(
                f"[ai_service] [{tier_label}] Rate-limit hit for '{model}': {exc}. "
                "Trying next model…"
            )
        except APIStatusError as exc:
            logger.warning(
                f"[ai_service] [{tier_label}] API error for '{model}' "
                f"(status={exc.status_code}): {exc.message}. Trying next model…"
            )
        except Exception as exc:
            logger.warning(
                f"[ai_service] [{tier_label}] Unexpected error for '{model}': {exc}. "
                "Trying next model…"
            )

    logger.error(f"[ai_service] [{tier_label}] All models in pool failed.")
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_answers(subject_name: str, questions: list[str]) -> dict:
    """
    Send questions to Groq and return {question: answer} dict.

    Tries PRIMARY_MODELS first; if all fail, falls back to FALLBACK_MODELS.
    Returns a graceful error dict if every model is exhausted.
    """
    if not questions:
        return {}

    logger.info(
        f"[ai_service] Generating answers for {len(questions)} question(s) in '{subject_name}'"
    )

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
    except RuntimeError as exc:
        logger.error(f"[ai_service] Client initialization failed: {exc}")
        return _fallback_dict(questions)

    # --- Tier 1: Primary models ---
    raw = _try_models(client, PRIMARY_MODELS, prompt, tier_label="Tier-1 Primary")

    # --- Tier 2: Last-resort compound models ---
    if raw is None:
        logger.warning("[ai_service] All Tier-1 models exhausted. Switching to Tier-2 fallback pool…")
        raw = _try_models(client, FALLBACK_MODELS, prompt, tier_label="Tier-2 Fallback")

    # --- Total failure ---
    if raw is None:
        logger.error("[ai_service] Every model in both pools failed. Returning placeholder answers.")
        return _fallback_dict(questions)

    return _parse_answers(questions, raw)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fallback_dict(questions: list[str]) -> dict:
    """Return a placeholder dict when all AI generation attempts fail."""
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
