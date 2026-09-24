"""Use-allowance verdict engine.

Evaluates proposed uses against a human-verified use pack (UseRows for the
M-1, OS, and PL districts, from SLC 21A.33.040/.070).

DESIGN DECISION (canonical vocabulary, per Rishab 2026-09-24): the verdict
set is {PASS, CONDITIONAL_PASS, FAIL, UNKNOWN, MANUAL_REVIEW}, matching
Caddy's use-checker vocabulary. Mapping from pack statuses: permitted ->
PASS, conditional -> CONDITIONAL_PASS, blank cell ("not permitted") ->
FAIL (a known code fact; mapping it to UNKNOWN would be dishonest),
unresolved -> UNKNOWN, qualifying-provision footnote -> MANUAL_REVIEW.
Nothing is ever defaulted to allowed: PASS requires a verified "permitted"
row, and UNKNOWN outranks both CONDITIONAL_PASS and PASS in aggregation.
UNKNOWN never passes.

Gate: every row executes through the same human_authorization gate as
RuleGraph (imported from rulegraph.engine) — a row without a human verdict
(result in {VERIFIED, CORRECTED} plus a named verifier and a date) cannot
authorize a verdict; it yields UNKNOWN. Rows whose status is "unresolved"
(e.g. M1-U-28 check cashing, OS-U-27 reception center) can therefore never
evaluate to a use allowance — their flags explain why.

Matching is case- and whitespace-insensitive on use names. Multiple pack
rows for one use take the MOST RESTRICTIVE verdict
(FAIL > UNKNOWN > MANUAL_REVIEW > CONDITIONAL_PASS > PASS); the reason
notes the tie.
"""
from __future__ import annotations

from typing import Dict, List

from rulegraph.engine import human_authorization

USE_DISTRICTS = ("M-1", "OS", "PL", "MU-5", "MU-6", "MU-11")

# Most restrictive wins: FAIL > UNKNOWN > MANUAL_REVIEW >
# CONDITIONAL_PASS > PASS. MANUAL_REVIEW sits between UNKNOWN and
# CONDITIONAL_PASS: a provision the machine cannot confirm outranks a
# known conditional allowance, but UNKNOWN (no basis at all) still
# outranks it.
_SEVERITY = {
    "FAIL": 4,
    "UNKNOWN": 3,
    "MANUAL_REVIEW": 2,
    "CONDITIONAL_PASS": 1,
    "PASS": 0,
}


def _norm(name) -> str:
    return (name or "").strip().lower()


def _hv_of(row) -> Dict:
    hv = row.human_verification
    return hv if isinstance(hv, dict) else {}


def _unknown_entry(use, rule_id, reason, row=None) -> Dict:
    hv = _hv_of(row) if row is not None else {}
    return {
        "use": use,
        "verdict": "UNKNOWN",
        "rule_id": rule_id,
        "reason": reason,
        "verified_by": hv.get("verified_by"),
        "verified_on": hv.get("verified_on"),
    }


def _evaluate_row(district: str, row) -> tuple:
    """Evaluate one pack row. Returns (verdict, reason)."""
    ok, gate_reason = human_authorization(
        {"human_verification": row.human_verification}
    )
    if not ok:
        return "UNKNOWN", (
            f"row {row.rule_id} is not human-verified; cannot execute"
        )
    marking = row.marking or ""
    provenance = row.provenance or ""
    if row.status == "unresolved":
        return "UNKNOWN", (row.flags or f"row {row.rule_id} status unresolved")
    if row.status == "not_permitted":
        return "FAIL", (
            f"blank cell — not permitted in {district} ({marking})"
        )
    if row.footnotes:
        return "MANUAL_REVIEW", (
            f"qualifying provision footnote(s) {list(row.footnotes)} — "
            "provision text not retrieved; requires manual review"
        )
    if row.status == "permitted":
        return "PASS", f"permitted ({marking}; {provenance})"
    if row.status == "conditional":
        return "CONDITIONAL_PASS", f"conditional ({marking}; {provenance})"
    # Defensive: the pack contract names only the four statuses above.
    return "UNKNOWN", (
        f"row {row.rule_id} has unrecognized status {row.status!r}; cannot execute"
    )


def _evaluate_use(district: str, use: str, rows: List) -> Dict:
    """Evaluate one proposed use against the district's pack rows."""
    key = _norm(use)
    candidates = [
        r for r in rows if r.district == district and _norm(r.use_name) == key
    ]
    if not candidates:
        return _unknown_entry(use, None, "no verified row for this use")
    evaluated = [(row, *_evaluate_row(district, row)) for row in candidates]
    # Most restrictive wins; ties keep pack order (deterministic).
    best = max(evaluated, key=lambda t: _SEVERITY[t[1]])
    row, verdict, reason = best
    hv = _hv_of(row)
    entry = {
        "use": use,
        "verdict": verdict,
        "rule_id": row.rule_id,
        "reason": reason,
        "verified_by": hv.get("verified_by"),
        "verified_on": hv.get("verified_on"),
    }
    if len(candidates) > 1:
        ids = ", ".join(r.rule_id for r in candidates)
        entry["reason"] = (
            f"most restrictive of {len(candidates)} candidate rows ({ids}): {reason}"
        )
    return entry


def evaluate_uses(
    district: str | None, proposed_uses: list | None, pack
) -> Dict:
    """Evaluate proposed uses against the pack.

    Returns {"verdict", "per_use", "applicable_rows", "note"}.
    verdict in {"PASS","CONDITIONAL_PASS","FAIL","UNKNOWN","MANUAL_REVIEW"};
    per_use is a list of
    {"use","verdict","rule_id","reason","verified_by","verified_on"}.
    """
    rows = getattr(pack, "rows", None) or []
    applicable_rows = sum(1 for r in rows if r.district == district)

    # Order matters: a run with no proposed uses reports "no proposed uses"
    # even when the district is also missing (the common no-program case) —
    # the actionable gap is the missing use list, not the district.
    if not proposed_uses:
        return {
            "verdict": "UNKNOWN",
            "per_use": [],
            "applicable_rows": applicable_rows,
            "note": "no proposed uses in program; use allowance cannot be evaluated",
        }

    if district is None or district not in USE_DISTRICTS:
        return {
            "verdict": "UNKNOWN",
            "per_use": [],
            "applicable_rows": applicable_rows,
            "note": (
                f"no use rows for district '{district}' "
                "(pack covers M-1/OS/PL/MU-5/MU-6/MU-11)"
            ),
        }

    per_use = [_evaluate_use(district, use, rows) for use in proposed_uses]
    verdicts = [p["verdict"] for p in per_use]
    if "FAIL" in verdicts:
        verdict = "FAIL"
    elif "UNKNOWN" in verdicts:
        verdict = "UNKNOWN"
    elif "MANUAL_REVIEW" in verdicts:
        verdict = "MANUAL_REVIEW"
    elif "CONDITIONAL_PASS" in verdicts:
        verdict = "CONDITIONAL_PASS"
    else:
        verdict = "PASS"

    return {
        "verdict": verdict,
        "per_use": per_use,
        "applicable_rows": applicable_rows,
        "note": (
            f"{len(per_use)} proposed use(s) evaluated in district {district} "
            f"against {applicable_rows} district row(s)"
        ),
    }
