"""NERON market optimizer: deterministic parameter sweep over subdividable parcels.

For each parcel that produced schemes in a baseline mass screen, this module
sweeps planning/program parameters around the parcel's manifest (provisional)
dimensionals, evaluates every grid point with the real pipeline
(:func:`prototype.pipeline.run_pipeline` — reused, never forked), and selects
the risk-adjusted-profit-maximizing candidate subject to hard constraints.

OBJECTIVE (risk-adjusted profit)
--------------------------------
    risk_adjusted_profit = profit - k * (unknowns / total_rule_outcomes) * |profit|

with k = K_RISK = 0.1.  Written out for the common profit >= 0 case:

    risk_adjusted_profit = profit * (1 - k * unknowns / total_rule_outcomes)

where ``unknowns`` is the count of RuleGraph rule outcomes that are UNKNOWN
for the candidate's top scheme and ``total_rule_outcomes`` is the count of
all evaluated rule outcomes (PASS + FAIL + UNKNOWN) for that scheme.

Why this form, and why k = 0.1:
  - UNKNOWNs are priced as epistemic risk, never treated as PASS. A candidate
    whose rule outcomes are entirely UNKNOWN is discounted 10%; a candidate
    with fully known outcomes is undiscounted. The penalty is deliberately
    small so genuine profit differences dominate, but large enough that among
    near-equal profits the optimizer prefers candidates with confirmed
    compliance evidence.
  - The |profit| factor (instead of profit) keeps the penalty direction
    correct for money-losing candidates (e.g. OS parcels with $0 lot revenue):
    more UNKNOWNs make a loss *worse*, not better.
  - k = 0.1 is a judgment call, documented here so it can be re-tuned; it is
    a module constant, not buried in code.

HARD CONSTRAINTS (a candidate violating any of these is ineligible)
-------------------------------------------------------------------
  (a) zero RuleGraph FAILs on the candidate's top scheme (rg_fail == 0);
      any candidate with rg_fail > 0 is ineligible, no exceptions;
  (b) geometric clean (the pipeline's ``clean`` flag, geometric validation
      only — RuleGraph verdicts are reported separately and never folded
      into ``clean``);
  (c) economics from inputs/economics_slco_2026.json via
      finance_config_from_economics, using the manifest's district code as
      the zone_label argument. (The manifest's long-form zone_label strings
      do not carry the district token, so passing them would silently fall
      back to DEFAULT revenue; passing the district reproduces the screen's
      own derivation exactly — verified value-for-value during development.)

SELECTION
---------
The candidate's representative is its TOP scheme by profit (the pipeline's
own ranking: highest profit, ties broken by more lots). The parcel's winner
is the eligible candidate with the highest risk-adjusted profit. Ties are
broken deterministically: higher risk-adjusted profit, then higher raw
profit, then fewer UNKNOWNs, then earlier grid order.

SWEEP GRID (documented choices)
-------------------------------
  - min_lot_area_sqft: manifest value x {0.7, 1.0, 1.4}. 0.7x = aggressive
    subdivision (smaller lots, more of them); 1.0x = the screen baseline;
    1.4x = generous lots. Three points bracket the provisional baseline
    without pretending to know the true optimum.
  - min_frontage_ft: manifest value x {0.7, 1.0, 1.4}, same rationale.
  - road_width_ft: manifest value +/- 5 ft (three points). Narrower roads
    free parcel area for lots; wider roads are a variable planners actually
    negotiate. Clamped at >= 20 ft (local-street floor; the pipeline also
    refuses non-positive widths loudly).
  - building_program: 'none' (no program -> honest UNKNOWN baseline, exactly
    reproducing the no-program screen) plus 'draft-lowrise' (a modest
    row-house program sized to PASS the verified MU-11 rules). Districts with
    verified rules in the store that program facts can move (MU-11, PL) also
    get 'draft-tower' (200 ft height), which FAILs MU-11-06/07 and therefore
    exercises the hard FAIL filter. Programs are machine-generated DRAFTS,
    labeled as such; they are hypothetical, not real projects, and never
    carry a human verdict.

INVARIANTS
----------
  - Deterministic: manifest order, fixed grid order, fixed float formatting,
    no timestamps, no absolute paths in outputs. Two runs produce
    byte-identical CSVs.
  - Loud failures: a candidate that errors produces an ineligible sweep row
    with the error text — never a silent skip, never aborting the parcel.
  - No verdicts invented: RuleGraph outcomes are propagated verbatim;
    UNKNOWN never defaults to compliance. This module does not build a
    use-allowance engine and does not touch rulegraph/engine.py.
  - Baselines and goldens untouched: demo/Jefferson inputs, golden_01..03,
    and the v01 scaffold zip are never modified by this module.
  - Provisional dimensionals: the sweep centers on the manifest's
    PROVISIONAL min_frontage_ft / min_lot_area_sqft / road_width_ft. The
    optimizer does not validate them against real code; winners inherit the
    provisional caveat.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
import tempfile
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Grid + objective configuration (documented above)
# ---------------------------------------------------------------------------

K_RISK = 0.1

AREA_MULTS = (0.7, 1.0, 1.4)
FRONTAGE_MULTS = (0.7, 1.0, 1.4)
ROAD_STEP_FT = 5.0
ROAD_MIN_FT = 20.0

# Districts whose verified rules a building program can move (height/setback
# rules live here); only these parcels get the tower (rule-failing) variant.
PROGRAM_SENSITIVE_DISTRICTS = ("MU-11", "PL")

SWEEP_COLUMNS = [
    "parcel_id",
    "district",
    "area_mult",
    "frontage_mult",
    "road_width_ft",
    "program",
    "min_lot_area_sqft",
    "min_frontage_ft",
    "top_scheme_id",
    "lots",
    "profit",
    "margin",
    "rg_pass",
    "rg_fail",
    "rg_unknown",
    "geometry_clean",
    "eligible",
    "ineligible_reason",
    "risk_adjusted_profit",
]

BEST_COLUMNS = [
    "parcel_id",
    "district",
    "win_area_mult",
    "win_frontage_mult",
    "win_road_width_ft",
    "win_program",
    "win_min_lot_area_sqft",
    "win_min_frontage_ft",
    "win_scheme_id",
    "win_lots",
    "win_profit",
    "win_margin",
    "win_rg_pass",
    "win_rg_fail",
    "win_rg_unknown",
    "win_geometry_clean",
    "win_risk_adjusted_profit",
    "baseline_top_profit",
    "baseline_risk_adjusted_profit",
    "uplift_abs",
    "uplift_pct",
    "n_candidates",
    "n_eligible",
]

_DRAFT_NOTE = (
    "DRAFT machine-generated building program for the NERON optimizer sweep "
    "only. NOT a real project — values are hypothetical and unverified. "
    "Never carries a human verdict."
)


def _draft_lowrise() -> Dict:
    """A modest row-house program sized to PASS the verified MU-11 rules."""
    return {
        "_note": _DRAFT_NOTE,
        "building_form": "row_house",
        "stories": [
            {"level": 0, "use": "live_work"},
            {"level": 1, "use": "residential"},
            {"level": 2, "use": "residential"},
        ],
        "height_ft": 40,
        "design_review_completed": False,
        "front_setback_ft": 12,
        "front_street": "400 South",
        "corner_side_setback_ft": 6,
        "corner_street": "500 East",
        "interior_side_setback_ft": 10,
        "interior_abuts_listed_zone": False,
        "rear_setback_ft": 20,
        "rear_abuts_listed_zone": False,
        "lot_abuts_sf_tf_residential": False,
    }


def _draft_tower() -> Dict:
    """Same envelope as draft-lowrise but 200 ft: FAILs MU-11-06/07 (150 ft
    bonus maximum), so these candidates must be filtered by the hard
    zero-FAIL constraint."""
    prog = _draft_lowrise()
    prog["height_ft"] = 200
    prog["design_review_completed"] = True
    return prog


def program_variants(district: str) -> List[Tuple[str, Optional[Dict]]]:
    """Ordered (name, program) variants for a parcel's district.

    'none' is always first: the honest UNKNOWN baseline that reproduces the
    no-program screen. The tower (rule-failing) variant is included only for
    districts with verified rules a program can move.
    """
    variants: List[Tuple[str, Optional[Dict]]] = [
        ("none", None),
        ("draft-lowrise", _draft_lowrise()),
    ]
    if district in PROGRAM_SENSITIVE_DISTRICTS:
        variants.append(("draft-tower", _draft_tower()))
    return variants


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def fmt(v: Any, nd: int) -> str:
    """Deterministic numeric formatting: '' for missing, else fixed decimals."""
    if v is None or v == "":
        return ""
    return repr(round(float(v), nd))


def _write_json(path: str, obj: Any) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def _load_value(value: Any, base_dir: str) -> Any:
    """A manifest field may be an inline dict/list or a path to a JSON file."""
    if isinstance(value, str):
        path = value if os.path.isabs(value) else os.path.join(base_dir, value)
        with open(path) as f:
            return json.load(f)
    return value


def risk_adjusted_profit(
    profit: float,
    unknowns: int,
    total_outcomes: int,
    k: float = K_RISK,
) -> float:
    """Risk-adjusted profit (see module docstring for the full rationale).

    penalty = k * (unknowns / total_outcomes) * |profit|; result = profit - penalty.
    UNKNOWNs strictly decrease the objective for any nonzero profit, so more
    UNKNOWNs can never win on the objective, all else equal.
    """
    if total_outcomes <= 0:
        return float(profit)
    penalty = k * (unknowns / total_outcomes) * abs(float(profit))
    return float(profit) - penalty


def _rg_counts(scheme: Dict) -> Tuple[int, int, int]:
    """(pass, fail, unknown) per-rule outcome counts for one scheme."""
    counts = {"PASS": 0, "FAIL": 0, "UNKNOWN": 0}
    for r in scheme.get("rulegraph", []) or []:
        o = r.get("outcome")
        if o in counts:
            counts[o] += 1
    return counts["PASS"], counts["FAIL"], counts["UNKNOWN"]


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

def grid_points(zoning: Dict) -> List[Dict]:
    """The 27 dimensional grid points around a parcel's manifest dimensionals.

    Returns dicts with area_mult, frontage_mult, road_width_ft,
    min_lot_area_sqft, min_frontage_ft, in fixed nested-loop order.
    """
    base_area = float(zoning["min_lot_area_sqft"])
    base_front = float(zoning["min_frontage_ft"])
    base_road = float(zoning["road_width_ft"])
    roads = sorted({
        round(max(base_road - ROAD_STEP_FT, ROAD_MIN_FT), 1),
        round(base_road, 1),
        round(base_road + ROAD_STEP_FT, 1),
    })
    points = []
    for am in AREA_MULTS:
        for fm in FRONTAGE_MULTS:
            for rw in roads:
                points.append({
                    "area_mult": am,
                    "frontage_mult": fm,
                    "road_width_ft": rw,
                    "min_lot_area_sqft": round(base_area * am, 2),
                    "min_frontage_ft": round(base_front * fm, 2),
                })
    return points


# ---------------------------------------------------------------------------
# Candidate evaluation
# ---------------------------------------------------------------------------

def evaluate_candidate(
    parcel_id: str,
    parcel_geojson: Any,
    zoning: Dict,
    finance_cfg: Dict,
    program_name: str,
    program: Optional[Dict],
    grid_pt: Dict,
    scratch_dir: str,
    max_schemes: int,
) -> Dict:
    """Run one grid point through the real pipeline; return a sweep row.

    The row's top scheme is the pipeline's ranked #1 (highest profit, ties by
    more lots). A pipeline exception becomes an ineligible row carrying the
    error text — loud, never a silent skip.
    """
    from prototype.pipeline import run_pipeline

    cand_dir = os.path.join(
        scratch_dir,
        f"a{grid_pt['area_mult']}_f{grid_pt['frontage_mult']}"
        f"_r{grid_pt['road_width_ft']}_{program_name}",
    )
    os.makedirs(cand_dir, exist_ok=True)
    cand_zoning = dict(zoning)
    cand_zoning["min_lot_area_sqft"] = grid_pt["min_lot_area_sqft"]
    cand_zoning["min_frontage_ft"] = grid_pt["min_frontage_ft"]
    cand_zoning["road_width_ft"] = grid_pt["road_width_ft"]

    row = {
        "parcel_id": parcel_id,
        "district": str(zoning.get("district", "")),
        "area_mult": fmt(grid_pt["area_mult"], 2),
        "frontage_mult": fmt(grid_pt["frontage_mult"], 2),
        "road_width_ft": fmt(grid_pt["road_width_ft"], 1),
        "program": program_name,
        "min_lot_area_sqft": fmt(grid_pt["min_lot_area_sqft"], 2),
        "min_frontage_ft": fmt(grid_pt["min_frontage_ft"], 2),
    }
    try:
        _write_json(os.path.join(cand_dir, "parcel.geojson"), parcel_geojson)
        _write_json(os.path.join(cand_dir, "zoning.json"), cand_zoning)
        _write_json(os.path.join(cand_dir, "finance.json"), finance_cfg)
        if program is not None:
            _write_json(os.path.join(cand_dir, "program.json"), program)
        result = run_pipeline(
            os.path.join(cand_dir, "parcel.geojson"),
            os.path.join(cand_dir, "zoning.json"),
            os.path.join(cand_dir, "finance.json"),
            os.path.join(cand_dir, "out"),
            max_schemes=max_schemes,
            building_program=program,
        )
        schemes = result["report"].get("schemes", [])
        if not schemes:
            row.update({
                "top_scheme_id": "", "lots": "", "profit": "",
                "margin": "", "rg_pass": 0, "rg_fail": 0, "rg_unknown": 0,
                "geometry_clean": "false",
                "eligible": "false",
                "ineligible_reason": "no schemes generated",
                "risk_adjusted_profit": "",
            })
            return row
        top = schemes[0]  # pipeline ranking: highest profit, ties by more lots
        p, f, u = _rg_counts(top)
        total = p + f + u
        profit = float(top["proforma"]["profit"])
        clean = bool(top.get("clean"))
        if f > 0:
            eligible, reason = False, f"rg_fail > 0 ({f} rule FAILs)"
        elif not clean:
            eligible, reason = False, "geometry not clean"
        else:
            eligible, reason = True, ""
        row.update({
            "top_scheme_id": top.get("scheme_id", ""),
            "lots": top.get("lots", ""),
            "profit": fmt(profit, 2),
            "margin": fmt(top["proforma"].get("margin"), 4),
            "rg_pass": p,
            "rg_fail": f,
            "rg_unknown": u,
            "geometry_clean": "true" if clean else "false",
            "eligible": "true" if eligible else "false",
            "ineligible_reason": reason,
            "risk_adjusted_profit": (
                fmt(risk_adjusted_profit(profit, u, total), 2)
                if eligible else ""
            ),
        })
    except Exception as exc:  # loud, never silent; never aborts the parcel
        msg = f"{type(exc).__name__}: {exc}".replace("\n", " ")[:500]
        row.update({
            "top_scheme_id": "", "lots": "", "profit": "",
            "margin": "", "rg_pass": 0, "rg_fail": 0, "rg_unknown": 0,
            "geometry_clean": "false",
            "eligible": "false",
            "ineligible_reason": f"pipeline error: {msg}",
            "risk_adjusted_profit": "",
        })
    return row


def pick_winner(sweep_rows: List[Dict]) -> Optional[Dict]:
    """The eligible row with the highest risk-adjusted profit.

    Deterministic tiebreak: higher risk-adjusted, then higher raw profit,
    then fewer UNKNOWNs, then earlier grid order.
    """
    best = None
    best_key = None
    for idx, r in enumerate(sweep_rows):
        if r["eligible"] != "true":
            continue
        key = (
            -float(r["risk_adjusted_profit"]),
            -float(r["profit"]),
            int(r["rg_unknown"]),
            idx,
        )
        if best_key is None or key < best_key:
            best_key = key
            best = r
    return best


# ---------------------------------------------------------------------------
# Baseline loading
# ---------------------------------------------------------------------------

def load_baseline(baseline_csv: str) -> Dict[str, Dict]:
    """Per-parcel baseline from the real screen: the top scheme row per parcel.

    The screen writes schemes in ranked (profit-descending) order per parcel,
    so the first scheme row per parcel is its top scheme. Returns
    {parcel_id: {profit, rg_pass, rg_fail, rg_unknown, district}}.
    """
    baseline: Dict[str, Dict] = {}
    with open(baseline_csv, newline="") as f:
        for r in csv.DictReader(f):
            if r["row_kind"] != "scheme":
                continue
            pid = r["parcel_id"]
            if pid in baseline:
                continue  # first scheme row per parcel = ranked top
            baseline[pid] = {
                "profit": float(r["profit"]) if r["profit"] != "" else 0.0,
                "rg_pass": int(r["rg_pass"] or 0),
                "rg_fail": int(r["rg_fail"] or 0),
                "rg_unknown": int(r["rg_unknown"] or 0),
                "district": r["district"],
            }
    return baseline


# ---------------------------------------------------------------------------
# Parcel + manifest optimization
# ---------------------------------------------------------------------------

def optimize_parcel(
    entry: Dict,
    base_dir: str,
    finance_cfg: Dict,
    max_schemes: int,
    program_order: Optional[List[Tuple[str, Optional[Dict]]]] = None,
) -> Tuple[List[Dict], Dict]:
    """Sweep one parcel; return (sweep_rows, winner_row_or_empty)."""
    parcel_id = entry.get("parcel_id") or "unknown"
    parcel_geojson = _load_value(entry.get("parcel_geojson"), base_dir)
    zoning = _load_value(entry.get("zoning_config"), base_dir)
    district = str(zoning.get("district", ""))
    variants = (program_order if program_order is not None
                else program_variants(district))
    points = grid_points(zoning)

    sweep_rows: List[Dict] = []
    with tempfile.TemporaryDirectory(prefix=f"neron_opt_{parcel_id}_") as tmp:
        for pt in points:
            for prog_name, prog in variants:
                sweep_rows.append(evaluate_candidate(
                    parcel_id, parcel_geojson, zoning, finance_cfg,
                    prog_name, prog, pt, tmp, max_schemes,
                ))
    return sweep_rows, (pick_winner(sweep_rows) or {})


def optimize_manifest(
    manifest_path: str,
    baseline_csv: str,
    economics_path: str,
    out_dir: str,
    max_schemes: int = 8,
) -> Tuple[List[Dict], List[Dict], Dict]:
    """Run the full optimization; write sweep.csv, best.csv, summary.json."""
    from prototype.economics import (
        finance_config_from_economics,
        load_economics,
    )

    t0 = time.time()
    manifest_path = os.path.abspath(manifest_path)
    base_dir = os.path.dirname(manifest_path)
    with open(manifest_path) as f:
        manifest = json.load(f)
    entries = manifest.get("parcels", [])
    econ = load_economics(economics_path)
    baseline = load_baseline(baseline_csv)

    # Only parcels that produced schemes in the baseline screen.
    targets = [e for e in entries
               if (e.get("parcel_id") or "unknown") in baseline]
    missing = [pid for pid in baseline
               if pid not in {e.get("parcel_id") for e in entries}]
    if missing:
        raise ValueError(
            f"baseline parcels missing from manifest: {missing[:10]}"
        )

    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    sweep_all: List[Dict] = []
    best_rows: List[Dict] = []
    uplift_abs_list: List[float] = []
    uplift_pct_list: List[float] = []
    improved = unchanged = worse_or_ineligible = 0
    win_params: Dict[str, List[str]] = {
        "area_mult": [], "frontage_mult": [], "road_width_ft": [],
        "program": [],
    }
    baseline_repro_mismatch: List[Dict] = []
    total_candidates = 0
    total_eligible = 0

    for entry in targets:
        parcel_id = entry.get("parcel_id") or "unknown"
        zoning = _load_value(entry.get("zoning_config"), base_dir)
        district = str(zoning.get("district", ""))
        finance_cfg = finance_config_from_economics(
            econ, district, economics_path
        )
        sweep_rows, winner = optimize_parcel(
            entry, base_dir, finance_cfg, max_schemes
        )
        sweep_all.extend(sweep_rows)
        total_candidates += len(sweep_rows)
        total_eligible += sum(1 for r in sweep_rows
                             if r["eligible"] == "true")

        b = baseline[parcel_id]
        b_total = b["rg_pass"] + b["rg_fail"] + b["rg_unknown"]
        b_risk_adj = risk_adjusted_profit(b["profit"], b["rg_unknown"], b_total)

        # Integrity check: the (1.0, 1.0, manifest road, none) grid point must
        # reproduce the baseline screen's top-scheme profit exactly.
        base_pt = next(
            (r for r in sweep_rows
             if r["area_mult"] == fmt(1.0, 2)
             and r["frontage_mult"] == fmt(1.0, 2)
             and r["road_width_ft"] == fmt(float(zoning["road_width_ft"]), 1)
             and r["program"] == "none"),
            None,
        )
        if base_pt is None:
            baseline_repro_mismatch.append(
                {"parcel_id": parcel_id, "issue": "baseline grid point missing"})
        elif base_pt["profit"] == "":
            baseline_repro_mismatch.append(
                {"parcel_id": parcel_id,
                 "issue": f"baseline grid point not evaluated: "
                          f"{base_pt['ineligible_reason']}"})
        elif round(float(base_pt["profit"]), 2) != round(b["profit"], 2):
            baseline_repro_mismatch.append(
                {"parcel_id": parcel_id,
                 "issue": f"profit mismatch: sweep {base_pt['profit']} vs "
                          f"baseline {b['profit']}"})

        best = {
            "parcel_id": parcel_id,
            "district": district,
            "baseline_top_profit": fmt(b["profit"], 2),
            "baseline_risk_adjusted_profit": fmt(b_risk_adj, 2),
            "n_candidates": len(sweep_rows),
            "n_eligible": sum(1 for r in sweep_rows
                              if r["eligible"] == "true"),
        }
        if winner:
            w_risk = float(winner["risk_adjusted_profit"])
            uplift_abs = w_risk - b_risk_adj
            uplift_pct = (uplift_abs / abs(b_risk_adj)
                          if abs(b_risk_adj) > 1e-9 else None)
            best.update({
                "win_area_mult": winner["area_mult"],
                "win_frontage_mult": winner["frontage_mult"],
                "win_road_width_ft": winner["road_width_ft"],
                "win_program": winner["program"],
                "win_min_lot_area_sqft": winner["min_lot_area_sqft"],
                "win_min_frontage_ft": winner["min_frontage_ft"],
                "win_scheme_id": winner["top_scheme_id"],
                "win_lots": winner["lots"],
                "win_profit": winner["profit"],
                "win_margin": winner["margin"],
                "win_rg_pass": winner["rg_pass"],
                "win_rg_fail": winner["rg_fail"],
                "win_rg_unknown": winner["rg_unknown"],
                "win_geometry_clean": winner["geometry_clean"],
                "win_risk_adjusted_profit": fmt(w_risk, 2),
                "uplift_abs": fmt(uplift_abs, 2),
                "uplift_pct": (fmt(uplift_pct, 4)
                               if uplift_pct is not None else ""),
            })
            uplift_abs_list.append(uplift_abs)
            if uplift_pct is not None:
                uplift_pct_list.append(uplift_pct)
            if uplift_abs > 1e-6:
                improved += 1
            elif uplift_abs < -1e-6:
                worse_or_ineligible += 1
            else:
                unchanged += 1
            for k in win_params:
                win_params[k].append(str(winner[
                    {"area_mult": "area_mult",
                     "frontage_mult": "frontage_mult",
                     "road_width_ft": "road_width_ft",
                     "program": "program"}[k]]))
        else:
            worse_or_ineligible += 1
            for c in BEST_COLUMNS:
                if c not in best:
                    best[c] = ""
        best_rows.append(best)

    def _mode(vals: List[str]) -> Optional[str]:
        if not vals:
            return None
        counts: Dict[str, int] = {}
        for v in vals:
            counts[v] = counts.get(v, 0) + 1
        top_count = max(counts.values())
        # deterministic: first value in winner order among the modes
        for v in vals:
            if counts[v] == top_count:
                return v
        return None  # pragma: no cover

    # Road-width wins are most informative as deltas from the manifest value.
    road_deltas = []
    for entry, best in zip(targets, best_rows):
        if best.get("win_road_width_ft"):
            zoning = _load_value(entry.get("zoning_config"), base_dir)
            road_deltas.append(fmt(
                float(best["win_road_width_ft"])
                - float(zoning["road_width_ft"]), 1))

    summary = {
        "optimizer": "screen/optimizer.py opt_v1",
        "manifest": manifest_path,
        "baseline_csv": os.path.abspath(baseline_csv),
        "economics": os.path.abspath(economics_path),
        "max_schemes": max_schemes,
        "objective": {
            "formula": ("risk_adjusted_profit = profit - k * "
                        "(unknowns / total_rule_outcomes) * |profit|"),
            "k": K_RISK,
            "k_rationale": ("k=0.1 discounts a fully-UNKNOWN candidate 10%: "
                            "UNKNOWNs are priced as epistemic risk, never "
                            "treated as PASS; genuine profit differences "
                            "still dominate."),
            "unknowns_definition": ("rg_unknown count on the candidate's top "
                                    "scheme; total_rule_outcomes = "
                                    "rg_pass + rg_fail + rg_unknown."),
            "eligibility": ("rg_fail == 0 AND geometry_clean AND >= 1 "
                            "scheme AND no pipeline error."),
            "tiebreak": ("higher risk-adjusted, then higher raw profit, "
                         "then fewer UNKNOWNs, then earlier grid order."),
        },
        "grid": {
            "area_mult": list(AREA_MULTS),
            "frontage_mult": list(FRONTAGE_MULTS),
            "road_width_ft": "manifest value +/- 5 ft, floor 20 ft",
            "programs": ("none (honest UNKNOWN baseline), draft-lowrise "
                         "(DRAFT, sized to PASS MU-11 rules); draft-tower "
                         "(DRAFT, 200 ft, FAILs MU-11-06/07) only for MU-11/PL"),
            "note": ("Grid centers on the manifest's PROVISIONAL dimensionals; "
                     "winners inherit the provisional caveat."),
        },
        "parcels_optimized": len(targets),
        "total_candidates": total_candidates,
        "total_eligible": total_eligible,
        "parcels_improved": improved,
        "parcels_unchanged": unchanged,
        "parcels_worse_or_ineligible": worse_or_ineligible,
        "uplift_abs": {
            "mean": (round(statistics.fmean(uplift_abs_list), 2)
                     if uplift_abs_list else None),
            "median": (round(statistics.median(uplift_abs_list), 2)
                       if uplift_abs_list else None),
        },
        "uplift_pct": {
            "mean": (round(statistics.fmean(uplift_pct_list), 4)
                     if uplift_pct_list else None),
            "median": (round(statistics.median(uplift_pct_list), 4)
                       if uplift_pct_list else None),
        },
        "most_common_winning_params": {
            "area_mult": _mode(win_params["area_mult"]),
            "frontage_mult": _mode(win_params["frontage_mult"]),
            "road_width_delta_ft": _mode(road_deltas),
            "program": _mode(win_params["program"]),
        },
        "baseline_reproduction": {
            "checked": len(targets),
            "mismatched": baseline_repro_mismatch,
        },
        "runtime_sec": round(time.time() - t0, 1),
        "note": ("All artifacts are machine-generated DRAFTS. No human "
                 "verdicts invented or implied. UNKNOWN never defaults to "
                 "compliance. demo/Jefferson inputs, goldens, and the v01 "
                 "scaffold zip were not touched."),
    }

    sweep_path = os.path.join(out_dir, "sweep.csv")
    with open(sweep_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SWEEP_COLUMNS,
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(sweep_all)
    best_path = os.path.join(out_dir, "best.csv")
    with open(best_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=BEST_COLUMNS,
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(best_rows)
    summary_path = os.path.join(out_dir, "summary.json")
    _write_json(summary_path, summary)

    print(_format_summary(summary))
    return sweep_all, best_rows, summary


def _format_summary(s: Dict) -> str:
    lines = [
        f"optimizer: {s['optimizer']}",
        f"parcels optimized: {s['parcels_optimized']}; "
        f"candidates: {s['total_candidates']} "
        f"({s['total_eligible']} eligible)",
        f"parcels improved: {s['parcels_improved']}, unchanged: "
        f"{s['parcels_unchanged']}, worse-or-ineligible: "
        f"{s['parcels_worse_or_ineligible']}",
        f"uplift_abs: mean {s['uplift_abs']['mean']}, "
        f"median {s['uplift_abs']['median']}",
        f"uplift_pct: mean {s['uplift_pct']['mean']}, "
        f"median {s['uplift_pct']['median']}",
        f"most common winning params: {s['most_common_winning_params']}",
        f"baseline reproduction mismatches: "
        f"{len(s['baseline_reproduction']['mismatched'])}",
        f"runtime: {s['runtime_sec']}s",
    ]
    for m in s["baseline_reproduction"]["mismatched"]:
        lines.append(f"  REPRO MISMATCH {m['parcel_id']}: {m['issue']}")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="NERON market optimizer")
    ap.add_argument("--manifest", required=True,
                    help="parcels manifest JSON (e.g. screen/real_manifest.json)")
    ap.add_argument("--baseline-csv", required=True,
                    help="baseline screening_results.csv")
    ap.add_argument("--economics", required=True,
                    help="economics JSON (e.g. inputs/economics_slco_2026.json)")
    ap.add_argument("--out", required=True,
                    help="output dir (sweep.csv, best.csv, summary.json)")
    ap.add_argument("--max-schemes", type=int, default=8)
    args = ap.parse_args(argv)
    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    optimize_manifest(args.manifest, args.baseline_csv, args.economics,
                      args.out, max_schemes=args.max_schemes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
