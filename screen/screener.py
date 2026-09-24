"""NERON mass screener (screening harness).

Config-driven multi-parcel harness around the single-parcel pipeline
(:func:`prototype.pipeline.run_pipeline`). For each parcel in a manifest it
runs the full pipeline into a per-parcel output directory, then aggregates
per-scheme results into one deterministic ``screening_results.csv`` plus a
``summary.json`` / printed summary.

Invariants:
  - Deterministic: manifest order is preserved, float formatting is fixed,
    no randomness anywhere. Two runs of the same manifest produce
    byte-identical CSV/summary.
  - Loud failures: a parcel that errors produces an ``error`` row — it is
    never silently skipped, and it never aborts the rest of the screen.
  - No verdicts are invented: RuleGraph PASS/FAIL/UNKNOWN outcomes are
    propagated verbatim from ``report.json``; UNKNOWNs are carried through
    the CSV, never zeroed or defaulted to compliance.

The parcel-input schema is documented in ``parcels_schema.md`` (same
directory): real GIS parcels plug into the manifest with zero code changes.
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import sys
import time
import traceback
from collections import Counter
from typing import Any, Dict, List, Tuple

CSV_COLUMNS = [
    "parcel_id",
    "zone_label",
    "district",
    "row_kind",        # "scheme" | "no_schemes" | "error"
    "scheme_id",
    "lots",
    "road_ft",
    "revenue",
    "total_cost",
    "profit",
    "margin",
    "rg_verdict",      # scheme-level RuleGraph verdict (canonical vocabulary)
    "rg_pass",         # per-rule outcome counts for the scheme
    "rg_conditional",
    "rg_fail",
    "rg_unknown",
    "rg_manual_review",
    "rg_applicable_rules",  # # of store rules applicable to the scheme's district
    "rg_verdict_basis",     # "evaluated" | "no_applicable_rules" | ""
                            # (qualifier only — the rg_verdict enum never changes)
    "use_verdict",     # scheme-level use-allowance verdict (canonical vocabulary)
    "geometry_clean",  # "true"/"false" (geometric validation only)
    "unknowns_count",  # # of RuleGraph context attributes with no evidence
    "error",
]

# Canonical verdict vocabulary (Caddy's canonical use-checker terms, adopted
# 2026-09-24 for both dimensional and use-allowance verdicts).
VERDICTS = ("PASS", "CONDITIONAL_PASS", "FAIL", "UNKNOWN", "MANUAL_REVIEW")

SUMMARY_FILENAME = "summary.json"
CSV_FILENAME = "screening_results.csv"
CHECKPOINT_FILENAME = "checkpoint.json"


def fmt(v: Any, nd: int) -> str:
    """Deterministic numeric formatting: '' for missing, else fixed decimals."""
    if v is None or v == "":
        return ""
    return repr(round(float(v), nd))


def _load_value(value: Any, base_dir: str) -> Any:
    """A manifest field may be an inline dict/list or a path to a JSON file.

    Relative paths resolve against the manifest file's directory.
    """
    if isinstance(value, str):
        path = value if os.path.isabs(value) else os.path.join(base_dir, value)
        with open(path) as f:
            return json.load(f)
    return value


def _write_json(path: str, obj: Any) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def _rg_outcome_counts(scheme: Dict) -> Tuple[str, Dict[str, int]]:
    """(overall_verdict, per-outcome counts) for a scheme, full vocabulary."""
    verdict = scheme.get("rulegraph_verdict", "")
    results = scheme.get("rulegraph", []) or []
    counts = {v: 0 for v in VERDICTS}
    for r in results:
        o = r.get("outcome")
        if o in counts:
            counts[o] += 1
    return verdict, counts


def _scheme_row(parcel_id: str, zone_label: str, district: str,
                scheme: Dict, unknowns_count: int) -> Dict:
    verdict, counts = _rg_outcome_counts(scheme)
    applicable = scheme.get("rulegraph_applicable_rules", "")
    # Vacuous-PASS qualifier: a PASS with zero applicable rules means no
    # verified rule in the store covered the parcel's district — it is NOT a
    # compliance finding. The verdict enum itself is never relabeled; the
    # distinction rides this separate field.
    if verdict == "PASS" and applicable == 0:
        basis = "no_applicable_rules"
    elif applicable == "":
        basis = ""
    else:
        basis = "evaluated"
    prof = scheme.get("proforma", {}) or {}
    return {
        "parcel_id": parcel_id,
        "zone_label": zone_label,
        "district": district,
        "row_kind": "scheme",
        "scheme_id": scheme.get("scheme_id", ""),
        "lots": scheme.get("lots", ""),
        "road_ft": fmt(scheme.get("road_ft"), 1),
        "revenue": fmt(prof.get("revenue"), 2),
        "total_cost": fmt(prof.get("total_cost"), 2),
        "profit": fmt(prof.get("profit"), 2),
        "margin": fmt(prof.get("margin"), 4),
        "rg_verdict": verdict,
        "rg_pass": counts["PASS"],
        "rg_conditional": counts["CONDITIONAL_PASS"],
        "rg_fail": counts["FAIL"],
        "rg_unknown": counts["UNKNOWN"],
        "rg_manual_review": counts["MANUAL_REVIEW"],
        "rg_applicable_rules": applicable,
        "rg_verdict_basis": basis,
        "use_verdict": scheme.get("use_verdict", ""),
        "geometry_clean": "true" if scheme.get("clean") else "false",
        "unknowns_count": unknowns_count,
        "error": "",
    }


def _blank_row(parcel_id: str, zone_label: str, district: str,
               row_kind: str, error: str = "") -> Dict:
    row = {c: "" for c in CSV_COLUMNS}
    row.update({
        "parcel_id": parcel_id,
        "zone_label": zone_label,
        "district": district,
        "row_kind": row_kind,
        "error": error,
    })
    return row


def screen_manifest(manifest_path: str, out_root: str | None = None,
                    max_schemes: int | None = None,
                    repo_root: str | None = None,
                    checkpoint_interval: int = 10,
                    resume: bool = True) -> Tuple[List[Dict], Dict]:
    """Run every parcel in a manifest; write CSV + summary; return (rows, summary).

    A parcel-level exception is captured as an ``error`` row and the screen
    continues. ``repo_root`` locates the pipeline package (defaults to the
    neron-scratch tree containing this ``screen/`` directory).

    Checkpoint/resume (DW-CHECK1): after every ``checkpoint_interval``
    parcels, the accumulated state is written to
    ``out_root/checkpoint.json``. If the process is killed (SIGTERM/SIGINT),
    the checkpoint survives. On restart with ``resume=True`` (default), the
    checkpoint is loaded and completed parcels are skipped. The checkpoint
    is deleted on successful completion.
    """
    from prototype.pipeline import run_pipeline

    manifest_path = os.path.abspath(manifest_path)
    base_dir = os.path.dirname(manifest_path)
    with open(manifest_path) as f:
        manifest = json.load(f)

    if out_root is None:
        out_root = os.path.join(base_dir, "outputs")
    out_root = os.path.abspath(out_root)
    os.makedirs(out_root, exist_ok=True)

    entries = manifest.get("parcels", [])
    if max_schemes is None:
        max_schemes = int(manifest.get("max_schemes", 8))

    checkpoint_path = os.path.join(out_root, CHECKPOINT_FILENAME)

    def _write_checkpoint(completed_ids, rows, errors, noscheme_diags,
                          top_lots):
        _write_json(checkpoint_path, {
            "manifest_path": manifest_path,
            "completed_parcel_ids": sorted(completed_ids),
            "rows": rows,
            "errors": errors,
            "noscheme_diagnostics": noscheme_diags,
            "top_scheme_lots": top_lots,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })

    def _load_checkpoint():
        with open(checkpoint_path) as f:
            return json.load(f)

    rows: List[Dict] = []
    errors: List[Dict] = []
    noscheme_diagnostics: Dict[str, int] = {}
    top_scheme_lots = 0
    completed_ids = set()
    if resume and os.path.exists(checkpoint_path):
        try:
            cp = _load_checkpoint()
            # Only resume if the checkpoint is for this manifest.
            if os.path.abspath(cp.get("manifest_path", "")) == manifest_path:
                completed_ids = set(cp.get("completed_parcel_ids", []))
                rows = cp.get("rows", [])
                errors = cp.get("errors", [])
                noscheme_diagnostics = cp.get("noscheme_diagnostics", {})
                top_scheme_lots = cp.get("top_scheme_lots", 0)
                print(f"Resuming from checkpoint: {len(completed_ids)} "
                      f"parcels already done, {len(entries) - len(completed_ids)} "
                      f"remaining.")
        except Exception as e:
            print(f"Checkpoint load failed ({e}); starting fresh.")

    for entry in entries:
        parcel_id = entry.get("parcel_id") or "unknown"
        if parcel_id in completed_ids:
            continue
        pdir = os.path.join(out_root, parcel_id)
        inputs_dir = os.path.join(pdir, "inputs")
        os.makedirs(inputs_dir, exist_ok=True)
        zone_label = ""
        district = ""
        try:
            parcel_gj = _load_value(entry.get("parcel_geojson"), base_dir)
            zoning = _load_value(entry.get("zoning_config"), base_dir)
            finance_cfg = _load_value(entry.get("finance_config"), base_dir)
            program = entry.get("program")
            if program is not None:
                program = _load_value(program, base_dir)
            zone_label = str((zoning or {}).get("zone_label", ""))
            district = str((zoning or {}).get("district", ""))

            # Materialize the effective inputs next to the parcel outputs so a
            # screen is fully reproducible from its own directory.
            for name, obj in (("parcel.geojson", parcel_gj),
                              ("zoning.json", zoning),
                              ("finance.json", finance_cfg)):
                _write_json(os.path.join(inputs_dir, name), obj)
            if program is not None:
                _write_json(os.path.join(inputs_dir, "program.json"), program)

            result = run_pipeline(
                os.path.join(inputs_dir, "parcel.geojson"),
                os.path.join(inputs_dir, "zoning.json"),
                os.path.join(inputs_dir, "finance.json"),
                pdir,
                max_schemes=max_schemes,
                building_program=program,
            )
            report = result["report"]
            schemes = report.get("schemes", [])
            unknowns_count = len((report.get("rulegraph") or {}).get("gaps", []))
            gen_verdict = (report.get("scheme_generation") or {}).get("verdict", "?")
            if not schemes:
                rows.append(_blank_row(parcel_id, zone_label, district,
                                       "no_schemes"))
                noscheme_diagnostics[gen_verdict] = \
                    noscheme_diagnostics.get(gen_verdict, 0) + 1
            else:
                top_scheme_lots += int(schemes[0].get("lots", 0) or 0)
                for s in schemes:
                    rows.append(_scheme_row(parcel_id, zone_label, district,
                                            s, unknowns_count))
        except Exception as exc:  # loud, never silent; never aborts the screen
            msg = f"{type(exc).__name__}: {exc}".replace("\n", " ")[:500]
            rows.append(_blank_row(parcel_id, zone_label, district,
                                   "error", error=msg))
            errors.append({"parcel_id": parcel_id, "error": msg,
                           "traceback": traceback.format_exc(limit=5)})
        # Mark completed and checkpoint periodically. A SIGTERM/SIGINT
        # between checkpoints loses at most checkpoint_interval parcels;
        # the checkpoint file itself is the resume point.
        completed_ids.add(parcel_id)
        if len(completed_ids) % checkpoint_interval == 0:
            _write_checkpoint(completed_ids, rows, errors,
                              noscheme_diagnostics, top_scheme_lots)

    # Final checkpoint before writing outputs (covers the tail).
    _write_checkpoint(completed_ids, rows, errors,
                      noscheme_diagnostics, top_scheme_lots)

    csv_path = os.path.join(out_root, CSV_FILENAME)
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    scheme_rows = [r for r in rows if r["row_kind"] == "scheme"]
    screened_ids = {r["parcel_id"] for r in rows
                    if r["row_kind"] in ("scheme", "no_schemes")}
    errored_ids = {r["parcel_id"] for r in rows if r["row_kind"] == "error"}
    noscheme_ids = {r["parcel_id"] for r in rows
                    if r["row_kind"] == "no_schemes"}
    profits = [float(r["profit"]) for r in scheme_rows if r["profit"] != ""]
    margins = [float(r["margin"]) for r in scheme_rows if r["margin"] != ""]
    summary = {
        "screen_name": manifest.get("screen_name", ""),
        "manifest": manifest_path,
        "max_schemes": max_schemes,
        "parcels_in_manifest": len(entries),
        "parcels_screened": len(screened_ids),
        "parcels_errored": len(errored_ids),
        "parcels_no_schemes": len(noscheme_ids),
        "no_schemes_by_diagnostic": dict(sorted(noscheme_diagnostics.items())),
        "scheme_rows": len(scheme_rows),
        "total_lots_top_scheme": top_scheme_lots,
        "profit_mean": round(statistics.fmean(profits), 2) if profits else None,
        "profit_median": (round(statistics.median(profits), 2)
                          if profits else None),
        "margin_mean": (round(statistics.fmean(margins), 4)
                        if margins else None),
        "margin_median": (round(statistics.median(margins), 4)
                          if margins else None),
        "rulegraph_outcomes": {
            v: sum(int(r[col]) for r in scheme_rows)
            for v, col in (
                ("PASS", "rg_pass"),
                ("CONDITIONAL_PASS", "rg_conditional"),
                ("FAIL", "rg_fail"),
                ("UNKNOWN", "rg_unknown"),
                ("MANUAL_REVIEW", "rg_manual_review"),
            )
        },
        "rg_vacuous_pass_schemes": sum(
            1 for r in scheme_rows
            if r["rg_verdict_basis"] == "no_applicable_rules"
        ),
        "rg_verdict_basis_note": (
            "rg_verdict_basis qualifies each scheme row: 'evaluated' means at "
            "least one store rule applied to the scheme's district; "
            "'no_applicable_rules' means the verdict is PASS with zero "
            "applicable rules — no verified rule covered the district, so it "
            "is not a compliance finding. The rg_verdict enum itself is "
            "unchanged."
        ),
        "useallow_outcomes": dict(sorted(Counter(
            r["use_verdict"] for r in scheme_rows if r["use_verdict"]
        ).items())),
        "use_verdict_note": (
            "Use-allowance verdicts are evaluated without a building program "
            "in the mass screen (no --program); most schemes report UNKNOWN "
            "until program facts are supplied. UNKNOWN is never defaulted to "
            "allowed."
        ),
        "csv": csv_path,
        "errors": [{"parcel_id": e["parcel_id"], "error": e["error"]}
                   for e in errors],
        "note": ("Means/medians and outcome counts are over scheme rows only; "
                 "error and no_schemes rows are excluded. UNKNOWN is never "
                 "defaulted to compliance."),
    }
    _write_json(os.path.join(out_root, SUMMARY_FILENAME), summary)
    print(_format_summary(summary))
    # Successful completion: the checkpoint is no longer needed.
    try:
        os.remove(checkpoint_path)
    except OSError:
        pass
    return rows, summary


def _format_summary(s: Dict) -> str:
    lines = [
        f"screen: {s['screen_name']}",
        f"parcels: {s['parcels_in_manifest']} in manifest, "
        f"{s['parcels_screened']} screened, "
        f"{s['parcels_no_schemes']} with no schemes, "
        f"{s['parcels_errored']} errored",
        f"no_schemes by diagnostic: {s.get('no_schemes_by_diagnostic', {})}",
        f"scheme rows: {s['scheme_rows']}; "
        f"total lots (top scheme per parcel): {s['total_lots_top_scheme']}",
        f"profit: mean {s['profit_mean']}, median {s['profit_median']}",
        f"margin: mean {s['margin_mean']}, median {s['margin_median']}",
        f"rulegraph rule outcomes: {s['rulegraph_outcomes']}",
        f"rulegraph vacuous-PASS schemes: "
        f"{s.get('rg_vacuous_pass_schemes', 0)} "
        f"(PASS with no applicable rules — not compliance findings)",
        f"use-allowance scheme verdicts: {s.get('useallow_outcomes', {})}",
        f"csv: {s['csv']}",
    ]
    for e in s["errors"]:
        lines.append(f"  ERROR {e['parcel_id']}: {e['error']}")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="NERON mass screener")
    ap.add_argument("--manifest", required=True,
                    help="path to parcels manifest JSON")
    ap.add_argument("--out", default=None,
                    help="output root (default: <manifest dir>/outputs)")
    ap.add_argument("--max-schemes", type=int, default=None,
                    help="override manifest max_schemes")
    args = ap.parse_args(argv)
    # Ensure the neron-scratch tree (parent of this screen/ package) is
    # importable when run as `python -m screen.screener`.
    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    screen_manifest(args.manifest, out_root=args.out,
                    max_schemes=args.max_schemes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
