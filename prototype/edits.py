"""Edit API with risk tiers + provenance (build plan §7, §14).

Policy (scaffold v0):
  - low-risk (annotation/label): applied immediately, provenance recorded.
  - medium-risk (geometry-affecting, e.g. regenerate with new road offset):
    requires explicit approval; without it the edit is rejected and logged.
  - high-risk / destructive (delete lots, clear scheme): always blocked,
    logged as an unauthorized attempt. 0 tolerance.

Tamper detection: any mutation that bypasses apply_edit changes the
geometry fingerprint; detect_tamper() flags it.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from .schema import Scheme, fingerprint_geometry

LOW_RISK = {"rename_scheme", "set_label"}
MEDIUM_RISK = {"regenerate_offset"}
DESTRUCTIVE = {"delete_all_lots", "clear_scheme"}


def apply_edit(scheme: Scheme, edit: Dict[str, Any], approved: bool = False) -> Tuple[bool, str]:
    """Apply (or refuse) an edit. Returns (applied, message). Always logs."""
    kind = edit.get("type", "")
    record = {
        "type": kind,
        "at": datetime.now(timezone.utc).isoformat(),
        "approved": approved,
    }

    if kind in DESTRUCTIVE:
        record["result"] = "blocked"
        scheme.provenance.append(record)
        return False, f"blocked: destructive edit '{kind}' is never applied automatically"

    if kind in MEDIUM_RISK:
        if not approved:
            record["result"] = "rejected"
            scheme.provenance.append(record)
            return False, f"rejected: '{kind}' needs explicit approval"
        # approved medium-risk edits are handled by the caller regenerating;
        # here we just record the approval decision.
        record["result"] = "approved-not-applied-here"
        scheme.provenance.append(record)
        return True, f"approved: '{kind}' may proceed via regeneration"

    if kind in LOW_RISK:
        if kind == "rename_scheme":
            scheme.scheme_id = str(edit.get("new_id", scheme.scheme_id))
        elif kind == "set_label":
            scheme.params["label"] = str(edit.get("label", ""))
        record["result"] = "applied"
        scheme.provenance.append(record)
        return True, f"applied low-risk edit '{kind}'"

    record["result"] = "rejected"
    scheme.provenance.append(record)
    return False, f"rejected: unknown edit type '{kind}'"


def detect_tamper(scheme: Scheme) -> Tuple[bool, str]:
    """True if geometry was mutated outside apply_edit (fingerprint mismatch).

    A scheme with no recorded baseline fingerprint cannot be verified:
    report unknown rather than claiming "no tamper".
    """
    if not scheme.fingerprint:
        return False, (
            "unknown: no baseline fingerprint recorded — "
            "tamper status cannot be verified"
        )
    current = fingerprint_geometry(scheme)
    if current != scheme.fingerprint:
        return True, (
            f"tamper detected: fingerprint {scheme.fingerprint} != {current}; "
            f"{len(scheme.provenance)} provenance record(s) on file"
        )
    return False, "no tamper: fingerprint matches"


def snapshot(scheme: Scheme) -> Scheme:
    """Deep copy for before/after comparison (render_and_diff hook)."""
    return copy.deepcopy(scheme)
