from __future__ import annotations

import re


TOKEN_RE = re.compile(r"[A-Za-z0-9#b]+")


def normalize_pattern(pattern: str) -> str:
    tokens = TOKEN_RE.findall(pattern)
    if not tokens:
        raise ValueError("Pattern must contain at least one harmonic token.")
    normalized = [_normalize_token(token) for token in tokens]
    return "-".join(normalized)


def _normalize_token(token: str) -> str:
    accidental = ""
    body = token
    if token and token[0] in {"b", "#"} and len(token) > 1:
        accidental = token[0]
        body = token[1:]
    return accidental + body.upper()

