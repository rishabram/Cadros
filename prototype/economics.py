"""Economics grounding (MarketGraph seed): maps a documented economics file
onto the finance config keys the pipeline expects.

Usage: run.py --economics inputs/economics_slco_2026.json

Mapping (also documented in the economics file's _meta.mapping):
    sale_price_per_lot <- districts[<matched>].finished_lot_revenue.value
    road_cost_per_lf   <- road_cost_per_lf.value
    soft_costs_fixed   <- soft_costs.fixed_planning_value.value
    contingency_pct    <- contingency_pct.value

District matching reads zone_label from the zoning config; an unmatched
label falls back to the DEFAULT district entry and the fallback is recorded
in provenance (never silent). OS/PL districts map to $0 lot revenue with an
explicit warning — they are not privately subdividable.

This module never invents market facts: every figure it consumes must carry
{source, date, confidence} tags (see validate_economics), and confidence
"sourced" vs "assumption" is preserved into the finance config provenance.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, Tuple

CONFIDENCES = ("sourced", "sourced-from-listings", "assumption")

REQUIRED_TOP_LEVEL = ("districts", "road_cost_per_lf", "soft_costs",
                      "contingency_pct")


def load_economics(path: str) -> Dict:
    with open(path) as f:
        econ = json.load(f)
    validate_economics(econ)
    return econ


def _check_tagged(obj: Dict, where: str) -> None:
    """Every figure (dict carrying 'value') must be tagged source/date/confidence."""
    missing = [k for k in ("value", "source", "date", "confidence")
               if k not in obj]
    if missing:
        raise ValueError(
            f"economics file: figure at {where} missing tags: "
            f"{', '.join(missing)} — refusing to price from untagged figures"
        )
    if obj["confidence"] not in CONFIDENCES:
        raise ValueError(
            f"economics file: figure at {where} has invalid confidence "
            f"'{obj['confidence']}' (must be one of {CONFIDENCES})"
        )


def _walk_tagged(obj, where: str = "$") -> None:
    if isinstance(obj, dict):
        if "value" in obj:
            _check_tagged(obj, where)
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            _walk_tagged(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk_tagged(v, f"{where}[{i}]")


def validate_economics(econ: Dict) -> None:
    missing = [k for k in REQUIRED_TOP_LEVEL if k not in econ]
    if missing:
        raise ValueError(
            f"economics file missing required sections: {', '.join(missing)}"
        )
    districts = econ["districts"]
    if "DEFAULT" not in districts:
        raise ValueError(
            "economics file: districts must include a DEFAULT entry for "
            "unmatched zone labels"
        )
    for dkey, dval in districts.items():
        rev = (dval or {}).get("finished_lot_revenue")
        if not isinstance(rev, dict):
            raise ValueError(
                f"economics file: districts.{dkey} missing finished_lot_revenue"
            )
    for skey in ("road_cost_per_lf", "contingency_pct"):
        if not isinstance(econ.get(skey), dict) or "value" not in econ[skey]:
            raise ValueError(
                f"economics file: section '{skey}' must be a tagged figure"
            )
    soft = econ["soft_costs"]
    for skey in ("fixed_planning_value", "pct_of_hard_costs"):
        if not isinstance(soft.get(skey), dict) or "value" not in soft[skey]:
            raise ValueError(
                f"economics file: soft_costs.{skey} must be a tagged figure"
            )
    _walk_tagged(econ)


def _district_token_pattern(dkey: str) -> "re.Pattern":
    # "MU-11" -> r'\bMU[-\s]?11\b'; "M-1" -> r'\bM[-\s]?1\b'; "OS" -> r'\bOS\b'
    core = re.escape(dkey).replace(r"\-", r"[-\s]?")
    return re.compile(r"\b" + core + r"\b")


def match_district(zone_label: str, districts: Dict) -> Tuple[str, bool]:
    """Return (district_key, fallback). Longest/most-specific token wins;
    no token match -> DEFAULT (fallback=True)."""
    label = (zone_label or "").upper()
    candidates = [k for k in districts if k != "DEFAULT"]
    candidates.sort(key=len, reverse=True)
    for dkey in candidates:
        if _district_token_pattern(dkey).search(label):
            return dkey, False
    return "DEFAULT", True


def finance_config_from_economics(econ: Dict, zone_label: str,
                                  econ_path: str = "") -> Dict:
    """Map the economics model onto the finance config keys the pipeline
    expects (sale_price_per_lot, road_cost_per_lf, soft_costs_fixed,
    contingency_pct), with a district->revenue lookup on zone_label."""
    validate_economics(econ)
    districts = econ["districts"]
    dkey, fallback = match_district(zone_label, districts)
    revenue = districts[dkey]["finished_lot_revenue"]

    warnings = []
    if dkey in ("OS", "PL"):
        warnings.append(
            f"district {dkey} is not privately subdividable; "
            "lot revenue set to 0 by the economics model"
        )

    cfg = {
        "sale_price_per_lot": float(revenue["value"]),
        "road_cost_per_lf": float(econ["road_cost_per_lf"]["value"]),
        "soft_costs_fixed": float(econ["soft_costs"]["fixed_planning_value"]["value"]),
        "contingency_pct": float(econ["contingency_pct"]["value"]),
    }
    for k, v in cfg.items():
        if v < 0:
            raise ValueError(
                f"economics file maps to negative {k}: {v} — refusing to price"
            )
    econ_file = os.path.basename(econ_path) if econ_path else "(in-memory)"
    cfg["source"] = (
        f"derived from {econ_file} "
        f"(district={dkey}{', DEFAULT fallback' if fallback else ''}, "
        f"economics build {econ.get('_meta', {}).get('created', 'unknown')}); "
        "per-value sources inside the economics file"
    )
    cfg["economics"] = {
        "economics_file": econ_file,
        "zone_label": zone_label,
        "district_matched": dkey,
        "fallback_to_default": fallback,
        "revenue_confidence": revenue["confidence"],
        "revenue_source": revenue["source"],
        "warnings": warnings,
    }
    return cfg
