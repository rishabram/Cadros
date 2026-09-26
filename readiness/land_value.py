#!/usr/bin/env python3
"""readiness/land_value.py — Attainable Land Value Calculator (Task HAH-04).

Reuses breakeven-lot-price logic, solving for maximum supportable LAND value:
  max_land_value = (target_price * units) - (hard_cost + soft_cost + per_unit_infra + builder_margin) * units
  per_unit       = max_land_value / units

Calculates for target prices $400,000 and $500,000 for every A, B, and C parcel,
using fits_type and fits_units from readiness/out/readiness_slc.csv and cost
assumptions strictly from readiness/assumptions/land_value_assumptions.csv.

Sensitivity calculation:
- LOW land value uses HIGH-cost assumptions (conservative builder/high inflation).
- MID land value uses MID-cost assumptions.
- HIGH land value uses LOW-cost assumptions (lean/efficient delivery).

Negative land value means the site does not pencil even with free land.
Negative values are explicitly preserved as valid findings.
Totals are not computed across parcels. The term "profit" is never used.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Any, Dict, List, Optional, Tuple


def parse_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("$", "").replace(",", "").replace("%", "")
    if not s or s.lower() in ("none", "null", "nan", "-"):
        return default
    try:
        return float(s)
    except ValueError:
        return default


def load_assumptions(path: str) -> Tuple[Dict[str, Dict[str, Dict[str, float]]], str]:
    """Loads cost assumptions from CSV.
    Supports either:
    1. Long format: fits_type, tier (low/mid/high), hard_cost, soft_cost, infra_per_unit, builder_margin, version
    2. Wide format: fits_type, hard_cost_low, hard_cost_mid, hard_cost_high, ..., version
    3. Global metrics format: metric, low, mid, high, version
    Returns (assumptions_by_type, assumption_set_version).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Assumptions file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"Assumptions file is empty: {path}")

    first_row = rows[0]
    headers = {k.strip().lower(): k for k in first_row.keys()}
    version = first_row.get("version") or first_row.get("assumption_set_version") or "v1.0"

    assumptions: Dict[str, Dict[str, Dict[str, float]]] = {}

    # Check if wide format (contains _low, _mid, _high in columns)
    is_wide = any("_low" in k or "_high" in k for k in headers)

    if is_wide:
        for r in rows:
            ft = r.get("fits_type", r.get("type", "default")).strip().lower()
            if not ft:
                ft = "default"
            assumptions[ft] = {
                "low_cost": {
                    "hard_cost": parse_float(r.get("hard_cost_low", r.get("hard_low"))),
                    "soft_cost": parse_float(r.get("soft_cost_low", r.get("soft_low"))),
                    "infra_per_unit": parse_float(r.get("infra_per_unit_low", r.get("infra_low"))),
                    "builder_margin": parse_float(r.get("builder_margin_low", r.get("margin_low"))),
                },
                "mid_cost": {
                    "hard_cost": parse_float(r.get("hard_cost_mid", r.get("hard_mid"))),
                    "soft_cost": parse_float(r.get("soft_cost_mid", r.get("soft_mid"))),
                    "infra_per_unit": parse_float(r.get("infra_per_unit_mid", r.get("infra_mid"))),
                    "builder_margin": parse_float(r.get("builder_margin_mid", r.get("margin_mid"))),
                },
                "high_cost": {
                    "hard_cost": parse_float(r.get("hard_cost_high", r.get("hard_high"))),
                    "soft_cost": parse_float(r.get("soft_cost_high", r.get("soft_high"))),
                    "infra_per_unit": parse_float(r.get("infra_per_unit_high", r.get("infra_high"))),
                    "builder_margin": parse_float(r.get("builder_margin_high", r.get("margin_high"))),
                },
            }
            if "version" in r and r["version"]:
                version = r["version"]
    else:
        # Long format by fits_type + cost_tier
        for r in rows:
            ft = r.get("fits_type", r.get("type", "default")).strip().lower()
            if not ft:
                ft = "default"
            tier = r.get("tier", r.get("scenario", r.get("cost_tier", "mid"))).strip().lower()
            if "low" in tier:
                tier_key = "low_cost"
            elif "high" in tier:
                tier_key = "high_cost"
            else:
                tier_key = "mid_cost"

            if ft not in assumptions:
                assumptions[ft] = {
                    "low_cost": {"hard_cost": 0.0, "soft_cost": 0.0, "infra_per_unit": 0.0, "builder_margin": 0.0},
                    "mid_cost": {"hard_cost": 0.0, "soft_cost": 0.0, "infra_per_unit": 0.0, "builder_margin": 0.0},
                    "high_cost": {"hard_cost": 0.0, "soft_cost": 0.0, "infra_per_unit": 0.0, "builder_margin": 0.0},
                }

            assumptions[ft][tier_key] = {
                "hard_cost": parse_float(r.get("hard_cost")),
                "soft_cost": parse_float(r.get("soft_cost")),
                "infra_per_unit": parse_float(r.get("infra_per_unit", r.get("infrastructure_per_unit", r.get("infra_cost")))),
                "builder_margin": parse_float(r.get("builder_margin", r.get("margin"))),
            }
            if "version" in r and r["version"]:
                version = r["version"]

    return assumptions, version


def get_assumptions_for_type(
    assumptions: Dict[str, Dict[str, Dict[str, float]]], fits_type: str
) -> Dict[str, Dict[str, float]]:
    ft = (fits_type or "").strip().lower()
    if ft in assumptions:
        return assumptions[ft]
    if "default" in assumptions:
        return assumptions["default"]
    if assumptions:
        return next(iter(assumptions.values()))
    zero_tier = {"hard_cost": 0.0, "soft_cost": 0.0, "infra_per_unit": 0.0, "builder_margin": 0.0}
    return {"low_cost": zero_tier, "mid_cost": zero_tier, "high_cost": zero_tier}


def compute_land_value(
    target_price: float,
    units: float,
    type_assumptions: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    """Computes max land value across low/mid/high sensitivities.
    low land value  = target_price * units - high_cost * units
    mid land value  = target_price * units - mid_cost * units
    high land value = target_price * units - low_cost * units
    """
    if units <= 0:
        return {
            "max_land_value_low": 0.0,
            "max_land_value_mid": 0.0,
            "max_land_value_high": 0.0,
            "per_unit_low": 0.0,
            "per_unit_mid": 0.0,
            "per_unit_high": 0.0,
        }

    high_c = type_assumptions.get("high_cost", {})
    cost_per_unit_high = (
        high_c.get("hard_cost", 0.0)
        + high_c.get("soft_cost", 0.0)
        + high_c.get("infra_per_unit", 0.0)
        + high_c.get("builder_margin", 0.0)
    )

    mid_c = type_assumptions.get("mid_cost", {})
    cost_per_unit_mid = (
        mid_c.get("hard_cost", 0.0)
        + mid_c.get("soft_cost", 0.0)
        + mid_c.get("infra_per_unit", 0.0)
        + mid_c.get("builder_margin", 0.0)
    )

    low_c = type_assumptions.get("low_cost", {})
    cost_per_unit_low = (
        low_c.get("hard_cost", 0.0)
        + low_c.get("soft_cost", 0.0)
        + low_c.get("infra_per_unit", 0.0)
        + low_c.get("builder_margin", 0.0)
    )

    per_unit_low = target_price - cost_per_unit_high
    per_unit_mid = target_price - cost_per_unit_mid
    per_unit_high = target_price - cost_per_unit_low

    max_land_val_low = per_unit_low * units
    max_land_val_mid = per_unit_mid * units
    max_land_val_high = per_unit_high * units

    return {
        "max_land_value_low": round(max_land_val_low, 2),
        "max_land_value_mid": round(max_land_val_mid, 2),
        "max_land_value_high": round(max_land_val_high, 2),
        "per_unit_low": round(per_unit_low, 2),
        "per_unit_mid": round(per_unit_mid, 2),
        "per_unit_high": round(per_unit_high, 2),
    }


def process_parcels(
    readiness_csv_path: str,
    assumptions_csv_path: str,
    out_csv_path: str,
    target_prices: List[float] = [400000.0, 500000.0],
) -> int:
    if not os.path.exists(readiness_csv_path):
        raise FileNotFoundError(f"Readiness output CSV not found: {readiness_csv_path}")

    assumptions, version = load_assumptions(assumptions_csv_path)

    out_dir = os.path.dirname(os.path.abspath(out_csv_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    results = []

    with open(readiness_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = (
                row.get("category")
                or row.get("readiness_category")
                or row.get("tier")
                or row.get("classification")
                or ""
            ).strip().upper()

            if cat not in ("A", "B", "C"):
                continue

            parcel_id = row.get("parcel_id") or row.get("id") or "unknown"
            fits_type = row.get("fits_type") or row.get("typology") or "single_family"
            fits_units = parse_float(row.get("fits_units") or row.get("units") or row.get("unit_count"), 0.0)

            if fits_units <= 0:
                continue

            type_assump = get_assumptions_for_type(assumptions, fits_type)

            for tp in target_prices:
                vals = compute_land_value(tp, fits_units, type_assump)
                results.append({
                    "parcel_id": parcel_id,
                    "target_price": int(tp),
                    "max_land_value_low": vals["max_land_value_low"],
                    "max_land_value_mid": vals["max_land_value_mid"],
                    "max_land_value_high": vals["max_land_value_high"],
                    "per_unit_low": vals["per_unit_low"],
                    "per_unit_mid": vals["per_unit_mid"],
                    "per_unit_high": vals["per_unit_high"],
                    "assumption_set_version": version,
                })

    fieldnames = [
        "parcel_id",
        "target_price",
        "max_land_value_low",
        "max_land_value_mid",
        "max_land_value_high",
        "per_unit_low",
        "per_unit_mid",
        "per_unit_high",
        "assumption_set_version",
    ]

    with open(out_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"Wrote {len(results)} land value evaluations to {out_csv_path}")
    return len(results)


def main():
    parser = argparse.ArgumentParser(description="Attainable Land Value Calculator (HAH-04)")
    parser.add_argument(
        "--readiness-csv",
        default="readiness/out/readiness_slc.csv",
        help="Path to readiness_slc.csv containing A, B, C parcels",
    )
    parser.add_argument(
        "--assumptions-csv",
        default="readiness/assumptions/land_value_assumptions.csv",
        help="Path to land_value_assumptions.csv (written by Chat 2)",
    )
    parser.add_argument(
        "--out-csv",
        default="readiness/out/land_value_slc.csv",
        help="Destination path for land_value_slc.csv",
    )
    parser.add_argument(
        "--target-prices",
        default="400000,500000",
        help="Comma-separated target prices",
    )

    args = parser.parse_args()
    tps = [float(x.strip()) for x in args.target_prices.split(",") if x.strip()]

    try:
        process_parcels(args.readiness_csv, args.assumptions_csv, args.out_csv, tps)
    except FileNotFoundError as e:
        print(f"BLOCKED_TECHNICAL / INPUTS_MISSING: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
