"""Generate traceable display examples by calling the policy router."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # also works under `python3 -I`, which drops the script dir

from policy_router import resolve_policy  # noqa: E402

SOURCE = HERE / "cases.json"
OUTPUT = HERE / "trace-examples.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source_data = json.loads(SOURCE.read_text(encoding="utf-8"))
    policies = source_data["policies"]
    scenarios = [
        {
            "id": "BOUNDARY-2026-09-30",
            "description": "Day before RET-V2 starts; RET-V1 end is exclusive.",
            "subject_covered": True,
            "channel": "online-store",
            "received_on": "2026-09-30",
            "observed_on": "2026-10-04",
        },
        {
            "id": "BOUNDARY-2026-10-01",
            "description": "RET-V2 start date is inclusive.",
            "subject_covered": True,
            "channel": "online-store",
            "received_on": "2026-10-01",
            "observed_on": "2026-10-04",
        },
        {
            "id": "CS-04-MISSING-DATE",
            "description": "Missing receipt date must not choose the newest policy.",
            "subject_covered": True,
            "channel": "online-store",
            "received_on": None,
            "observed_on": "2026-10-04",
        },
        {
            "id": "CS-06-UNSUPPORTED-CHANNEL",
            "description": "Corporate-contract channel is outside both online-store policies.",
            "subject_covered": True,
            "channel": "corporate-contract",
            "received_on": "2026-10-02",
            "observed_on": "2026-10-04",
        },
        {
            "id": "CS-02-UNSUPPORTED-SUBJECT",
            "description": "Warranty question is outside the return-policy subject gate.",
            "subject_covered": False,
            "channel": "online-store",
            "received_on": "2026-10-02",
            "observed_on": "2026-10-04",
        },
        {
            "id": "GAP-BEFORE-RET-V1",
            "description": "Date before all supplied policy intervals has no selected source.",
            "subject_covered": True,
            "channel": "online-store",
            "received_on": "2025-12-31",
            "observed_on": "2026-10-04",
        },
        {
            "id": "FUTURE-RECEIPT-DATE",
            "description": "Receipt date later than observation date fails closed.",
            "subject_covered": True,
            "channel": "online-store",
            "received_on": "2026-10-05",
            "observed_on": "2026-10-04",
        },
    ]
    records = []
    for case in scenarios:
        result = resolve_policy(
            subject_covered=case["subject_covered"],
            channel=case["channel"],
            received_on=case["received_on"],
            observed_on=case["observed_on"],
            policies=policies,
        )
        records.append({"case": case, "router_result": result.as_dict()})

    evidence = {
        "artifact": "synthetic deterministic policy-routing display examples",
        "provenance": "Actual calls to policy_router.resolve_policy; no LLM or customer data.",
        "source_path": "cases.json",
        "source_sha256": sha256(SOURCE),
        "router_path": "policy_router.py",
        "router_sha256": sha256(HERE / "policy_router.py"),
        "generator_path": "capture_examples.py",
        "generator_sha256": sha256(Path(__file__)),
        "scope": "Synthetic RET-V1/RET-V2 intervals only; upstream subject_covered is supplied, not inferred.",
        "records": records,
    }
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} router traces to {OUTPUT.name}")
    print(f"Source SHA-256: {evidence['source_sha256']}")
    print(f"Router SHA-256: {evidence['router_sha256']}")
    for record in records:
        result = record["router_result"]
        print(f"{record['case']['id']}: {result['status']} -> {result['selected_version']}")


if __name__ == "__main__":
    main()
