#!/usr/bin/env python3
"""render_parcel.py — Generates parcel_<id>.png (1920x1080) for Hack-A-House 2026.

Reads ALL data from:
  - readiness/out/readiness_slc.csv   (parcel geometry, zone, category, fits)
  - readiness/out/land_value_slc.csv  (land value low/mid/high at each target price)

Zero hardcoded parcel values. Render is fully reproducible from CSV contents.
"""

from __future__ import annotations

import csv
import os
import sys
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.patches as patches


# ── CSV loaders ──────────────────────────────────────────────────────────────

def load_readiness(path: str = "readiness/out/readiness_slc.csv") -> Dict[str, dict]:
    """Load readiness CSV into dict keyed by parcel_id."""
    if not os.path.exists(path):
        sys.exit(f"ERROR: readiness CSV not found: {path}")
    result = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result[row["parcel_id"]] = row
    return result


def load_land_values(path: str = "readiness/out/land_value_slc.csv") -> Dict[str, Dict[int, dict]]:
    """Load land value CSV into dict[parcel_id][target_price] = row."""
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
    """Format a dollar amount from CSV string."""
    try:
        v = int(float(val))
        if v < 0:
            return f"-${abs(v):,}"
        return f"${v:,}"
    except (ValueError, TypeError):
        return str(val)


# ── Rendering ────────────────────────────────────────────────────────────────

def render_parcel_card(
    parcel_id: str,
    readiness: Dict[str, dict],
    land_values: Dict[str, Dict[int, dict]],
    output_png: str,
    run_id: str = "RUN-20260925-LANDVALUE",
):
    """Render a single parcel dossier slide from CSV data only."""
    if parcel_id not in readiness:
        sys.exit(f"ERROR: parcel {parcel_id} not found in readiness CSV")
    r = readiness[parcel_id]
    lv = land_values.get(parcel_id, {})

    cat = r.get("category", "UNKNOWN")
    cat_color = "#10B981" if cat == "A" else ("#F97316" if cat == "C" else "#38BDF8")
    fits_type = r.get("fits_type", "unknown")
    fits_units = r.get("fits_units", "0")
    address = r.get("address", parcel_id)
    zone = r.get("district", "UNKNOWN")
    zone_name = r.get("zone_label", "")
    acres = r.get("acres", "0")
    sqft = r.get("sqft", "0")

    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#080D1A")
    ax.axis("off")

    # Header
    ax.text(0.06, 0.93, f"CADROS | PARCEL READINESS DOSSIER \u00b7 CATEGORY {cat}",
            fontsize=14, fontweight="bold", color=cat_color)
    ax.text(0.06, 0.86, f"{address} (Parcel {parcel_id})",
            fontsize=34, fontweight="heavy", color="#F8FAFC")
    ax.text(0.06, 0.81,
            "Salt Lake City Municipal Public Land Strategy \u00b7 Site Feasibility & Attainable Land Value Range",
            fontsize=16, color="#94A3B8")

    # 4 Horizontal Pipeline Cards (data-driven, no binding rule hardcodes)
    pipeline = [
        ("01 SOURCE RECORD", [
            f"ID: {parcel_id}",
            f"Address: {address}",
            f"County: Salt Lake County",
            f"Area: {acres} acres ({int(float(sqft)):,} sqft)",
            f"Source: AGRC / County GIS"
        ]),
        ("02 ZONING DISTRICT", [
            f"District: {zone}",
            f"Name: {zone_name}",
            f"Jurisdiction: Salt Lake City",
            f"Status: Recorded in City GIS",
            f"Overlays: See city zoning map"
        ]),
        ("03 WHAT FITS", [
            f"Typology: {fits_type}",
            f"Feasible Yield: {fits_units} units",
            f"Configuration: {fits_type} infill",
            f"Access: Per site assessment",
            f"Infrastructure: Per site assessment"
        ]),
        ("04 READINESS TIER", [
            f"Category: {cat}",
            f"Type: {fits_type}",
            f"Units: {fits_units}",
            f"Zone: {zone}",
            f"Data Status: From readiness CSV"
        ]),
    ]

    card_w = 0.205
    gap = 0.016
    start_x = 0.055
    card_y = 0.44
    card_h = 0.33

    for i, (title, lines) in enumerate(pipeline):
        cx = start_x + i * (card_w + gap)
        is_highlight = (i == 3)
        border_col = cat_color if is_highlight else "#334155"
        bg_col = "#131D31" if not is_highlight else "#152438"

        rect = patches.FancyBboxPatch(
            (cx, card_y), card_w, card_h,
            boxstyle="round,pad=0.015,rounding_size=0.015",
            linewidth=1.8 if is_highlight else 1.2,
            edgecolor=border_col,
            facecolor=bg_col,
            zorder=2
        )
        ax.add_patch(rect)

        ax.text(cx + 0.012, card_y + card_h - 0.035, title,
                fontsize=11, fontweight="bold",
                color="#38BDF8" if not is_highlight else cat_color, zorder=3)
        ax.plot([cx + 0.012, cx + card_w - 0.012],
                [card_y + card_h - 0.05, card_y + card_h - 0.05],
                color="#1E293B", lw=1, zorder=3)

        line_y = card_y + card_h - 0.085
        for line in lines:
            ax.text(cx + 0.012, line_y, line, fontsize=10.5, color="#E2E8F0", zorder=3)
            line_y -= 0.045

        if i < len(pipeline) - 1:
            ax.annotate(
                "",
                xy=(cx + card_w + gap - 0.003, card_y + card_h / 2),
                xytext=(cx + card_w + 0.003, card_y + card_h / 2),
                arrowprops=dict(arrowstyle="->,head_width=0.3,head_length=0.4",
                                color="#475569", lw=2),
                zorder=4
            )

    # Land Value Section — read from CSV
    val_box = patches.FancyBboxPatch(
        (0.055, 0.12), 0.58, 0.28,
        boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=2,
        edgecolor="#38BDF8",
        facecolor="#0F172A",
        zorder=2
    )
    ax.add_patch(val_box)

    ax.text(0.075, 0.355, "MAXIMUM SUPPORTABLE LAND VALUE (Residual Land Value Model)",
            fontsize=14, fontweight="bold", color="#38BDF8", zorder=3)
    ax.text(0.075, 0.33,
            "Formula: (Target Price \u00d7 Units) \u2212 (Hard Cost + Soft Cost + Infra + Builder Margin) \u00d7 Units",
            fontsize=11, color="#94A3B8", zorder=3)

    for idx, (tp, x_offset) in enumerate([(400000, 0.075), (500000, 0.35)]):
        row = lv.get(tp, {})
        low = row.get("max_land_value_low", "N/A")
        mid = row.get("max_land_value_mid", "N/A")
        high = row.get("max_land_value_high", "N/A")
        pu_low = row.get("per_unit_low", "N/A")
        pu_mid = row.get("per_unit_mid", "N/A")
        pu_high = row.get("per_unit_high", "N/A")
        mid_positive = float(mid) > 0 if mid != "N/A" else False

        c_box = patches.FancyBboxPatch(
            (x_offset, 0.145), 0.25, 0.165,
            boxstyle="round,pad=0.01,rounding_size=0.01",
            linewidth=1,
            edgecolor="#334155",
            facecolor="#1E293B",
            zorder=3
        )
        ax.add_patch(c_box)
        ax.text(x_offset + 0.015, 0.28, f"TARGET PRICE: ${tp:,} / unit",
                fontsize=11, fontweight="bold", color="#F8FAFC", zorder=4)
        ax.text(x_offset + 0.015, 0.245,
                f"Site Range: {_fmtd(low)} to {_fmtd(high)}",
                fontsize=12, fontweight="heavy", color="#38BDF8", zorder=4)
        ax.text(x_offset + 0.015, 0.215,
                f"Midpoint Site: {_fmtd(mid)}",
                fontsize=11, color="#E2E8F0", zorder=4)
        ax.text(x_offset + 0.015, 0.185,
                f"Per Unit: {_fmtd(pu_mid)} (range {_fmtd(pu_low)} to {_fmtd(pu_high)})",
                fontsize=10, color="#94A3B8", zorder=4)
        finding_color = "#10B981" if mid_positive else "#EF4444"
        finding_text = "Pencils at midpoint" if mid_positive else "Does not pencil at midpoint"
        ax.text(x_offset + 0.015, 0.155, f"Finding: {finding_text}",
                fontsize=9.5, fontweight="bold", color=finding_color, zorder=4)

    # Status Box
    version = lv.get(400000, lv.get(500000, {})).get("assumption_set_version", "unknown")
    status_box = patches.FancyBboxPatch(
        (0.66, 0.12), 0.29, 0.28,
        boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=1.5,
        edgecolor="#334155",
        facecolor="#131D31",
        zorder=2
    )
    ax.add_patch(status_box)

    ax.text(0.68, 0.355, "DATA STATUS & REPRODUCIBILITY",
            fontsize=13, fontweight="bold", color="#F8FAFC", zorder=3)
    ax.plot([0.68, 0.93], [0.34, 0.34], color="#1E293B", lw=1, zorder=3)

    status_items = [
        f"Execution Run: {run_id}",
        f"Assumptions: {version}",
        f"Source: readiness/out/*.csv",
        f"Zone: {zone} ({zone_name})",
        f"Provenance: Salt Lake County Open GIS / Cadros",
    ]
    sy = 0.31
    for sit in status_items:
        ax.plot([0.685], [sy], marker="s", markersize=4, color="#38BDF8", zorder=3)
        ax.text(0.698, sy - 0.005, sit, fontsize=10.5, color="#CBD5E1", zorder=3)
        sy -= 0.038

    # Footer
    ax.plot([0.055, 0.95], [0.07, 0.07], color="#1E293B", lw=1.5)
    ax.text(0.055, 0.035, f"Run {run_id} \u00b7 Cadros Platform Delivery \u00b7 Hack-A-House 2026",
            fontsize=11, fontweight="bold", color="#38BDF8")
    ax.text(0.95, 0.035, "Audit-ready slide export \u00b7 Overseer drop-in compatible",
            fontsize=11, color="#64748B", ha="right")

    os.makedirs(os.path.dirname(output_png) or ".", exist_ok=True)
    plt.savefig(output_png, dpi=100)
    plt.close()
    print(f"Rendered {output_png} (1920x1080)")


def main():
    """Render parcel cards. Usage: python render_parcel.py [parcel_id ...]

    If no parcel IDs given, renders one A and one C parcel from the CSV
    (first occurrence of each category).
    """
    readiness = load_readiness()
    land_values = load_land_values()

    parcel_ids = sys.argv[1:] if len(sys.argv) > 1 else None

    if parcel_ids is None:
        # Pick first A and first C parcel from readiness CSV
        picked = {}
        for pid, row in readiness.items():
            cat = row.get("category", "")
            if cat in ("A", "C") and cat not in picked and pid in land_values:
                picked[cat] = pid
            if len(picked) >= 2:
                break
        parcel_ids = list(picked.values())

    if not parcel_ids:
        sys.exit("ERROR: no renderable parcels found in readiness/out/*.csv")

    for pid in parcel_ids:
        render_parcel_card(pid, readiness, land_values,
                           f"readiness/render/parcel_{pid}.png")


if __name__ == "__main__":
    main()
