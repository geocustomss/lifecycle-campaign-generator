"""Turn winning variants into a per-customer send plan with a deterministic A/B split."""
from __future__ import annotations

import hashlib
from datetime import date

from .segments import segment_of


def assign_arm(experiment: str, customer_id: str, n_arms: int) -> int:
    """Stable hash split: the same customer always gets the same arm for an experiment."""
    return int(hashlib.sha256(f"{experiment}:{customer_id}".encode()).hexdigest(), 16) % n_arms


def render(text: str, customer: dict) -> str:
    return (text.replace("{first_name}", customer["first_name"])
                .replace("{cta_link}", f"https://example.com/c/{customer['customer_id']}")
                .replace("{unsubscribe_link}", f"https://example.com/u/{customer['customer_id']}"))


def build_plan(customers: list[dict], winners: dict[str, list[dict]], as_of: date,
               experiment: str = "exp-001") -> dict:
    messages, suppressed = [], []
    for c in customers:
        seg = segment_of(c, as_of)
        arms = winners.get(seg, [])
        if not arms:
            suppressed.append({"customer_id": c["customer_id"], "reason": f"no compliant variant for {seg}"})
            continue
        arm = assign_arm(experiment, c["customer_id"], len(arms))
        v = arms[arm]
        sent = False
        if c["email_optin"]:
            messages.append({"customer_id": c["customer_id"], "segment": seg, "channel": "email", "arm": arm,
                             "angle": v["angle"], "subject": render(v["subject"], c),
                             "body": render(v["email_body"], c)})
            sent = True
        if c["sms_optin"]:
            messages.append({"customer_id": c["customer_id"], "segment": seg, "channel": "sms", "arm": arm,
                             "angle": v["angle"], "body": render(v["sms"], c)})
            sent = True
        if not sent:
            suppressed.append({"customer_id": c["customer_id"], "reason": "no channel opt-in"})
    return {"experiment": experiment, "as_of": as_of.isoformat(), "messages": messages, "suppressed": suppressed}
