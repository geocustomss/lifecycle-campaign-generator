# lifecycle-campaign-generator

[![CI](https://github.com/geocustomss/lifecycle-campaign-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/geocustomss/lifecycle-campaign-generator/actions/workflows/ci.yml)

Segment customers, generate email + SMS variants per segment with an LLM, **automatically block anything that makes
non-compliant claims**, score what's left, and output a per-customer send plan with a deterministic A/B split.

Built for regulated-ish categories (health and wellness) where "the model wrote something it shouldn't have" is the
main risk of AI-generated marketing.

```
customers.csv ─► segments (new / active / vip / at_risk / lapsed / prospect)
                      │
                      ▼  LLM generates N variants per segment (validated JSON, retried on bad output)
            compliance gate  ── forbidden claims, SMS length *as rendered*, unsubscribe + STOP language ──► disqualify
                      ▼
            heuristic scoring (subject length, CTA, personalization, readability, ...) ─► top 2 per segment
                      ▼
            send plan: respects email/SMS opt-in, stable hash-based A/B assignment, suppression list
```

## Quickstart (no API keys needed)

```bash
python -m unittest discover -s tests -v
python -m lifecycle --as-of 2026-09-30 --out out        # writes out/campaign_plan.json + variants_scored.json
python -m lifecycle --provider anthropic --model claude-haiku-4-5-20251001   # real model (set ANTHROPIC_API_KEY)
```

Customer data in `data/customers.csv` is synthetic. Edit `lifecycle/brand.json` for voice and CTA.

## Sample run (mock model)

```
as_of=2026-09-30  customers=14  generation cost=$0.009013

segment   n   variants disqualified winner(s)
new       2   3        0            benefit(100), urgency(85)
vip       3   3        0            benefit(100), urgency(85)
active    3   3        0            benefit(100), urgency(85)
at_risk   2   3        1            benefit(100), social_proof(60)
lapsed    2   3        0            benefit(100), urgency(75)
prospect  2   3        0            benefit(100), urgency(75)

messages planned: 21   suppressed: 1
  blocked [at_risk/urgency]: forbidden claim: 'guaranteed'
```

The mock model deliberately writes one non-compliant "guaranteed results" variant for the `at_risk` segment, and the
gate blocks it even though a plain quality score would have ranked it highly (see `test_violators_never_win...`).

## Design decisions

- **Compliance is a hard gate, scoring is a soft ranking.** A variant with a banned claim can never win, no matter how
  well it scores.
- **SMS length is checked as rendered**, using worst-case name and link lengths. Checking the template alone lets
  160-character violations slip through after personalization.
- **Deterministic A/B assignment**: `sha256(experiment + customer_id) % arms` gives a stable, roughly even split with
  no state to store, so results can be joined back to arms later.
- **Opt-in respected per channel**; customers with no channel or no compliant variant land on a suppression list with a reason.
- A test caught a real bug while building this (the unsubscribe placeholder wasn't being rendered), which is the
  reason the end-to-end test asserts no `{placeholder}` survives into a final message.

## Limitations / next steps

- Scores are transparent heuristics, not measured performance. The real objective is conversion, so wire in send
  results and promote winners with a proper significance test.
- The banned-claims list is illustrative; real programs need legal review of claims language per channel and region.
- Add Klaviyo (or other ESP) export: profile properties plus flow variants via their API.
- Add an LLM judge as a second-pass scorer and measure its agreement with human ratings.
