"""Run the six synthetic support cases through the router and print the result table.

Inputs and policies come from cases.json. `subject_covered` is a hand label
stored in that file: the inputs have a free-text question and no subject
field, and the router does not classify questions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # also works under `python3 -I`, which drops the script dir

from policy_router import resolve_policy  # noqa: E402

LABELS = {
    "subject_not_covered": "none: subject not covered",
    "channel_missing": "none: channel missing",
    "channel_unsupported": "none: channel unsupported",
    "receipt_date_missing": "none: receipt date missing",
    "receipt_date_in_future": "none: receipt date after request",
    "no_valid_policy": "none: date outside every version",
}


def main() -> int:
    data = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    policies = data["policies"]
    print("| Case | Router result | Expected source | Match |")
    print("| --- | --- | --- | --- |")
    mismatches = 0
    for case in data["cases"]:
        given = case["input"]
        decision = resolve_policy(
            subject_covered=case["subject_covered"],
            channel=given["channel"],
            received_on=given["received_on"],
            observed_on=given["observed_on"],
            policies=policies,
        )
        shown = decision.selected_version or LABELS.get(decision.status, decision.status)
        expected = case["expected_source_ids"]
        match = list(decision.source_ids) == expected
        mismatches += not match
        print(f"| {case['case_id']} | {shown} | {', '.join(expected) or 'none'} | {'yes' if match else 'NO'} |")
    print()
    print(f"{len(data['cases']) - mismatches}/{len(data['cases'])} match the expected source written before the model run.")
    print("subject_covered is a hand label for all six cases, not something the router decided.")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
