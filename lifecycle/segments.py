"""Rule-based customer segmentation on recency, frequency and spend."""
from __future__ import annotations

import csv
from collections import Counter
from datetime import date


def _d(s: str):
    return date.fromisoformat(s) if s else None


def load_customers(path: str) -> list[dict]:
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "customer_id": r["customer_id"], "first_name": r["first_name"],
                "email_optin": r["email_optin"].lower() == "yes", "sms_optin": r["sms_optin"].lower() == "yes",
                "signup_date": _d(r["signup_date"]), "last_order_date": _d(r["last_order_date"]),
                "orders": int(r["orders"]), "total_spend": float(r["total_spend"]), "interest": r["interest"],
            })
    return rows


def segment_of(c: dict, as_of: date) -> str:
    if c["orders"] == 0 or c["last_order_date"] is None:
        return "new" if (as_of - c["signup_date"]).days <= 30 else "prospect"
    days = (as_of - c["last_order_date"]).days
    if days > 120:
        return "lapsed"
    if days > 60:
        return "at_risk"
    if c["orders"] >= 3 and c["total_spend"] >= 500:
        return "vip"
    return "active"


def segment_counts(customers: list[dict], as_of: date) -> Counter:
    return Counter(segment_of(c, as_of) for c in customers)
