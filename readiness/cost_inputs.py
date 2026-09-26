#!/usr/bin/env python3
"""readiness/cost_inputs.py — Reads Chat 2's "HAH-04a Cost Inputs" sheet export
and writes the per-unit low/mid/high tiers that land_value.py expects.

Input:  A CSV export of Chat 2's cost input sheet with columns:
          fits_type, metric, value, unit
        Where metric is one of:
          building_sqft, cost_per_sqft, soft_pct, infra_per_unit, builder_margin_pct

Output: readiness/assumptions/land_value_assumptions.csv in the format:
          fits_type,tier,hard_cost,soft_cost,infra_per_unit,builder_margin,version

The code computes:
  hard_cost     = building_sqft * cost_per_sqft
  soft_cost     = hard_cost * soft_pct
  builder_margin = hard_cost * builder_margin_pct
  infra_per_unit = passed through directly

Tier mapping:
  LOW tier  = uses HIGH cost_per_sqft, HIGH soft_pct, HIGH infra, HIGH margin_pct
  MID tier  = uses MID values
  HIGH tier = uses LOW cost_per_sqft, LOW soft_pct, LOW infra, LOW margin_pct
  (low land value = high costs; high land value = low costs)

Usage:
  python readiness/cost_inputs.py readiness/data/cost_inputs_export.csv
  python readiness/cost_inputs.py --sheet-id <google_sheet_id> --tab "HAH-04a Cost Inputs"

The --sheet-id form requires gspread and a service account; use the CSV form
for offline / CI environments.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple


TIERS = ["low", "mid", "high"]
VERSION = "v2.0-cost-inputs"

# Expected metrics in the sheet export
EXPECTED_METRICS = {
    "building_sqft",
    "cost_per_sqft",
    "soft_pct",
    "infra_per_unit",
    "builder_margin_pct",
}


def parse_float(val: str, default: float = 0.0) -> float:
    """Parse a numeric value, stripping $, %, commas."""
    if not val or val.strip().lower() in ("none", "null", "nan", "-", ""):
        return default
    s = val.strip().replace("$", "").replace(",", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return default


def load_cost_inputs_csv(path: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Load a cost inputs CSV export.

    Expected format (long-form):
        fits_type, metric, low, mid, high

    Returns: {fits_type: {metric: {tier: value}}}
    """
    if not os.path.exists(path):
        sys.exit(f"ERROR: cost inputs file not found: {path}")

    data: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        # Normalize headers
        h_lower = [h.strip().lower() for h in headers]

        for row_raw in reader:
            # Normalize keys
            row = {k.strip().lower(): v for k, v in row_raw.items()}

            fits_type = row.get("fits_type", "").strip()
            metric = row.get("metric", "").strip()

            if not fits_type or not metric:
                continue

            for tier in TIERS:
                val = row.get(tier, "")
                data[fits_type][metric][tier] = parse_float(val)

    return dict(data)


def compute_assumptions(
    cost_data: Dict[str, Dict[str, Dict[str, float]]]
) -> List[Dict[str, str]]:
    """Compute per-unit cost assumptions from raw sq ft / $/sq ft / % inputs.

    For each fits_type and each tier:
        hard_cost      = building_sqft[tier] * cost_per_sqft[tier]
        soft_cost      = hard_cost * soft_pct[tier]
        infra_per_unit = infra_per_unit[tier]  (passthrough)
        builder_margin = hard_cost * builder_margin_pct[tier]

    Tier inversion for land value sensitivity:
        LOW  land value tier uses HIGH cost inputs (worst case costs)
        MID  land value tier uses MID  cost inputs
        HIGH land value tier uses LOW  cost inputs (best case costs)
    """
    # Tier mapping: land_value tier -> cost_input tier
    TIER_MAP = {"low": "high", "mid": "mid", "high": "low"}

    rows = []
    for fits_type, metrics in sorted(cost_data.items()):
        # Validate that all expected metrics exist
        missing = EXPECTED_METRICS - set(metrics.keys())
        if missing:
            print(f"WARNING: fits_type '{fits_type}' missing metrics: {missing}",
                  file=sys.stderr)

        for lv_tier in TIERS:
            cost_tier = TIER_MAP[lv_tier]

            building_sqft = metrics.get("building_sqft", {}).get(cost_tier, 0)
            cost_per_sqft = metrics.get("cost_per_sqft", {}).get(cost_tier, 0)
            soft_pct = metrics.get("soft_pct", {}).get(cost_tier, 0)
            infra = metrics.get("infra_per_unit", {}).get(cost_tier, 0)
            margin_pct = metrics.get("builder_margin_pct", {}).get(cost_tier, 0)

            # Percentages: if > 1, assume already a percentage (e.g. 15 means 15%)
            if soft_pct > 1:
                soft_pct = soft_pct / 100.0
            if margin_pct > 1:
                margin_pct = margin_pct / 100.0

            hard_cost = building_sqft * cost_per_sqft
            soft_cost = hard_cost * soft_pct
            builder_margin = hard_cost * margin_pct

            rows.append({
                "fits_type": fits_type,
                "tier": lv_tier,
                "hard_cost": str(round(hard_cost)),
                "soft_cost": str(round(soft_cost)),
                "infra_per_unit": str(round(infra)),
                "builder_margin": str(round(builder_margin)),
                "version": VERSION,
            })

    return rows


def write_assumptions(
    rows: List[Dict[str, str]],
    output_path: str = "readiness/assumptions/land_value_assumptions.csv",
):
    """Write computed assumptions CSV in the format land_value.py expects."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fieldnames = ["fits_type", "tier", "hard_cost", "soft_cost",
                  "infra_per_unit", "builder_margin", "version"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Chat 2 cost inputs to land_value.py assumptions CSV"
    )
    parser.add_argument(
        "input_csv",
        help="Path to CSV export of HAH-04a Cost Inputs sheet"
    )
    parser.add_argument(
        "-o", "--output",
        default="readiness/assumptions/land_value_assumptions.csv",
        help="Output path for assumptions CSV (default: %(default)s)"
    )
    args = parser.parse_args()

    print(f"Loading cost inputs from: {args.input_csv}")
    cost_data = load_cost_inputs_csv(args.input_csv)

    if not cost_data:
        sys.exit("ERROR: no cost data found in input CSV")

    print(f"Found {len(cost_data)} fits_type(s): {sorted(cost_data.keys())}")

    rows = compute_assumptions(cost_data)
    write_assumptions(rows, args.output)

    # Summary
    print("\n--- Computed Assumptions Summary ---")
    for row in rows:
        print(f"  {row['fits_type']:20s} {row['tier']:4s}  "
              f"hard={row['hard_cost']:>8s}  soft={row['soft_cost']:>8s}  "
              f"infra={row['infra_per_unit']:>8s}  margin={row['builder_margin']:>8s}")
    print(f"\nVersion: {VERSION}")
    print(f"Output:  {args.output}")
    print("Ready for: python readiness/land_value.py")


if __name__ == "__main__":
    main()
