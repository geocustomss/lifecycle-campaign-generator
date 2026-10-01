"""Generate message variants per segment with an LLM, validated against a schema."""
from __future__ import annotations

import json
from pathlib import Path

from . import llm

FIELDS = ("angle", "subject", "preview", "email_body", "sms")
SYSTEM = ("You write lifecycle marketing for a wellness brand. Never make medical or health-outcome claims "
          "(no cure, treat, prevent, guarantee, clinically proven). Use only the placeholders given.")


def load_brand(path: str | None = None) -> dict:
    return json.loads(Path(path or Path(__file__).with_name("brand.json")).read_text())


def build_prompt(segment: str, brand: dict, n: int) -> str:
    return (
        f"Brand: {brand['name']}. Voice: {brand['voice']}.\nSegment: {segment}\n"
        f"Write {n} distinct variants, each with a different angle (e.g. benefit, social_proof, urgency).\n"
        "Reply with ONLY JSON: "
        '{"variants": [{"angle": "...", "subject": "<=60 chars", "preview": "40-90 chars", '
        '"email_body": "40-120 words", "sms": "<=160 chars"}]}\n'
        "Placeholders: {first_name}, {cta_link}, {unsubscribe_link}. The email body must contain "
        f"{{cta_link}} and {{unsubscribe_link}}. The SMS must contain {{cta_link}} and end with 'Reply STOP to opt out'. "
        f"CTA idea: {brand['cta']}."
    )


def validate(n: int):
    def check(obj) -> None:
        variants = obj.get("variants") if isinstance(obj, dict) else None
        if not isinstance(variants, list) or len(variants) < n:
            raise ValueError(f"need a 'variants' list with {n} items")
        for v in variants:
            missing = [f for f in FIELDS if not isinstance(v.get(f), str) or not v[f].strip()]
            if missing:
                raise ValueError(f"variant missing fields: {missing}")
    return check


def generate_variants(segment: str, brand: dict, n: int = 3, provider: str = "mock",
                      model: str = "mock-large", complete_fn=None) -> tuple[list[dict], float]:
    obj, attempts = llm.complete_json(build_prompt(segment, brand, n), validate(n), system=SYSTEM,
                                      complete_fn=complete_fn, provider=provider, model=model)
    return obj["variants"][:n], sum(a.cost_usd for a in attempts)
