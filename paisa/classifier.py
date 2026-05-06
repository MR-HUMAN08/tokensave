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
    "distributed lock",
}


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def classify(prompt: str) -> Tuple[str, float]:
    if not prompt:
        label = "SIMPLE"
        confidence = 0.5
        print(f"[classifier] label={label} confidence={confidence:.2f}")
        return label, confidence

    length = len(prompt)
    lower_prompt = prompt.lower()

    trimmed = prompt.strip()
    if len(trimmed) < 20 and re.search(r"\d", trimmed) and re.search(r"[+\-*/]", trimmed):
        label = "SIMPLE"
        confidence = 1.0
        print(f"[classifier] label={label} confidence={confidence:.2f}")
        return label, confidence

    if _contains_any(lower_prompt, _COMPLEX_KEYWORDS):
        label = "COMPLEX"
        confidence = 0.9 if length > 200 else 0.7
        print(f"[classifier] label={label} confidence={confidence:.2f}")
        return label, confidence

    if _contains_any(lower_prompt, _MODERATE_KEYWORDS):
        label = "MODERATE"
        confidence = 0.8
        print(f"[classifier] label={label} confidence={confidence:.2f}")
        return label, confidence

    if length > 300:
        label = "COMPLEX"
        confidence = 0.6
        print(f"[classifier] label={label} confidence={confidence:.2f}")
        return label, confidence
    if length < 50:
        label = "SIMPLE"
        confidence = 0.6
        print(f"[classifier] label={label} confidence={confidence:.2f}")
        return label, confidence

    label = "MODERATE"
    confidence = 0.6
    print(f"[classifier] label={label} confidence={confidence:.2f}")
    return label, confidence
