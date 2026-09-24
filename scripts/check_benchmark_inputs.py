#!/usr/bin/env python3
"""Cross-lane consistency check: benchmark harness inputs vs rule-pack drafts.

For every scored plat in benchmark/plats.json (zoning.status == "known"),
verify that the harness inputs (min_lot_area_sqft, min_frontage_ft,
road_width_ft) do not contradict the corresponding jurisdiction rule-pack
draft params. FAILS LOUDLY (nonzero exit + named mismatches) on any drift.

Sourcing-path policy (per RISHAB ACCURACY DIRECTIVE 2026-09-24):
- Both sides numeric and different  -> MISMATCH (fail). Contradictory values.
- Rule-pack null, benchmark sourced -> WARNING (pass). The benchmark's
  approval-record sourcing path is legitimate; the pack simply has a gap.
- Benchmark missing, rule-pack has  -> WARNING (pass). Pack value exists but
  the scoring lane used another documented source; flag for review.
- No rule-pack draft for the city  -> SKIP note (pass). Absence of a pack is
  not drift; do not invent a comparison.

Usage:
  python3 scripts/check_benchmark_inputs.py        # from neron-scratch root
  python3 -m unittest benchmark.test_harness      # also runs via the suite
"""
from __future__ import annotations

import json
import os
import sys

SCRATCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(SCRATCH, "benchmark")
RULEGRAPH = os.path.join(SCRATCH, "rulegraph")

# city -> rule-pack draft file (None = no draft exists yet -> SKIP, not fail)
CITY_PACKS = {
    "Murray": os.path.join(RULEGRAPH, "murray_params_draft.json"),
    "South Jordan": None,   # no South Jordan draft as of 2026-09-24
    "Taylorsville": os.path.join(RULEGRAPH, "taylorsville_params_draft.json"),
}


def _num(v):
    return None if v is None else float(v)


def check_murray(entry, pack):
    """Return (mismatches, warnings) for a Murray plat."""
    mismatches, warnings = [], []
    z = entry["zoning"]
    district = z.get("district")
    districts = pack.get("districts", {})
    d = districts.get(district)
    pid = entry["plat_id"]
    if d is None:
        warnings.append(f"{pid}: district {district!r} not in Murray draft "
                        f"(pack gap, not drift)")
    else:
        pairs = [
            ("min_lot_area_sqft", z.get("min_lot_area_sqft"),
             d.get("min_lot_area_sqft"), "lot area"),
            # benchmark frontage is lot-width-at-setback-line proxy;
            # pack field is min_lot_width_ft
            ("min_frontage_ft~min_lot_width_ft", z.get("min_frontage_ft"),
             d.get("min_lot_width_ft"), "lot width/frontage"),
        ]
        for label, bench_v, pack_v, name in pairs:
            bv, pv = _num(bench_v), _num(pack_v)
            if bv is not None and pv is not None and bv != pv:
                mismatches.append(
                    f"{pid}: {name} DRIFT — benchmark {bv:g} vs "
                    f"rule-pack {pv:g} ({label})")
            elif bv is not None and pv is None:
                warnings.append(
                    f"{pid}: {name} — benchmark {bv:g}, rule-pack null "
                    f"(pack gap; benchmark used approval-record sourcing)")
            elif bv is None and pv is not None:
                warnings.append(
                    f"{pid}: {name} — benchmark missing, rule-pack {pv:g} "
                    f"(review sourcing path)")
    # road width: Murray §16.16.180 street_min_width_ft
    sub = pack.get("subdivision_16_16_180", {})
    bv, pv = _num(z.get("road_width_ft")), _num(sub.get("street_min_width_ft"))
    if bv is not None and pv is not None and bv != pv:
        mismatches.append(
            f"{pid}: road_width_ft DRIFT — benchmark {bv:g} vs "
            f"rule-pack §16.16.180 {pv:g}")
    elif bv is not None and pv is None:
        warnings.append(f"{pid}: road width — benchmark {bv:g}, rule-pack null")
    return mismatches, warnings


def check_all():
    mismatches, warnings, skips = [], [], []
    with open(os.path.join(BENCH, "plats.json")) as f:
        plats = json.load(f)["plats"]
    for entry in plats:
        if not entry.get("scored"):
            continue
        z = entry.get("zoning", {})
        if z.get("status") != "known":
            continue
        pid = entry["plat_id"]
        city = entry.get("city")
        pack_path = CITY_PACKS.get(city, "UNKNOWN_CITY")
        if pack_path == "UNKNOWN_CITY":
            skips.append(f"{pid}: city {city!r} has no pack mapping — "
                         f"add one to CITY_PACKS")
            continue
        if pack_path is None:
            skips.append(f"{pid}: no {city} rule-pack draft exists yet — "
                         f"cannot cross-check (not drift)")
            continue
        if not os.path.exists(pack_path):
            warnings.append(f"{pid}: pack file missing: {pack_path}")
            continue
        with open(pack_path) as f:
            pack = json.load(f)
        if city == "Murray":
            m, w = check_murray(entry, pack)
        else:
            m, w = [], [f"{pid}: no checker implemented for {city} "
                        f"(pack exists but field mapping unwritten)"]
        mismatches.extend(m)
        warnings.extend(w)
    return mismatches, warnings, skips


def main():
    mismatches, warnings, skips = check_all()
    print("== benchmark input consistency check ==")
    for s in skips:
        print("SKIP :", s)
    for w in warnings:
        print("WARN :", w)
    for m in mismatches:
        print("MISMATCH:", m)
    print(f"-> {len(mismatches)} mismatches, {len(warnings)} warnings, "
          f"{len(skips)} skips")
    if mismatches:
        print("FAIL: cross-lane drift detected — fix inputs before scoring.")
        return 1
    print("OK: no drift between benchmark inputs and rule-pack drafts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
