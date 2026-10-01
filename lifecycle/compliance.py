"""Marketing-claim and channel rules. Any violation disqualifies a variant."""
import re

FORBIDDEN = [r"\bcure[sd]?\b", r"\bguarantee[sd]?\b", r"\bmiracle\b", r"\bfda[- ]approved\b", r"\brisk[- ]free\b",
             r"\btreat(s|ed|ing|ment)?\b", r"\bprevent(s|ed|ing)?\b", r"\bclinically proven\b",
             r"\breverse (aging|ageing)\b", r"\blose \d+ ?(lbs|pounds)\b"]
SMS_MAX = 160
FIRST_NAME_MAX = 15   # worst-case rendered length of {first_name}
LINK_LEN = 30         # rendered length of {cta_link}


def rendered_sms_len(sms: str) -> int:
    return len(sms.replace("{first_name}", "x" * FIRST_NAME_MAX).replace("{cta_link}", "x" * LINK_LEN))


def check_variant(v: dict) -> list[str]:
    problems = []
    text = " ".join(str(v.get(k, "")) for k in ("subject", "preview", "email_body", "sms")).lower()
    for pattern in FORBIDDEN:
        m = re.search(pattern, text)
        if m:
            problems.append(f"forbidden claim: '{m.group(0)}'")
    if "{unsubscribe_link}" not in v.get("email_body", ""):
        problems.append("email missing {unsubscribe_link}")
    sms = v.get("sms", "")
    if rendered_sms_len(sms) > SMS_MAX:
        problems.append(f"sms too long when rendered ({rendered_sms_len(sms)} > {SMS_MAX})")
    if "reply stop" not in sms.lower():
        problems.append("sms missing 'Reply STOP' opt-out")
    return problems
