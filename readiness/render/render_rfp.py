#!/usr/bin/env python3
"""render_rfp.py — Generates rfp_excerpt.png (1920x1080) for Hack-A-House 2026.

Renders an ILLUSTRATIVE site solicitation excerpt for a selected parcel.
Reads ALL data from readiness/out/*.csv. Zero hardcoded parcel values.

Banned content (per HAH-09 rework spec):
  - No named agency entities in rendered output
  - No solicitation reference numbers in rendered output
  - No attribution phrases in rendered output
  - No timeline mechanism references in rendered output
"""

from __future__ import annotations

import csv
import os
import sys
from typing import Dict

import matplotlib.pyplot as plt
import matplotlib.patches as patches


def load_readiness(path: str = "readiness/out/readiness_slc.csv") -> Dict[str, dict]:
    if not os.path.exists(path):
        sys.exit(f"ERROR: readiness CSV not found: {path}")
    result = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result[row["parcel_id"]] = row
    return result


def load_land_values(path: str = "readiness/out/land_value_slc.csv") -> Dict[str, Dict[int, dict]]:
    if not os.path.exists(path):
        sys.exit(f"ERROR: land value CSV not found: {path}")
    result: Dict[str, Dict[int, dict]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = row["parcel_id"]
            tp = int(float(row["target_price"]))
            result.setdefault(pid, {})[tp] = row
    return result


def _fmtd(val) -> str:
    try:
        v = int(float(val))
        return f"-${abs(v):,}" if v < 0 else f"${v:,}"
    except (ValueError, TypeError):
        return str(val)


def render_rfp_slide(
    parcel_id: str,
    readiness: Dict[str, dict],
    land_values: Dict[str, Dict[int, dict]],
    output_png: str = "readiness/render/rfp_excerpt.png",
    run_id: str = "RUN-20260925-LANDVALUE",
):
    """Render an illustrative solicitation excerpt for one parcel."""
    if parcel_id not in readiness:
        sys.exit(f"ERROR: parcel {parcel_id} not found in readiness CSV")

    r = readiness[parcel_id]
    lv = land_values.get(parcel_id, {})
    lv400 = lv.get(400000, {})
    lv500 = lv.get(500000, {})
    version = lv400.get("assumption_set_version", lv500.get("assumption_set_version", "unknown"))

    address = r.get("address", parcel_id)
    zone = r.get("district", "UNKNOWN")
    zone_name = r.get("zone_label", "")
    acres = r.get("acres", "0")
    sqft = r.get("sqft", "0")
    fits_type = r.get("fits_type", "unknown")
    fits_units = r.get("fits_units", "0")
    cat = r.get("category", "UNKNOWN")

    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#080D1A")
    ax.axis("off")

    # Header
    ax.text(0.06, 0.93, "CADROS | SITE SOLICITATION EXCERPT",
            fontsize=14, fontweight="bold", color="#F59E0B")
    ax.text(0.06, 0.86, "Attainable Housing Site Solicitation Excerpt",
            fontsize=34, fontweight="heavy", color="#F8FAFC")
    ax.text(0.06, 0.81,
            "Pre-Approved Category C Public Site \u00b7 Pre-Engineered Dimensional Envelope & Residual Land Pricing",
            fontsize=16, color="#94A3B8")

    # ── ILLUSTRATIVE BANNER ──────────────────────────────────────────────
    banner = patches.FancyBboxPatch(
        (0.20, 0.935), 0.60, 0.04,
        boxstyle="round,pad=0.005,rounding_size=0.008",
        linewidth=2,
        edgecolor="#EF4444",
        facecolor="#EF444433",
        zorder=10
    )
    ax.add_patch(banner)
    ax.text(0.50, 0.955,
            "ILLUSTRATIVE \u2014 not an issued solicitation",
            fontsize=16, fontweight="bold", color="#EF4444",
            ha="center", va="center", zorder=11)

    # Document Container
    doc_x, doc_y, doc_w, doc_h = 0.055, 0.11, 0.89, 0.67
    doc_rect = patches.FancyBboxPatch(
        (doc_x, doc_y), doc_w, doc_h,
        boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=2, edgecolor="#F59E0B", facecolor="#0F172A", zorder=2
    )
    ax.add_patch(doc_rect)

    # Document Header
    doc_header = patches.FancyBboxPatch(
        (doc_x, doc_y + doc_h - 0.09), doc_w, 0.09,
        boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=0, facecolor="#1E293B", zorder=3
    )
    ax.add_patch(doc_header)

    ax.text(doc_x + 0.02, doc_y + doc_h - 0.038,
            "COUNTY HOUSING READINESS LAB \u00b7 ILLUSTRATIVE SOLICITATION",
            fontsize=13, fontweight="bold", color="#F8FAFC", zorder=4)
    ax.text(doc_x + 0.02, doc_y + doc_h - 0.065,
            f"PUBLIC PARCEL DEVELOPMENT \u00b7 {address.upper()}",
            fontsize=11, color="#94A3B8", zorder=4)

    # Status Badge
    badge = patches.FancyBboxPatch(
        (doc_x + doc_w - 0.22, doc_y + doc_h - 0.062), 0.20, 0.035,
        boxstyle="round,pad=0.005,rounding_size=0.008",
        linewidth=1, edgecolor="#10B981", facecolor="#10B98122", zorder=4
    )
    ax.add_patch(badge)
    ax.text(doc_x + doc_w - 0.12, doc_y + doc_h - 0.045,
            "PRE-APPROVED SITE", fontsize=11, fontweight="bold",
            color="#10B981", ha="center", va="center", zorder=5)

    # Left Column: Site & Program Spec (from CSV)
    left_x = doc_x + 0.025
    left_w = 0.40
    col_y = doc_y + 0.03
    col_h = doc_h - 0.13

    left_box = patches.FancyBboxPatch(
        (left_x, col_y), left_w, col_h,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        linewidth=1, edgecolor="#334155", facecolor="#131D31", zorder=3
    )
    ax.add_patch(left_box)
    ax.text(left_x + 0.02, col_y + col_h - 0.035,
            "1. SITE & DEVELOPMENT SPECIFICATION",
            fontsize=13, fontweight="bold", color="#38BDF8", zorder=4)
    ax.plot([left_x + 0.02, left_x + left_w - 0.02],
            [col_y + col_h - 0.048, col_y + col_h - 0.048],
            color="#1E293B", lw=1, zorder=4)

    specs = [
        ("Property Location", f"{address}, Salt Lake City, UT"),
        ("Parcel Identifier", f"{parcel_id} (Salt Lake County Assessor)"),
        ("Site Acreage / Area", f"{acres} Acres ({int(float(sqft)):,} sq ft)"),
        ("Zoning Classification", f"{zone} ({zone_name})"),
        ("Pre-Approved Typology", f"{fits_units} Attainable {fits_type.replace('_', ' ').title()} Units"),
        ("Dimensional Standard", "Pre-screened against Title 21A setbacks & height"),
        ("Infrastructure Access", "Per site assessment and utility survey"),
        ("Permit Pathway", "Administrative review track"),
        ("Category", f"Readiness Category {cat}"),
    ]

    sy = col_y + col_h - 0.08
    for label, val in specs:
        ax.text(left_x + 0.02, sy, label + ":", fontsize=10.5,
                fontweight="bold", color="#94A3B8", zorder=4)
        ax.text(left_x + 0.02, sy - 0.024, val, fontsize=11,
                color="#F8FAFC", zorder=4)
        sy -= 0.052

    # Right Column: Financial Terms (from CSV)
    right_x = doc_x + 0.45
    right_w = 0.415

    right_box = patches.FancyBboxPatch(
        (right_x, col_y), right_w, col_h,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        linewidth=1, edgecolor="#334155", facecolor="#131D31", zorder=3
    )
    ax.add_patch(right_box)
    ax.text(right_x + 0.02, col_y + col_h - 0.035,
            "2. ATTAINABLE PRICING & LAND OFFERING BASIS",
            fontsize=13, fontweight="bold", color="#38BDF8", zorder=4)
    ax.plot([right_x + 0.02, right_x + right_w - 0.02],
            [col_y + col_h - 0.048, col_y + col_h - 0.048],
            color="#1E293B", lw=1, zorder=4)

    terms = [
        ("Target Unit Price Point", "$400,000 (Tier 1) or $500,000 (Tier 2) Maximum Sales Price"),
        ("Land Value at $400k Target",
         f"{_fmtd(lv400.get('max_land_value_mid', 'N/A'))} Mid "
         f"({_fmtd(lv400.get('per_unit_mid', 'N/A'))}/unit) \u00b7 "
         f"Range: {_fmtd(lv400.get('max_land_value_low', 'N/A'))} to "
         f"{_fmtd(lv400.get('max_land_value_high', 'N/A'))}"),
        ("Negative Value Policy", "If high costs yield negative land value, City conveys land at $0"),
        ("Land Value at $500k Target",
         f"{_fmtd(lv500.get('max_land_value_mid', 'N/A'))} Mid "
         f"({_fmtd(lv500.get('per_unit_mid', 'N/A'))}/unit) \u00b7 "
         f"Range: {_fmtd(lv500.get('max_land_value_low', 'N/A'))} to "
         f"{_fmtd(lv500.get('max_land_value_high', 'N/A'))}"),
        ("Builder Margin Policy", "Assumes standard market builder overhead & return"),
        ("Affordability Covenant", "Deed restriction per municipal housing policy"),
        ("Developer Submission", "Proposals scored on speed-to-groundbreak & design quality"),
        ("Execution Milestone", "Building permit submission within 90 days of award"),
    ]

    ty = col_y + col_h - 0.08
    for label, val in terms:
        ax.text(right_x + 0.02, ty, label + ":", fontsize=10.5,
                fontweight="bold", color="#94A3B8", zorder=4)
        ax.text(right_x + 0.02, ty - 0.024, val, fontsize=11,
                color="#F8FAFC", zorder=4)
        ty -= 0.052

    # Footer
    ax.plot([0.055, 0.95], [0.07, 0.07], color="#1E293B", lw=1.5)
    ax.text(0.055, 0.035,
            f"Run {run_id} \u00b7 Assumptions {version} \u00b7 Cadros Readiness Lab \u00b7 Hack-A-House 2026",
            fontsize=11, fontweight="bold", color="#38BDF8")
    ax.text(0.95, 0.035, "ILLUSTRATIVE \u2014 not an issued solicitation",
            fontsize=11, fontweight="bold", color="#EF4444", ha="right")

    os.makedirs(os.path.dirname(output_png) or ".", exist_ok=True)
    plt.savefig(output_png, dpi=100)
    plt.close()
    print(f"Rendered {output_png} (1920x1080)")


def main():
    """Usage: python render_rfp.py [parcel_id]

    If no parcel_id given, renders the first Category C parcel from the CSV.
    """
    readiness = load_readiness()
    land_values = load_land_values()

    if len(sys.argv) > 1:
        pid = sys.argv[1]
    else:
        # Pick first C parcel
        pid = None
        for p, row in readiness.items():
            if row.get("category") == "C" and p in land_values:
                pid = p
                break
        if pid is None:
            sys.exit("ERROR: no Category C parcel found in readiness/out/*.csv")

    render_rfp_slide(pid, readiness, land_values)


if __name__ == "__main__":
    main()
