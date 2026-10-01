"""Template-based stand-in model so the pipeline runs offline. Not a quality benchmark."""
import json
import re

HOOKS = {"new": "Welcome", "vip": "Thank you", "at_risk": "We saved your spot", "lapsed": "It has been a while",
         "active": "Your routine", "prospect": "Ready when you are"}


def _variants(seg: str) -> list[dict]:
    hook = HOOKS.get(seg, "Hello")
    link = "{cta_link}"
    body = ("Hi {first_name}, thanks for being part of our community. Small habits add up, and your dashboard "
            "makes the next step simple. Pick up where you left off whenever you are ready. "
            f"Visit your dashboard: {link}. If you would rather not hear from us, use {{unsubscribe_link}}.")
    v1 = {"angle": "benefit", "subject": f"{hook}, {{first_name}}: your next step is ready",
          "preview": "Small habits add up. Your dashboard makes the next step simple and quick.",
          "email_body": body, "sms": f"Hi {{first_name}}, your next step is ready: {link} Reply STOP to opt out"}
    v2 = {"angle": "social_proof", "subject": "Members love this",
          "preview": "See what other members are doing this week.",
          "email_body": "Members tell us short routines work best. See what others are doing: "
                        f"{link}. Unsubscribe: {{unsubscribe_link}}.",
          "sms": f"Members love the new routines: {link} Reply STOP to opt out"}
    risky = seg == "at_risk"
    v3 = {"angle": "urgency",
          "subject": ("Guaranteed results if you come back today, {first_name}" if risky
                      else f"{hook}, {{first_name}}: a quick reminder for this week"),
          "preview": "A short note that fits into your week, with one clear next step for you.",
          "email_body": ("Hi {first_name}, come back today for guaranteed results. " if risky
                         else "Hi {first_name}, this week is a good moment to check in. ")
                        + f"It takes two minutes. Visit your dashboard: {link}. Unsubscribe: {{unsubscribe_link}}.",
          "sms": f"{{first_name}}, a quick reminder: {link} Reply STOP to opt out"}
    return [v1, v2, v3]


def handler(system: str, prompt: str, model: str) -> str:
    seg = re.search(r"Segment: (\w+)", prompt).group(1)
    return json.dumps({"variants": _variants(seg)})
