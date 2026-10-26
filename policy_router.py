"""Deterministic policy-version preflight for the synthetic RET-V1/RET-V2 policy set.

This component resolves applicability only. It does not calculate request
eligibility from duration clauses, draft customer language, or perform actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Decision:
    status: str
    selected_version: str | None
    source_ids: tuple[str, ...]
    missing_fields: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_ids"] = list(self.source_ids)
        value["missing_fields"] = list(self.missing_fields)
        return value


def _as_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be an ISO YYYY-MM-DD string")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO YYYY-MM-DD string") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field_name} must be canonical YYYY-MM-DD")
    return parsed


def resolve_policy(
    *,
    subject_covered: bool,
    channel: Any,
    received_on: Any,
    observed_on: Any,
    policies: list[dict[str, Any]],
) -> Decision:
    """Select one policy by trusted subject gate, channel, and validity dates.

    `subject_covered` is an upstream, explicit gate. This function does not
    infer semantic intent from free text. All date intervals are
    applies_from-inclusive and applies_before-exclusive.
    """
    if subject_covered is not True:
        return Decision("subject_not_covered", None, (), (), "No policy selection: subject gate is false.")
    if not isinstance(channel, str) or not channel.strip():
        return Decision("channel_missing", None, (), ("channel",), "Channel is missing or invalid.")

    matching_channel = [policy for policy in policies if policy.get("scope") == channel]
    if not matching_channel:
        return Decision("channel_unsupported", None, (), (), "No policy covers this channel.")
    if received_on is None:
        return Decision("receipt_date_missing", None, (), ("received_on",), "Receipt date is absent.")
    receipt_date = _as_date(received_on, "received_on")
    observed_date = _as_date(observed_on, "observed_on")
    if receipt_date > observed_date:
        return Decision("receipt_date_in_future", None, (), (), "Receipt date is later than the observation date.")

    matches: list[str] = []
    for policy in matching_channel:
        start = _as_date(policy["applies_to_received_from"], "applies_to_received_from")
        end_raw = policy.get("applies_to_received_before")
        end = _as_date(end_raw, "applies_to_received_before") if end_raw is not None else None
        if receipt_date >= start and (end is None or receipt_date < end):
            matches.append(policy["source_id"])

    if len(matches) > 1:
        raise ValueError(f"Overlapping policy intervals for receipt date: {matches}")
    if not matches:
        return Decision("no_valid_policy", None, (), (), "Receipt date is outside all policy validity intervals.")
    selected = matches[0]
    return Decision("selected", selected, (selected,), (), "Exactly one channel and date interval matches.")
