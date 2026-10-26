"""Boundary tests for deterministic source-version selection, not LLM quality."""

import json
import unittest
from pathlib import Path

from policy_router import resolve_policy


HERE = Path(__file__).resolve().parent
POLICIES = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["policies"]


class PolicyRouterTests(unittest.TestCase):
    def route(self, received_on, *, channel="online-store", observed_on="2026-10-04", subject_covered=True):
        return resolve_policy(
            subject_covered=subject_covered,
            channel=channel,
            received_on=received_on,
            observed_on=observed_on,
            policies=POLICIES,
        )

    def test_ret_v1_inclusive_start(self):
        result = self.route("2026-01-01")
        self.assertEqual((result.status, result.selected_version, result.source_ids), ("selected", "RET-V1", ("RET-V1",)))

    def test_ret_v1_day_before_exclusive_end(self):
        result = self.route("2026-09-30")
        self.assertEqual((result.status, result.selected_version), ("selected", "RET-V1"))

    def test_ret_v2_inclusive_start(self):
        result = self.route("2026-10-01")
        self.assertEqual((result.status, result.selected_version), ("selected", "RET-V2"))

    def test_gap_before_first_policy(self):
        result = self.route("2025-12-31")
        self.assertEqual((result.status, result.selected_version, result.source_ids), ("no_valid_policy", None, ()))

    def test_missing_receipt_date_does_not_guess_latest_policy(self):
        result = self.route(None)
        self.assertEqual((result.status, result.selected_version, result.missing_fields), ("receipt_date_missing", None, ("received_on",)))

    def test_unsupported_channel_does_not_fall_back_to_online_policy(self):
        result = self.route("2026-10-02", channel="corporate-contract")
        self.assertEqual((result.status, result.selected_version, result.source_ids), ("channel_unsupported", None, ()))

    def test_uncovered_subject_does_not_select_return_policy(self):
        result = self.route("2026-10-02", subject_covered=False)
        self.assertEqual((result.status, result.selected_version), ("subject_not_covered", None))

    def test_future_receipt_date_is_not_routed(self):
        result = self.route("2026-10-05", observed_on="2026-10-04")
        self.assertEqual((result.status, result.selected_version), ("receipt_date_in_future", None))

    def test_rejects_non_canonical_date(self):
        with self.assertRaises(ValueError):
            self.route("2026-9-30")

    def test_rejects_overlapping_policy_intervals(self):
        overlapping = [dict(POLICIES[0]), dict(POLICIES[1])]
        overlapping[1]["applies_to_received_from"] = "2026-09-01"
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            resolve_policy(subject_covered=True, channel="online-store", received_on="2026-09-30", observed_on="2026-10-04", policies=overlapping)


if __name__ == "__main__":
    unittest.main()
