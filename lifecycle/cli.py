import argparse
import json
from datetime import date
from pathlib import Path

from . import llm, mock
from .campaign import build_plan
from .generate import generate_variants, load_brand
from .score import pick_winners, rank
from .segments import load_customers, segment_counts


def main() -> None:
    llm.register_mock(mock.handler)
    p = argparse.ArgumentParser(prog="lifecycle")
    p.add_argument("--customers", default="data/customers.csv")
    p.add_argument("--as-of", default=date.today().isoformat())
    p.add_argument("--provider", default="mock")
    p.add_argument("--model", default="mock-large")
    p.add_argument("--variants", type=int, default=3)
    p.add_argument("--experiment", default="exp-001")
    p.add_argument("--out", default="out")
    args = p.parse_args()

    as_of = date.fromisoformat(args.as_of)
    customers = load_customers(args.customers)
    counts = segment_counts(customers, as_of)
    brand, winners, report, cost = load_brand(), {}, {}, 0.0

    for seg in counts:
        variants, c = generate_variants(seg, brand, args.variants, args.provider, args.model)
        ranked = rank(variants)
        winners[seg], report[seg], cost = pick_winners(ranked), ranked, cost + c

    plan = build_plan(customers, winners, as_of, args.experiment)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "variants_scored.json").write_text(json.dumps(report, indent=2))
    (out / "campaign_plan.json").write_text(json.dumps(plan, indent=2))

    print(f"as_of={as_of}  customers={len(customers)}  generation cost=${cost:.6f}\n")
    print(f"{'segment':<10}{'n':<4}{'variants':<9}{'disqualified':<13}winner(s)")
    for seg, ranked in report.items():
        dq = sum(1 for v in ranked if v["violations"])
        print(f"{seg:<10}{counts[seg]:<4}{len(ranked):<9}{dq:<13}"
              + ", ".join(f"{w['angle']}({w['score']})" for w in winners[seg]))
    print(f"\nmessages planned: {len(plan['messages'])}   suppressed: {len(plan['suppressed'])}")
    for seg, ranked in report.items():
        for v in ranked:
            for problem in v["violations"]:
                print(f"  blocked [{seg}/{v['angle']}]: {problem}")


if __name__ == "__main__":
    main()
