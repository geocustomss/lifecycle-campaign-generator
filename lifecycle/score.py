"""Score variants (0-100) with transparent heuristics; non-compliant variants are disqualified."""
from __future__ import annotations

import re

from .compliance import check_variant


def _avg_sentence_words(text: str) -> float:
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    return sum(len(s.split()) for s in sentences) / max(1, len(sentences))


def score_variant(v: dict) -> dict:
    b = {}
    n = len(v["subject"])
    b["subject_length"] = 20 if 25 <= n <= 60 else 10 if 15 <= n <= 70 else 0
    b["preview_length"] = 10 if 40 <= len(v["preview"]) <= 90 else 0
    body = v["email_body"]
    words = len(re.sub(r"\{[a-z_]+\}", "", body).split())
    b["cta_link"] = 20 if "{cta_link}" in body else 0
    b["personalization"] = 15 if "{first_name}" in v["subject"] + body else 0
    b["body_length"] = 15 if 40 <= words <= 120 else 5 if 25 <= words <= 150 else 0
    b["readability"] = 10 if _avg_sentence_words(body) <= 18 else 0
    b["sms"] = 10 if "{cta_link}" in v["sms"] and len(v["sms"]) <= 160 else 0
    return {"score": sum(b.values()), "breakdown": b, "violations": check_variant(v)}


def rank(variants: list[dict]) -> list[dict]:
    """Return variants with scores, compliant ones first (best score first)."""
    scored = [{**v, **score_variant(v)} for v in variants]
    return sorted(scored, key=lambda s: (bool(s["violations"]), -s["score"]))


def pick_winners(ranked: list[dict], k: int = 2) -> list[dict]:
    return [v for v in ranked if not v["violations"]][:k]
