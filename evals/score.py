"""Phase 0 eval metrics (build plan §14).

Each scorer is a pure function: predictions/artifacts in, score out.
Metrics the scaffold cannot produce yet (no extraction model wired) return
status "n/a" — the scorer signatures exist so future model work plugs in.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from shapely.geometry import Polygon

from prototype import dxf_export, edits
from prototype.schema import CheckResult, Lot, Scheme


# ---- geometry extraction: IoU-based (target ≥ 0.90) -------------------------

def lot_iou(a: List[List[float]], b: List[List[float]]) -> float:
    pa, pb = Polygon(a), Polygon(b)
    union = pa.union(pb).area
    return pa.intersection(pb).area / union if union > 0 else 0.0


def score_geometry_iou(generated: List[Lot], expected: List[List[float]]) -> float:
    """Mean IoU of generated lot polygons vs golden expected (order-matched).

    In the scaffold this is a determinism/regression check: the golden
    expected was snapshotted from the same deterministic engine, so replay
    must reproduce it near-exactly. Future model-based extraction will be
    scored against human-verified expected geometry the same way.
    """
    if not expected or len(generated) != len(expected):
        return 0.0
    ious = [lot_iou(g.polygon, e) for g, e in zip(generated, expected)]
    return sum(ious) / len(ious)


# ---- constraint satisfaction (target 100% on deterministic checks) ----------

def score_constraint_satisfaction(
    validations: Dict[str, List[CheckResult]],
) -> Tuple[float, int, int]:
    """(fraction of checks without 'fail', n_fail, n_total)."""
    all_checks = [c for v in validations.values() for c in v]
    fails = sum(1 for c in all_checks if c.status == "fail")
    total = len(all_checks)
    return ((total - fails) / total if total else 0.0, fails, total)


# ---- native CAD validity: DXF reopen + audit (target 100%) -------------------

def score_dxf_validity(dxf_paths: List[str]) -> Tuple[float, Dict[str, List[str]]]:
    """(fraction of DXFs with zero audit errors, per-file errors)."""
    errors: Dict[str, List[str]] = {}
    for p in dxf_paths:
        errs = dxf_export.audit_dxf(p)
        if errs:
            errors[p] = errs
    ok = len(dxf_paths) - len(errors)
    return (ok / len(dxf_paths) if dxf_paths else 0.0, errors)


# ---- edit safety: risk tiers + tamper detection (0 tolerance) ----------------

def _tiny_scheme() -> Scheme:
    s = Scheme(
        scheme_id="eval-edit-01",
        parcel_id="eval-parcel",
        lots=[
            Lot(lot_id="L00", polygon=[[0, 0], [70, 0], [70, 120], [0, 120], [0, 0]],
                area_sqft=8400.0, frontage_ft=70.0),
        ],
    )
    from prototype.schema import fingerprint_geometry

    s.fingerprint = fingerprint_geometry(s)
    return s


def score_edit_safety() -> Dict[str, bool]:
    """Scripted scenarios; every value must be True."""
    out: Dict[str, bool] = {}

    s = _tiny_scheme()
    ok, _ = edits.apply_edit(s, {"type": "rename_scheme", "new_id": "eval-edit-02"})
    out["low_risk_applied_and_logged"] = ok and any(
        r.get("result") == "applied" for r in s.provenance
    )

    s = _tiny_scheme()
    ok, _ = edits.apply_edit(s, {"type": "regenerate_offset"}, approved=False)
    out["medium_risk_rejected_without_approval"] = (not ok) and any(
        r.get("result") == "rejected" for r in s.provenance
    )

    s = _tiny_scheme()
    ok, _ = edits.apply_edit(s, {"type": "delete_all_lots"})
    out["destructive_blocked"] = (not ok) and len(s.lots) == 1 and any(
        r.get("result") == "blocked" for r in s.provenance
    )

    s = _tiny_scheme()
    s.lots.pop()  # bypass the edit API: unauthorized mutation
    tampered, _ = edits.detect_tamper(s)
    out["unauthorized_mutation_detected"] = tampered

    s = _tiny_scheme()
    tampered, _ = edits.detect_tamper(s)
    out["clean_scheme_not_flagged"] = not tampered
    return out


# ---- model-dependent metrics: stubs awaiting an extraction model --------------

def score_plan_classification(predictions, expected) -> Dict:
    return {"status": "n/a", "reason": "no plan/sheet classifier wired in scaffold"}


def score_titleblock_extraction(predictions, expected) -> Dict:
    return {"status": "n/a", "reason": "no title-block extractor wired in scaffold"}


def score_bearing_transcription(predictions, expected) -> Dict:
    return {"status": "n/a", "reason": "no bearing/distance transcriber wired in scaffold"}
