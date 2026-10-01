import unittest
from collections import Counter
from datetime import date

from lifecycle import llm, mock
from lifecycle.campaign import assign_arm, build_plan
from lifecycle.compliance import check_variant, rendered_sms_len
from lifecycle.generate import generate_variants, load_brand
from lifecycle.score import pick_winners, rank, score_variant
from lifecycle.segments import load_customers, segment_counts, segment_of

llm.register_mock(mock.handler)
AS_OF = date(2026, 9, 30)


def cust(**kw):
    base = {"customer_id": "X", "first_name": "Sam", "email_optin": True, "sms_optin": True,
            "signup_date": date(2025, 1, 1), "last_order_date": date(2026, 9, 20), "orders": 1,
            "total_spend": 50.0, "interest": "sleep"}
    base.update(kw)
    return base


def good_variant(**kw):
    v = {"angle": "benefit", "subject": "Your next step is ready, {first_name}",
         "preview": "Small habits add up. Your dashboard makes the next step simple.",
         "email_body": "Hi {first_name}, thanks for being with us. Small habits add up. Your dashboard makes "
                       "the next step simple. Pick up where you left off whenever you are ready today. "
                       "Visit your dashboard: {cta_link}. Unsubscribe: {unsubscribe_link}.",
         "sms": "Hi {first_name}, your next step: {cta_link} Reply STOP to opt out"}
    v.update(kw)
    return v


class SegmentTest(unittest.TestCase):
    def test_segments(self):
        self.assertEqual(segment_of(cust(orders=0, last_order_date=None, signup_date=date(2026, 9, 20)), AS_OF), "new")
        self.assertEqual(segment_of(cust(orders=0, last_order_date=None), AS_OF), "prospect")
        self.assertEqual(segment_of(cust(orders=5, total_spend=900), AS_OF), "vip")
        self.assertEqual(segment_of(cust(), AS_OF), "active")
        self.assertEqual(segment_of(cust(last_order_date=date(2026, 7, 15)), AS_OF), "at_risk")
        self.assertEqual(segment_of(cust(last_order_date=date(2026, 4, 1)), AS_OF), "lapsed")

    def test_sample_file(self):
        counts = segment_counts(load_customers("data/customers.csv"), AS_OF)
        self.assertEqual(sum(counts.values()), 14)
        self.assertGreaterEqual(len(counts), 5)


class ComplianceTest(unittest.TestCase):
    def test_good_variant_passes(self):
        self.assertEqual(check_variant(good_variant()), [])

    def test_forbidden_claims(self):
        self.assertTrue(check_variant(good_variant(subject="Guaranteed results")))
        self.assertTrue(check_variant(good_variant(email_body="This can cure it {unsubscribe_link}")))

    def test_channel_rules(self):
        self.assertTrue(check_variant(good_variant(sms="Hi {first_name} {cta_link}")))            # no STOP
        self.assertTrue(check_variant(good_variant(email_body="no unsubscribe {cta_link}")))      # no unsubscribe
        long_sms = "x" * 140 + " {cta_link} Reply STOP"
        self.assertGreater(rendered_sms_len(long_sms), 160)
        self.assertTrue(check_variant(good_variant(sms=long_sms)))


class ScoreTest(unittest.TestCase):
    def test_better_variant_scores_higher(self):
        weak = good_variant(subject="Hi", preview="x", email_body="Short {unsubscribe_link}")
        self.assertGreater(score_variant(good_variant())["score"], score_variant(weak)["score"])

    def test_violators_never_win_even_with_top_score(self):
        bad = good_variant(angle="urgency", subject="Guaranteed results for you, {first_name}")
        ok = good_variant(angle="benefit", subject="Hi", preview="x")
        self.assertGreater(score_variant(bad)["score"], score_variant(ok)["score"])  # bad scores higher...
        winners = pick_winners(rank([bad, ok]))                                    # ...but is disqualified
        self.assertEqual([w["angle"] for w in winners], ["benefit"])


class CampaignTest(unittest.TestCase):
    def test_assignment_is_stable_and_balanced(self):
        self.assertEqual(assign_arm("e", "C1", 2), assign_arm("e", "C1", 2))
        arms = Counter(assign_arm("e", f"C{i}", 2) for i in range(1000))
        self.assertTrue(400 < arms[0] < 600)

    def test_opt_outs_and_suppression(self):
        winners = {"active": [good_variant()]}
        plan = build_plan([cust(customer_id="A", sms_optin=False),
                           cust(customer_id="B", email_optin=False, sms_optin=False),
                           cust(customer_id="C", last_order_date=date(2026, 1, 1))], winners, AS_OF)
        channels = [(m["customer_id"], m["channel"]) for m in plan["messages"]]
        self.assertEqual(channels, [("A", "email")])
        self.assertEqual({s["customer_id"] for s in plan["suppressed"]}, {"B", "C"})

    def test_end_to_end_with_mock(self):
        customers = load_customers("data/customers.csv")
        brand, winners = load_brand(), {}
        for seg in segment_counts(customers, AS_OF):
            variants, _ = generate_variants(seg, brand)
            winners[seg] = pick_winners(rank(variants))
            self.assertTrue(winners[seg])
            self.assertTrue(all(not w["violations"] for w in winners[seg]))
        plan = build_plan(customers, winners, AS_OF)
        self.assertTrue(plan["messages"])
        for m in plan["messages"]:
            self.assertNotIn("{", m["body"])
            if m["channel"] == "sms":
                self.assertLessEqual(len(m["body"]), 160)


if __name__ == "__main__":
    unittest.main()
