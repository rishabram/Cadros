#!/usr/bin/env python3
"""30-parcel benchmark harness for the NERON parcel-feasibility pipeline.

=====================================================================
MACHINE-DRAFT EVALUATION — NOT HUMAN VERIFICATION
=====================================================================
This harness performs pipeline-geometry evaluation ONLY: it re-runs
``prototype.pipeline.run_pipeline`` on a stratified sample of parcels
and machine-reads the outputs for geometric / arithmetic / verdict-
consistency failure modes. It produces NO zoning-rule verdicts and
implies none: no VERIFIED / CORRECTED / REJECTED labels appear anywhere
in this file or its outputs. All machine-produced artifacts are labeled
draft / provisional. UNKNOWN is never defaulted to compliance.

Determinism: the sample list is fixed-order and hand-stratified
(selection seed 20260923; ties broken by parcel_id). Every output is
written with sorted keys / sorted rows and contains no timestamps or
absolute paths, so two runs of this harness on the same inputs produce
byte-identical ``failure_table.md`` and ``findings.json``.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from prototype.pipeline import run_pipeline  # noqa: E402
from screen.screener import _load_value, _write_json  # noqa: E402

try:
    from shapely.geometry import Polygon  # noqa: E402
except ImportError:  # pragma: no cover
    Polygon = None

BANNER = (
    "=====================================================================\n"
    "MACHINE-DRAFT EVALUATION — NOT HUMAN VERIFICATION\n"
    "=====================================================================\n"
    "This artifact was produced by an automated benchmark harness. It is\n"
    "pipeline-geometry evaluation ONLY (scheme geometry, pro-forma\n"
    "arithmetic, verdict consistency). It contains NO zoning-rule\n"
    "verification and implies NO human verdicts (no VERIFIED / CORRECTED /\n"
    "REJECTED anywhere). UNKNOWN is never defaulted to compliance. All\n"
    "dimensional minimums used here are PROVISIONAL mass-screen v1\n"
    "assumptions except where the record says otherwise.\n"
    "====================================================================="
)

SELECTION_SEED = 20260923

# ---------------------------------------------------------------------------
# Stratified sample (fixed order = strata order). Each entry carries the
# stratification rationale for auditability.
# ---------------------------------------------------------------------------
SAMPLE: List[Dict[str, str]] = [
    # -- Stratum A: top-profit winners (screen ranking, top 8 by scheme_00 profit)
    {"parcel_id": "08214000240000", "rationale": "A: #1 profit $7.36M (M-1, 18 lots); flagship winner re-check"},
    {"parcel_id": "08253510440000", "rationale": "A: #2 profit $6.01M (M-1); winner re-check"},
    {"parcel_id": "08251510020000", "rationale": "A: #3 profit $3.58M (M-2, 95.03 ac mega-parcel); winner + scale edge"},
    {"parcel_id": "08253280010000", "rationale": "A: #4 profit $3.50M (M-1); winner re-check"},
    {"parcel_id": "08243000240000", "rationale": "A: #5 profit $3.50M (M-1); winner re-check"},
    {"parcel_id": "08253510430000", "rationale": "A: #6 profit $3.11M (M-1); winner re-check"},
    {"parcel_id": "08252000080000", "rationale": "A: #7 profit $2.58M (EI, 29.89 ac); winner + EI district scheme coverage"},
    {"parcel_id": "08253260190000", "rationale": "A: #8 profit $2.55M (M-1); winner re-check"},
    # -- Stratum B: no_schemes on large parcels that look subdividable
    {"parcel_id": "08234570150000", "rationale": "B: no_schemes, M-2, 14.28 ac (area fits ~31 min-lots); largest no_schemes in screen"},
    {"parcel_id": "08252780010000", "rationale": "B: no_schemes, FR-2, 9.6 ac (area fits ~9.6 min-lots); FR-2 district coverage"},
    {"parcel_id": "08235010060000", "rationale": "B: no_schemes, M-2, 6.07 ac (area fits ~13 min-lots); elongated 3.3 aspect"},
    {"parcel_id": "08233510040000", "rationale": "B: no_schemes, OS, 3.02 ac (area fits ~6.6 min-lots)"},
    {"parcel_id": "08251760200000", "rationale": "B: no_schemes, M-1, 2.97 ac (area fits ~6.5 min-lots), near-square aspect 1.2"},
    {"parcel_id": "08253260200000", "rationale": "B: no_schemes, M-1, 2.61 ac (area fits ~5.7 min-lots)"},
    {"parcel_id": "08243000210000", "rationale": "B: no_schemes, EI, 2.10 ac (area fits ~4.6 min-lots), near-square aspect 1.1"},
    # -- Stratum C: district coverage (districts with no scheme parcels in the screen)
    {"parcel_id": "08223520380000", "rationale": "C: R-1-7000 coverage (largest R-1-7000, 0.34 ac); all 159 R-1-7000 parcels are no_schemes"},
    {"parcel_id": "08223810250000", "rationale": "C: R-1-7000 second case (0.32 ac); checks the all-no_schemes district pattern"},
    {"parcel_id": "08223810880000", "rationale": "C: R-1-5000 coverage (largest R-1-5000, 0.25 ac); all R-1-5000 no_schemes"},
    {"parcel_id": "08254260060000", "rationale": "C: FR-3 coverage (largest FR-3, 1.21 ac); all FR-3 no_schemes"},
    # -- Stratum D: edge cases
    {"parcel_id": "08253290080000", "rationale": "D: MU-11 edge case; sole MU-11 parcel, 48 screen UNKNOWNs (program-dependent rules, no program supplied)"},
    {"parcel_id": "08244000050000", "rationale": "D: OS parcel that produced schemes; LARGEST parcel in screen (199.12 ac)"},
    {"parcel_id": "08253780310000", "rationale": "D: SMALLEST parcel in screen (26.1 sqft, MU-5); degenerate-geometry edge"},
    {"parcel_id": "08253780300000", "rationale": "D: 2nd-smallest parcel (48.0 sqft, MU-5); degenerate-geometry edge"},
    {"parcel_id": "08223810760000", "rationale": "D: RMF-30 coverage; sole RMF-30 parcel in screen, produced schemes"},
    # -- Stratum E: scheme parcels from remaining districts (MU-5, BP, M-2, EI)
    {"parcel_id": "08251770050000", "rationale": "E: MU-5 scheme parcel (largest MU-5 with schemes, 2.3 ac)"},
    {"parcel_id": "08253300130000", "rationale": "E: MU-5 no_schemes (largest MU-5 without schemes, 0.63 ac); intra-district contrast"},
    {"parcel_id": "08253290060000", "rationale": "E: BP coverage; sole BP scheme parcel (3.41 ac)"},
    {"parcel_id": "08253260180000", "rationale": "E: M-2 scheme parcel (20.02 ac); 2nd M-2 scheme case"},
    {"parcel_id": "08243000200000", "rationale": "E: EI scheme parcel (23.88 ac); 2nd EI scheme case"},
    {"parcel_id": "08235030120000", "rationale": "E: M-2 scheme parcel (11.32 ac); 3rd M-2 scheme case"},
]

SEVERITY_WEIGHT = {"high": 3, "med": 2, "low": 1}

MODE_SEVERITY: Dict[str, Tuple[str, str]] = {
    # mode: (severity, one-line justification)
    "no_schemes_large_subdividable": (
        "high",
        "Generator silently yields nothing where conforming lots clearly fit — "
        "direct revenue/feasibility miss, no diagnostic emitted.",
    ),
    "rerun_status_mismatch": (
        "high",
        "Re-run disagrees with the published screen row for the same parcel — "
        "breaks reproducibility of the screen artifact.",
    ),
    "profit_arithmetic_mismatch": (
        "high",
        "revenue - total_cost != profit — the ranked number users act on is wrong.",
    ),
    "lots_exceed_parcel_area": (
        "high",
        "Scheme lots cannot all meet min area inside the parcel — physically impossible scheme.",
    ),
    "zero_lot_scheme": (
        "high",
        "Ranked scheme with 0 lots — degenerate generator output.",
    ),
    "rulegraph_fail_outcome": (
        "high",
        "A RuleGraph rule returned FAIL on a ranked scheme — a compliance "
        "blocker the screen totals hid.",
    ),
    "rulegraph_unknown_scope_bug": (
        "high",
        "UNKNOWN verdict with zero applicable rules — district scoping is broken, not merely uninformative.",
    ),
    "margin_arithmetic_mismatch": (
        "med",
        "margin != profit/revenue — derived metric inconsistent with its own inputs.",
    ),
    "margin_out_of_range": (
        "med",
        "Margin outside [-0.5, 0.97] — implausible pro forma (near-free development or catastrophic loss).",
    ),
    "geometry_not_clean": (
        "med",
        "Scheme ranked despite failing geometric validation — validation works, but unclean schemes are still presented.",
    ),
    "ranked_order_not_profit_sorted": (
        "med",
        "Ranked order is not profit-descending — the 'top scheme' may not be the best.",
    ),
    "lot_count_inconsistent": (
        "med",
        "Scheme lots != proforma lot_count — geometry and finance disagree on what was built.",
    ),
    "validation_detail_mismatch": (
        "med",
        "Validation detail lot-count disagrees with scheme lots — check text is stale or miscounted.",
    ),
    "rulegraph_pass_zero_applicable": (
        "med",
        "Verdict PASS with zero applicable rules evaluated — reads as compliance confirmation but no rule fired.",
    ),
    "road_ft_zero_multi_lots": (
        "low",
        "Multiple lots with road_ft = 0 — only valid if lots front an existing street, which the model never verifies.",
    ),
    "all_schemes_identical": (
        "low",
        "All ranked schemes identical on (lots, road_ft, profit) — ranking over a degenerate set.",
    ),
}


# ---------------------------------------------------------------------------
# Parcel geometry facts (machine-read from the same boundary the pipeline used)
# ---------------------------------------------------------------------------

def parcel_geom_facts(parcel_geojson: Dict) -> Dict[str, float]:
    gj = parcel_geojson
    if gj.get("type") == "Feature":
        coords = gj["geometry"]["coordinates"][0]
    else:
        coords = gj["coordinates"][0]
    if Polygon is None:  # pragma: no cover
        raise RuntimeError("shapely is required for benchmark geometry facts")
    poly = Polygon(coords)
    minx, miny, maxx, maxy = poly.bounds
    w, h = maxx - minx, maxy - miny
    return {
        "area_sqft": float(poly.area),
        "perimeter_ft": float(poly.length),
        "bbox_w_ft": float(w),
        "bbox_h_ft": float(h),
        "aspect_ratio": float(max(w, h) / max(min(w, h), 1e-9)),
    }


# ---------------------------------------------------------------------------
# Failure-mode checks. Each returns a list of finding dicts:
# {"parcel_id", "scheme_id" (or None), "mode", "severity", "detail"}.
# Severity/justification live in MODE_SEVERITY (single source of truth).
# ---------------------------------------------------------------------------

def _finding(parcel_id: str, mode: str, detail: str,
             scheme_id: Optional[str] = None) -> Dict[str, Any]:
    severity, _ = MODE_SEVERITY[mode]
    return {
        "parcel_id": parcel_id,
        "scheme_id": scheme_id,
        "mode": mode,
        "severity": severity,
        "detail": detail,
    }


def check_no_schemes_large(parcel_id: str, report: Dict, geom: Dict,
                           zoning: Dict) -> List[Dict]:
    if report.get("status") != "no_schemes_generated":
        return []
    min_area = float(zoning.get("min_lot_area_sqft", 0) or 0)
    if min_area <= 0:
        return []
    ratio = geom["area_sqft"] / min_area
    if ratio >= 2.0:
        gen = report.get("scheme_generation") or {}
        if gen:
            diag_txt = (
                "generator diagnostic: verdict={} (top blocking reason: {}; "
                "area fits {:.1f}x min_lot_area)".format(
                    gen.get("verdict", "?"),
                    gen.get("top_blocking_reason", "?"),
                    gen.get("area_min_lot_ratio", ratio),
                )
            )
        else:
            diag_txt = "generator emitted no diagnostic (legacy report)"
        return [_finding(
            parcel_id, "no_schemes_large_subdividable",
            f"no_schemes but parcel area {geom['area_sqft']:.0f} sqft "
            f"({geom['area_sqft']/43560:.2f} ac) fits {ratio:.1f}x the "
            f"min_lot_area ({min_area:.0f} sqft); bbox "
            f"{geom['bbox_w_ft']:.0f}x{geom['bbox_h_ft']:.0f} ft, aspect "
            f"{geom['aspect_ratio']:.1f}; district "
            f"{zoning.get('district','?')}; {diag_txt}",
        )]
    return []


def check_rerun_status(parcel_id: str, report: Dict,
                       original_row_kind: Optional[str]) -> List[Dict]:
    if original_row_kind is None:
        return []
    status = report.get("status")
    rerun_kind = {"ok": "scheme", "no_schemes_generated": "no_schemes"}.get(status, "error")
    if rerun_kind != original_row_kind:
        return [_finding(
            parcel_id, "rerun_status_mismatch",
            f"original screen row_kind={original_row_kind} but re-run status="
            f"{status} (rerun_kind={rerun_kind}); screen artifact not reproducible",
        )]
    return []


def _schemes(report: Dict) -> List[Dict]:
    return report.get("schemes", []) or []


def check_scheme_level(parcel_id: str, report: Dict, geom: Dict,
                       zoning: Dict) -> List[Dict]:
    findings: List[Dict] = []
    min_area = float(zoning.get("min_lot_area_sqft", 0) or 0)
    for s in _schemes(report):
        sid = s.get("scheme_id")
        lots = int(s.get("lots", 0) or 0)
        road_ft = float(s.get("road_ft", 0) or 0)
        pf = s.get("proforma", {}) or {}

        if lots == 0:
            findings.append(_finding(
                parcel_id, "zero_lot_scheme",
                f"{sid}: ranked scheme has 0 lots", scheme_id=sid))

        if min_area > 0 and lots * min_area > geom["area_sqft"]:
            findings.append(_finding(
                parcel_id, "lots_exceed_parcel_area",
                f"{sid}: {lots} lots x min_area {min_area:.0f} = "
                f"{lots*min_area:.0f} sqft > parcel area "
                f"{geom['area_sqft']:.0f} sqft; lots cannot all meet minimums",
                scheme_id=sid))

        revenue = float(pf.get("revenue", 0) or 0)
        total_cost = float(pf.get("total_cost", 0) or 0)
        profit = float(pf.get("profit", 0) or 0)
        margin = pf.get("margin")
        if abs((revenue - total_cost) - profit) > 1.0:
            findings.append(_finding(
                parcel_id, "profit_arithmetic_mismatch",
                f"{sid}: revenue {revenue:.2f} - total_cost {total_cost:.2f} = "
                f"{revenue-total_cost:.2f} != profit {profit:.2f}",
                scheme_id=sid))
        if margin is not None and revenue > 0:
            margin = float(margin)
            if abs(margin - profit / revenue) > 1e-4:
                findings.append(_finding(
                    parcel_id, "margin_arithmetic_mismatch",
                    f"{sid}: margin {margin:.4f} != profit/revenue "
                    f"{profit/revenue:.4f}", scheme_id=sid))
            if margin < -0.5 or margin > 0.97:
                findings.append(_finding(
                    parcel_id, "margin_out_of_range",
                    f"{sid}: margin {margin:.4f} outside [-0.5, 0.97]; "
                    f"profit {profit:.2f} on revenue {revenue:.2f}",
                    scheme_id=sid))

        if road_ft == 0 and lots >= 2:
            findings.append(_finding(
                parcel_id, "road_ft_zero_multi_lots",
                f"{sid}: {lots} lots with road_ft = 0; no internal road modeled",
                scheme_id=sid))

        lot_count_pf = pf.get("lot_count")
        if lot_count_pf is not None and int(lot_count_pf) != lots:
            findings.append(_finding(
                parcel_id, "lot_count_inconsistent",
                f"{sid}: scheme lots={lots} but proforma lot_count={lot_count_pf}",
                scheme_id=sid))

        if not s.get("clean", True):
            failed = [(c.get("rule_id", "?"), str(c.get("detail", ""))[:160])
                      for c in (s.get("validation") or [])
                      if c.get("status") != "pass"]
            failed_txt = ("; ".join(f"{rid}: {det}" for rid, det in failed)
                          if failed else "unspecified checks")
            findings.append(_finding(
                parcel_id, "geometry_not_clean",
                f"{sid}: ranked despite failing geometric validation: "
                f"{failed_txt}",
                scheme_id=sid))

        m = re.search(r"(\d+)\s*/\s*(\d+)\s+lots meet min area",
                      " ".join(str(c.get("detail", "")) for c in (s.get("validation") or [])))
        if m and int(m.group(2)) != lots:
            findings.append(_finding(
                parcel_id, "validation_detail_mismatch",
                f"{sid}: validation says '{m.group(0)}' but scheme has {lots} lots",
                scheme_id=sid))

        # RuleGraph verdict consistency
        results = s.get("rulegraph", []) or []
        applicable = [r for r in results if r.get("applicable")]
        verdict = s.get("rulegraph_verdict")
        if any(r.get("outcome") == "FAIL" for r in results):
            bad = [r.get("rule_id") for r in results if r.get("outcome") == "FAIL"]
            findings.append(_finding(
                parcel_id, "rulegraph_fail_outcome",
                f"{sid}: RuleGraph rule(s) FAIL on a ranked scheme: "
                f"{', '.join(bad)}", scheme_id=sid))
        if verdict == "PASS" and len(applicable) == 0:
            findings.append(_finding(
                parcel_id, "rulegraph_pass_zero_applicable",
                f"{sid}: rg verdict PASS but 0 of {len(results)} rules were "
                f"applicable (all district-scoped out); no rule actually evaluated",
                scheme_id=sid))
        if verdict == "UNKNOWN" and len(applicable) == 0:
            findings.append(_finding(
                parcel_id, "rulegraph_unknown_scope_bug",
                f"{sid}: rg verdict UNKNOWN with 0 applicable rules; "
                f"district scoping should have passed these through",
                scheme_id=sid))
    return findings


def check_ranking(parcel_id: str, report: Dict) -> List[Dict]:
    schemes = _schemes(report)
    if len(schemes) < 2:
        return []
    sigs = sorted({(int(s.get("lots", 0) or 0),
                    round(float(s.get("road_ft", 0) or 0), 1),
                    round(float((s.get("proforma", {}) or {}).get("profit", 0) or 0), 2))
                   for s in schemes})
    findings: List[Dict] = []
    if len(sigs) == 1:
        findings.append(_finding(
            parcel_id, "all_schemes_identical",
            f"all {len(schemes)} ranked schemes identical on "
            f"(lots, road_ft, profit) = {sigs[0]}"))
    order = report.get("ranked_order", []) or []
    by_id = {s.get("scheme_id"): s for s in schemes}
    profits = [float((by_id[sid].get("proforma", {}) or {}).get("profit", 0) or 0)
               for sid in order if sid in by_id]
    if any(b > a for a, b in zip(profits, profits[1:])):
        findings.append(_finding(
            parcel_id, "ranked_order_not_profit_sorted",
            f"ranked_order profits not non-increasing: "
            f"{[round(p, 2) for p in profits]}"))
    return findings


def analyze_parcel(parcel_id: str, report: Dict, parcel_geojson: Dict,
                   zoning: Dict,
                   original_row_kind: Optional[str]) -> List[Dict]:
    geom = parcel_geom_facts(parcel_geojson)
    findings: List[Dict] = []
    findings += check_no_schemes_large(parcel_id, report, geom, zoning)
    findings += check_rerun_status(parcel_id, report, original_row_kind)
    findings += check_scheme_level(parcel_id, report, geom, zoning)
    findings += check_ranking(parcel_id, report)
    findings.sort(key=lambda f: (f["mode"], f["parcel_id"], f["scheme_id"] or ""))
    return findings


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _load_screen_kinds(csv_path: Optional[str]) -> Dict[str, str]:
    if not csv_path or not os.path.exists(csv_path):
        return {}
    kinds: Dict[str, str] = {}
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            kinds.setdefault(row["parcel_id"], row["row_kind"])
    return kinds


def _materialize_inputs(entry: Dict, base_dir: str, pdir: str) -> Tuple[str, str, str, Any]:
    inputs_dir = os.path.join(pdir, "inputs")
    os.makedirs(inputs_dir, exist_ok=True)
    parcel_gj = _load_value(entry.get("parcel_geojson"), base_dir)
    zoning = _load_value(entry.get("zoning_config"), base_dir)
    finance_cfg = _load_value(entry.get("finance_config"), base_dir)
    program = entry.get("program")
    if program is not None:
        program = _load_value(program, base_dir)
    paths = {}
    for name, obj in (("parcel.geojson", parcel_gj),
                      ("zoning.json", zoning),
                      ("finance.json", finance_cfg)):
        p = os.path.join(inputs_dir, name)
        _write_json(p, obj)
        paths[name] = p
    if program is not None:
        pp = os.path.join(inputs_dir, "program.json")
        _write_json(pp, program)
    else:
        pp = None
    return paths["parcel.geojson"], paths["zoning.json"], paths["finance.json"], pp, \
        parcel_gj, zoning


def _group_findings(fs: List[Dict]) -> List[Dict]:
    """Collapse per-scheme duplicate findings into one line per parcel+detail.

    Deterministic: input order is the (mode, parcel_id, scheme_id) sort, and
    scheme ids are re-sorted on output.
    """
    groups: Dict[Tuple[str, str], Dict[str, Any]] = {}
    order: List[Tuple[str, str]] = []
    for f in fs:
        det = f["detail"]
        sid = f.get("scheme_id")
        m = re.match(r"^(scheme_\d+): (.*)$", det, re.DOTALL)
        if m and sid and m.group(1) == sid:
            key = (f["parcel_id"], m.group(2))
            label: Optional[str] = sid
        else:
            key = (f["parcel_id"], det)
            label = None
        if key not in groups:
            groups[key] = {"parcel_id": f["parcel_id"], "detail": key[1],
                           "schemes": []}
            order.append(key)
        if label and label not in groups[key]["schemes"]:
            groups[key]["schemes"].append(label)
    return [groups[k] for k in order]


def build_failure_table(findings: List[Dict], sample_meta: List[Dict]) -> str:
    lines: List[str] = [BANNER, ""]
    lines.append("# 30-Parcel Benchmark — Failure-Frequency Table (geometry-improvement backlog)")
    lines.append("")
    lines.append(f"Parcels evaluated: {len(sample_meta)}. "
                 f"Parcels with >=1 finding: "
                 f"{len({f['parcel_id'] for f in findings})}. "
                 f"Clean parcels: "
                 f"{len(sample_meta) - len({f['parcel_id'] for f in findings})}.")
    lines.append("")
    lines.append("Priority = severity_weight(high=3, med=2, low=1) x parcels-affected, "
                 "ties broken by severity then mode name. Severity carries a one-line "
                 "justification per mode; see the table.")
    lines.append("")

    by_mode: Dict[str, List[Dict]] = {}
    for f in findings:
        by_mode.setdefault(f["mode"], []).append(f)

    rows = []
    for mode, fs in by_mode.items():
        parcels = sorted({f["parcel_id"] for f in fs})
        severity, why = MODE_SEVERITY[mode]
        priority = SEVERITY_WEIGHT[severity] * len(parcels)
        rows.append((priority, SEVERITY_WEIGHT[severity], mode, severity, why,
                     len(parcels), parcels))
    rows.sort(key=lambda r: (-r[0], -r[1], r[2]))

    lines.append("| rank | failure mode | parcels | severity | priority | examples |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for i, (priority, _w, mode, severity, why, n, parcels) in enumerate(rows, 1):
        ex = ", ".join(parcels[:5]) + (f" (+{len(parcels)-5} more)" if len(parcels) > 5 else "")
        lines.append(f"| {i} | `{mode}` | {n} | {severity} | {priority} | {ex} |")
    lines.append("")

    for i, (priority, _w, mode, severity, why, n, parcels) in enumerate(rows, 1):
        lines.append(f"## {i}. `{mode}` — {severity} (priority {priority}, {n} parcels)")
        lines.append("")
        lines.append(f"Why this severity: {why}")
        lines.append("")
        mode_fs = sorted(by_mode[mode],
                         key=lambda f: (f["parcel_id"], f["scheme_id"] or ""))
        for g in _group_findings(mode_fs):
            sids = sorted(g["schemes"])
            if len(sids) > 1:
                lines.append(f"- {g['parcel_id']} ({len(sids)} schemes: "
                             f"{', '.join(sids)}): {g['detail']}")
            elif len(sids) == 1:
                lines.append(f"- {g['parcel_id']} [{sids[0]}]: {g['detail']}")
            else:
                lines.append(f"- {g['parcel_id']}: {g['detail']}")
        lines.append("")

    if not rows:
        lines.append("No failure modes fired on this sample.")
        lines.append("")

    clean = [m["parcel_id"] for m in sample_meta
             if m["parcel_id"] not in {f["parcel_id"] for f in findings}]
    lines.append("## Clean parcels (no findings)")
    lines.append("")
    lines.append(f"{len(clean)} of {len(sample_meta)} sampled parcels showed no issues: "
                 + (", ".join(sorted(clean)) if clean else "none"))
    lines.append("")
    lines.append(BANNER)
    lines.append("")
    return "\n".join(lines)


def run_benchmark(manifest_path: str, out_dir: str,
                  sample_ids: Optional[List[str]] = None,
                  screen_csv_path: Optional[str] = None) -> Dict[str, Any]:
    """Run the benchmark harness.

    manifest_path: mass-screen manifest (parcel_geojson may be path or inline).
    out_dir:      harness output root (sample.json, findings.json, failure_table.md,
                  runs/<parcel_id>/...).
    sample_ids:   parcel ids to evaluate; defaults to the 30-parcel SAMPLE.
    screen_csv_path: optional published screen CSV for the re-run-vs-screen
                     reproducibility check.
    """
    manifest_path = os.path.abspath(manifest_path)
    base_dir = os.path.dirname(manifest_path)
    with open(manifest_path) as f:
        manifest = json.load(f)
    entries = {e.get("parcel_id"): e for e in manifest.get("parcels", [])}
    max_schemes = int(manifest.get("max_schemes", 8))
    original_kinds = _load_screen_kinds(screen_csv_path)

    if sample_ids is None:
        sample_spec = SAMPLE
    else:
        sample_spec = [
            next((s for s in SAMPLE if s["parcel_id"] == pid),
                 {"parcel_id": pid,
                  "rationale": "test fixture parcel (not in 30-parcel stratification)"})
            for pid in sample_ids
        ]

    out_dir = os.path.abspath(out_dir)
    runs_dir = os.path.join(out_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)

    sample_meta: List[Dict] = []
    all_findings: List[Dict] = []

    for spec in sample_spec:
        pid = spec["parcel_id"]
        entry = entries.get(pid)
        if entry is None:
            raise ValueError(f"sample parcel {pid} not found in manifest {manifest_path}")
        pdir = os.path.join(runs_dir, pid)
        os.makedirs(pdir, exist_ok=True)
        (parcel_p, zoning_p, finance_p, program_p,
         parcel_gj, zoning) = _materialize_inputs(entry, base_dir, pdir)
        program = None
        if program_p:
            with open(program_p) as f:
                program = json.load(f)
        result = run_pipeline(parcel_p, zoning_p, finance_p, pdir,
                              max_schemes=max_schemes,
                              building_program=program)
        report = result["report"]
        findings = analyze_parcel(pid, report, parcel_gj, zoning,
                                  original_kinds.get(pid))
        all_findings.extend(findings)
        status = report.get("status")
        rerun_kind = {"ok": "scheme",
                      "no_schemes_generated": "no_schemes"}.get(status, "error")
        sample_meta.append({
            "parcel_id": pid,
            "district": str((zoning or {}).get("district", "")),
            "rationale": spec["rationale"],
            "original_row_kind": original_kinds.get(pid),
            "rerun_status": rerun_kind,
            "n_schemes": len(report.get("schemes", []) or []),
            "n_findings": len(findings),
        })

    all_findings.sort(key=lambda f: (f["mode"], f["parcel_id"], f["scheme_id"] or ""))

    sample_doc = {
        "_banner": "MACHINE-DRAFT sample list for pipeline-geometry evaluation; "
                   "not human verification. See screen/benchmark.py SAMPLE.",
        "selection_seed": SELECTION_SEED,
        "selection": ("hand-stratified deterministic list, fixed order in "
                      "screen/benchmark.py SAMPLE; ties broken by parcel_id"),
        "n": len(sample_meta),
        "parcels": sample_meta,
    }
    with open(os.path.join(out_dir, "sample.json"), "w") as f:
        json.dump(sample_doc, f, indent=2, sort_keys=True)
        f.write("\n")

    with open(os.path.join(out_dir, "findings.json"), "w") as f:
        json.dump({"_banner": "MACHINE-DRAFT findings; not human verification.",
                   "findings": all_findings}, f, indent=2, sort_keys=True)
        f.write("\n")

    table = build_failure_table(all_findings, sample_meta)
    with open(os.path.join(out_dir, "failure_table.md"), "w") as f:
        f.write(table)

    return {
        "n_parcels": len(sample_meta),
        "n_findings": len(all_findings),
        "n_parcels_with_findings": len({f["parcel_id"] for f in all_findings}),
        "n_clean": len(sample_meta) - len({f["parcel_id"] for f in all_findings}),
        "out_dir": out_dir,
    }


def main() -> None:
    manifest = os.path.join(REPO_ROOT, "screen", "real_manifest.json")
    out_dir = os.path.join(REPO_ROOT, "screen", "outputs", "benchmark_30")
    screen_csv = os.path.join(REPO_ROOT, "screen", "outputs", "real_slco_v1",
                              "screening_results.csv")
    summary = run_benchmark(manifest, out_dir, screen_csv_path=screen_csv)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
