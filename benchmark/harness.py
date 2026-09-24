#!/usr/bin/env python3
"""Approved-plat benchmark harness (Phase B).

For each plat in plats.json with zoning.status == "known" and scored == true:
  parent polygon -> NERON prototype pipeline -> top-ranked scheme lot count
  -> compare vs approved lot count (primary metric: within +/-15%).

Plats with unknown zoning are NOT scored; they are recorded with their reason.
Nothing is invented: a missing zoning source is a gap, never a fill.

Outputs (deterministic, no wall-clock timestamps):
  benchmark/results.json   per-plat results + aggregate
  benchmark/results.md     human-readable summary
  benchmark/runs/<plat_id>/  pipeline outputs per scored plat

Usage:
  python3 harness.py            # run scored set (currently may be empty)
  python3 harness.py --selftest # mechanics check: Mill parent polygon with the
                                # synthetic demo zoning; NOT a benchmark result.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.dirname(BASE)
sys.path.insert(0, SCRATCH)

from prototype import pipeline as pipe_mod  # noqa: E402

TOLERANCE = 0.15  # +/-15% lot-count tolerance (pre-registered)
FINANCE_PATH = os.path.join(SCRATCH, "inputs", "finance.json")
DEMO_ZONING_PATH = os.path.join(SCRATCH, "inputs", "zoning.json")


def load_plats():
    with open(os.path.join(BASE, "plats.json")) as f:
        return json.load(f)["plats"]


def run_one(entry, zoning: dict, out_dir: str) -> dict:
    poly_path = os.path.join(BASE, entry["parent_polygon"])
    with open(poly_path) as f:
        gj = json.load(f)
    boundary = [list(map(float, pt)) for pt in gj["geometry"]["coordinates"][0]]
    props = gj.get("properties", {})
    parcel_id = props.get("parcel_id", entry["plat_id"])
    with open(FINANCE_PATH) as f:
        finance_cfg = json.load(f)
    os.makedirs(out_dir, exist_ok=True)
    result = pipe_mod.run_pipeline_objects(
        parcel_id, boundary, props, zoning, finance_cfg, out_dir, max_schemes=8
    )
    ranked = result["ranked"]
    schemes = [
        {"scheme_id": s.scheme_id, "lots": len(s.lots)} for s in ranked
    ]
    top_lots = len(ranked[0].lots)
    approved = entry["approved_lots"]
    rel_err = abs(top_lots - approved) / approved if approved else None
    return {
        "plat_id": entry["plat_id"],
        "approved_lots": approved,
        "neron_top_ranked_lots": top_lots,
        "schemes": schemes,
        "relative_error": round(rel_err, 4) if rel_err is not None else None,
        "within_15pct": (rel_err <= TOLERANCE) if rel_err is not None else False,
        "zoning_source": zoning.get("source"),
    }


def write_results(results):
    scored = [r for r in results if r["status"] == "scored"]
    n = len(scored)
    n_pass = sum(1 for r in scored if r["within_15pct"])
    payload = {
        "tolerance": TOLERANCE,
        "aim": ">=70% of scored plats within +/-15% (base: 10 plats; stretch: 20)",
        "scored_plats": n,
        "within_tolerance": n_pass,
        "pass_rate": round(n_pass / n, 4) if n else None,
        "aim_met": (n_pass / n >= 0.70) if n else False,
        "results": results,
    }
    with open(os.path.join(BASE, "results.json"), "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    lines = [
        "# Approved-plat benchmark results",
        "",
        f"Tolerance: +/-{TOLERANCE:.0%}. Aim: >=70% of scored plats within tolerance.",
        f"Scored plats: {n}. Within tolerance: {n_pass}.",
        "",
        "| plat_id | approved | neron (top-ranked) | rel err | within 15% | zoning source |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        if r["status"] == "scored":
            lines.append(
                f"| {r['plat_id']} | {r['approved_lots']} | {r['neron_top_ranked_lots']} | "
                f"{r['relative_error']:.1%} | {'YES' if r['within_15pct'] else 'no'} | {r['zoning_source']} |"
            )
        else:
            lines.append(
                f"| {r['plat_id']} | {r.get('approved_lots', '?')} | — | — | not scored: {r['reason']} | — |"
            )
    lines += [""]
    # Hand-written research narrative lives in results_narrative.md so that
    # regenerating this file never destroys it (fixed 2026-09-24 after a
    # harness run wiped the narrative sections). Deterministic: file content
    # only; no timestamps.
    narrative_path = os.path.join(BASE, "results_narrative.md")
    if os.path.exists(narrative_path):
        with open(narrative_path) as f:
            lines.append(f.read().rstrip("\n"))
            lines.append("")
    with open(os.path.join(BASE, "results.md"), "w") as f:
        f.write("\n".join(lines))
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        entry = next(p for p in load_plats() if p["plat_id"] == "mill-subdivision")
        with open(DEMO_ZONING_PATH) as f:
            zoning = json.load(f)
        zoning = dict(zoning)
        zoning["source"] = "SELFTEST ONLY: inputs/zoning.json synthetic R-1-8 demo params — not a benchmark result"
        res = run_one(entry, zoning, "/tmp/bench_selftest")
        res["status"] = "selftest"
        print(json.dumps(res, indent=2, sort_keys=True))
        assert res["neron_top_ranked_lots"] > 0, "pipeline produced no lots"
        print("SELFTEST PASS: pipeline ran end-to-end on reconstructed parent polygon")
        return

    results = []
    for entry in load_plats():
        z = entry.get("zoning", {})
        if entry.get("scored") and z.get("status") == "known":
            required = ["min_lot_area_sqft", "road_width_ft"]
            if z.get("product_type") not in ("attached_twinhome", "attached_townhome"):
                required.append("min_frontage_ft")
            for k in required:
                if k not in z:
                    raise ValueError(
                        f"plat {entry['plat_id']}: scored but zoning missing {k} — refusing"
                    )
            res = run_one(entry, z, os.path.join(BASE, "runs", entry["plat_id"]))
            res["status"] = "scored"
            results.append(res)
        else:
            results.append({
                "status": "not_scored",
                "plat_id": entry["plat_id"],
                "approved_lots": entry.get("approved_lots"),
                "reason": z.get("reason", "no reason recorded"),
            })
    payload = write_results(results)
    print(f"scored: {payload['scored_plats']}, within tolerance: {payload['within_tolerance']}")
    print("wrote benchmark/results.json + benchmark/results.md")


if __name__ == "__main__":
    main()
