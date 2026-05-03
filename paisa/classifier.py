from __future__ import annotations

import re
from typing import Iterable, Tuple

from sentence_transformers import SentenceTransformer


# Load once at import time so requests reuse the same model instance.
_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

_MODERATE_KEYWORDS = {
    "explain",
    "compare",
    "difference",
    "summarize",
    "list",
    "what is the difference",
    "what is the relationship",
    "what is the impact",
    "who is",
    "when",
    "where",
    "how many",
}
_COMPLEX_KEYWORDS = {
    "write code",
    "implement",
    "algorithm",
    "function",
    "debug",
    "analyze",
    "design",
    "architecture",
    "optimize",
    "build",
    "create a program",
    "step by step",
}


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _heuristic_label(prompt: str) -> Tuple[str, float]:
    length = len(prompt)
    lower_prompt = prompt.lower()

    if length > 300:
        return "COMPLEX", 0.9

    if _contains_any(lower_prompt, _COMPLEX_KEYWORDS):
        if length > 200:
            return "COMPLEX", 0.9
        return "COMPLEX", 0.7

    if _contains_any(lower_prompt, _MODERATE_KEYWORDS):
        return "MODERATE", 0.8

    if length < 50:
        return "SIMPLE", 0.6
    if length > 200:
        return "COMPLEX", 0.6
    return "MODERATE", 0.6


def classify(prompt: str) -> Tuple[str, float]:
    if not prompt:
        label = "SIMPLE"
        confidence = 0.5
        print(f"[classifier] label={label} confidence={confidence:.2f}")
        return label, confidence

    trimmed = prompt.strip().lower()
    if len(trimmed) < 20 and re.search(r"\d", trimmed) and re.search(r"[+\-*/]", trimmed):
        label = "SIMPLE"
        confidence = 1.0
        print(f"[classifier] label={label} confidence={confidence:.2f}")
        return label, confidence

    # Trigger a lightweight embedding call to ensure the model is loaded.
    _MODEL.encode([prompt], show_progress_bar=False)

    label, confidence = _heuristic_label(prompt)
    print(f"[classifier] label={label} confidence={confidence:.2f}")
    return label, confidence
