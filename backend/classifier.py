from __future__ import annotations

import re
from typing import Iterable, Tuple


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
    """
    Lightweight keyword-based classification rules:
    - Math pattern (digits + operators, <20 chars) → SIMPLE, 1.0
    - COMPLEX keywords found → COMPLEX, 0.9 or 0.7
    - MODERATE keywords found → MODERATE, 0.8
    - Length >300 chars → COMPLEX, 0.6
    - Length <50 chars → SIMPLE, 0.6
    - Default → MODERATE, 0.6
    """
    length = len(prompt)
    lower_prompt = prompt.lower()

    # Math pattern detection (high confidence simple)
    trimmed = prompt.strip()
    if len(trimmed) < 20 and re.search(r"\d", trimmed) and re.search(r"[+\-*/]", trimmed):
        return "SIMPLE", 1.0

    # COMPLEX keywords
    if _contains_any(lower_prompt, _COMPLEX_KEYWORDS):
        if length > 200:
            return "COMPLEX", 0.9
        return "COMPLEX", 0.7

    # MODERATE keywords
    if _contains_any(lower_prompt, _MODERATE_KEYWORDS):
        return "MODERATE", 0.8

    # Length-based heuristics
    if length > 300:
        return "COMPLEX", 0.6
    if length < 50:
        return "SIMPLE", 0.6

    # Default
    return "MODERATE", 0.6


def classify(prompt: str) -> Tuple[str, float]:
    """
    Classify a prompt into SIMPLE, MODERATE, or COMPLEX.
    Uses pure keyword matching and length heuristics.
    No ML models required.
    """
    if not prompt:
        label = "SIMPLE"
        confidence = 0.5
        print(f"[classifier] label={label} confidence={confidence:.2f}")
        return label, confidence

    label, confidence = _heuristic_label(prompt)
    print(f"[classifier] label={label} confidence={confidence:.2f}")
    return label, confidence
