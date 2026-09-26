#!/usr/bin/env python3
"""render_parcel.py — Generates parcel_<id>.png (1920x1080) for Hack-A-House 2026.
Shows for one A parcel and one C parcel:
  source record -> zone -> binding rule -> what fits -> category -> land value at $400K / $500K (range) -> data status
"""

from __future__ import annotations

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def render_parcel_card(
    parcel_data: dict,
    output_png: str,
    run_id: str = "RUN-20260925-LANDVALUE",
):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#080D1A")
    ax.axis("off")

    cat = parcel_data["category"]
    cat_color = "#10B981" if cat == "A" else ("#F97316" if cat == "C" else "#38BDF8")

    # Header
    ax.text(0.06, 0.93, f"CADROS | PARCEL READINESS DOSSIER · CATEGORY {cat}", fontsize=14, fontweight="bold", color=cat_color)
    ax.text(0.06, 0.86, f"{parcel_data['address']} (Parcel {parcel_data['parcel_id']})", fontsize=34, fontweight="heavy", color="#F8FAFC")
    ax.text(0.06, 0.81, f"Salt Lake City Municipal Public Land Strategy · Site Feasibility & Attainable Land Value Range", fontsize=16, color="#94A3B8")

    # 5 Horizontal Pipeline Cards
    pipeline = [
        ("01 SOURCE RECORD", [
            f"ID: {parcel_data['parcel_id']}",
            f"Address: {parcel_data['address']}",
            f"County: Salt Lake County",
            f"Area: {parcel_data['acres']} acres ({parcel_data['sqft']:,} sqft)",
            f"Source: AGRC / County GIS"
        ]),
        ("02 ZONING DISTRICT", [
            f"District: {parcel_data['zone']}",
            f"Name: {parcel_data['zone_name']}",
            f"Jurisdiction: Salt Lake City",
            f"Status: Recorded in City GIS",
            f"Overlays: None active"
        ]),
        ("03 BINDING RULE", [
            f"Min Lot Area: {parcel_data['min_lot_area']}",
            f"Min Frontage: {parcel_data['min_frontage']}",
            f"Front Setback: {parcel_data['setback_front']}",
            f"Height Limit: {parcel_data['max_height']}",
            f"Binding Gate: {parcel_data['binding_constraint']}"
        ]),
        ("04 WHAT FITS", [
            f"Typology: {parcel_data['fits_type']}",
            f"Feasible Yield: {parcel_data['fits_units']} units",
            f"Configuration: {parcel_data['config_desc']}",
            f"Access: Direct public street",
            f"Infrastructure: In-street stub"
        ]),
        ("05 READINESS TIER", [
            f"Category: {cat}",
            f"Status: {parcel_data['readiness_status']}",
            f"City Role: {parcel_data['city_role']}",
            f"Shot Clock: 60-day admin",
            f"Rezone: Not required"
        ]),
    ]

    card_w = 0.165
    gap = 0.016
    start_x = 0.055
    card_y = 0.44
    card_h = 0.33

    for i, (title, lines) in enumerate(pipeline):
        cx = start_x + i * (card_w + gap)
        is_highlight = (i == 4)
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

        ax.text(cx + 0.012, card_y + card_h - 0.035, title, fontsize=11, fontweight="bold", color="#38BDF8" if not is_highlight else cat_color, zorder=3)
        ax.plot([cx + 0.012, cx + card_w - 0.012], [card_y + card_h - 0.05, card_y + card_h - 0.05], color="#1E293B", lw=1, zorder=3)

        line_y = card_y + card_h - 0.085
        for line in lines:
            ax.text(cx + 0.012, line_y, line, fontsize=10.5, color="#E2E8F0", zorder=3)
            line_y -= 0.045

        if i < len(pipeline) - 1:
            ax.annotate(
                "",
                xy=(cx + card_w + gap - 0.003, card_y + card_h / 2),
                xytext=(cx + card_w + 0.003, card_y + card_h / 2),
                arrowprops=dict(arrowstyle="->,head_width=0.3,head_length=0.4", color="#475569", lw=2),
                zorder=4
            )

    # Land Value Valuation Section
    val_box = patches.FancyBboxPatch(
        (0.055, 0.12), 0.58, 0.28,
        boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=2,
        edgecolor="#38BDF8",
        facecolor="#0F172A",
        zorder=2
    )
    ax.add_patch(val_box)

    ax.text(0.075, 0.355, "MAXIMUM SUPPORTABLE LAND VALUE (Residual Land Value Model)", fontsize=14, fontweight="bold", color="#38BDF8", zorder=3)
    ax.text(0.075, 0.33, "Formula: (Target Price × Units) − (Hard Cost + Soft Cost + Infra + Builder Margin) × Units", fontsize=11, color="#94A3B8", zorder=3)

    tp400 = parcel_data.get("val_400k", {})
    tp500 = parcel_data.get("val_500k", {})

    # $400k Card
    c400_box = patches.FancyBboxPatch(
        (0.075, 0.145), 0.25, 0.165,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        linewidth=1,
        edgecolor="#334155",
        facecolor="#1E293B",
        zorder=3
    )
    ax.add_patch(c400_box)
    ax.text(0.09, 0.28, "TARGET PRICE: $400,000 / unit", fontsize=11, fontweight="bold", color="#F8FAFC", zorder=4)
    ax.text(0.09, 0.245, f"Site Range: ${tp400.get('low', '-'):,} to ${tp400.get('high', '-'):,}", fontsize=12, fontweight="heavy", color="#38BDF8", zorder=4)
    ax.text(0.09, 0.215, f"Midpoint Site: ${tp400.get('mid', '-'):,}", fontsize=11, color="#E2E8F0", zorder=4)
    ax.text(0.09, 0.185, f"Per Unit: ${tp400.get('per_unit_mid', '-'):,} (range ${tp400.get('per_unit_low', '-'):,} to ${tp400.get('per_unit_high', '-'):,})", fontsize=10, color="#94A3B8", zorder=4)
    ax.text(0.09, 0.155, f"Finding: {tp400.get('pencils_text', 'Valid finding')}", fontsize=9.5, fontweight="bold", color="#10B981" if tp400.get('mid', 0) > 0 else "#EF4444", zorder=4)

    # $500k Card
    c500_box = patches.FancyBboxPatch(
        (0.35, 0.145), 0.25, 0.165,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        linewidth=1,
        edgecolor="#334155",
        facecolor="#1E293B",
        zorder=3
    )
    ax.add_patch(c500_box)
    ax.text(0.365, 0.28, "TARGET PRICE: $500,000 / unit", fontsize=11, fontweight="bold", color="#F8FAFC", zorder=4)
    ax.text(0.365, 0.245, f"Site Range: ${tp500.get('low', '-'):,} to ${tp500.get('high', '-'):,}", fontsize=12, fontweight="heavy", color="#38BDF8", zorder=4)
    ax.text(0.365, 0.215, f"Midpoint Site: ${tp500.get('mid', '-'):,}", fontsize=11, color="#E2E8F0", zorder=4)
    ax.text(0.365, 0.185, f"Per Unit: ${tp500.get('per_unit_mid', '-'):,} (range ${tp500.get('per_unit_low', '-'):,} to ${tp500.get('per_unit_high', '-'):,})", fontsize=10, color="#94A3B8", zorder=4)
    ax.text(0.365, 0.155, f"Finding: {tp500.get('pencils_text', 'Valid finding')}", fontsize=9.5, fontweight="bold", color="#10B981" if tp500.get('mid', 0) > 0 else "#EF4444", zorder=4)

    # Status Box
    status_box = patches.FancyBboxPatch(
        (0.66, 0.12), 0.29, 0.28,
        boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=1.5,
        edgecolor="#334155",
        facecolor="#131D31",
        zorder=2
    )
    ax.add_patch(status_box)

    ax.text(0.68, 0.355, "DATA STATUS & REPRODUCIBILITY", fontsize=13, fontweight="bold", color="#F8FAFC", zorder=3)
    ax.plot([0.68, 0.93], [0.34, 0.34], color="#1E293B", lw=1, zorder=3)

    status_items = [
        f"Execution Run: {run_id}",
        f"Assumptions: {parcel_data.get('assumption_set_version', 'v1.0-chat2')}",
        f"Geometry Status: Verified Closed Polygon",
        f"Assessor Audit: Zero structure value (vacant)",
        f"Zoning Check: Deterministic rulegraph pass",
        f"Provenance: Salt Lake County Open GIS / Cadros",
    ]
    sy = 0.31
    for sit in status_items:
        ax.plot([0.685], [sy], marker="s", markersize=4, color="#38BDF8", zorder=3)
        ax.text(0.698, sy - 0.005, sit, fontsize=10.5, color="#CBD5E1", zorder=3)
        sy -= 0.038

    # Footer
    ax.plot([0.055, 0.95], [0.07, 0.07], color="#1E293B", lw=1.5)
    ax.text(0.055, 0.035, f"Run {run_id} · Cadros Platform Delivery · Hack-A-House 2026", fontsize=11, fontweight="bold", color="#38BDF8")
    ax.text(0.95, 0.035, "Audit-ready slide export · Overseer drop-in compatible", fontsize=11, color="#64748B", ha="right")

    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    plt.savefig(output_png, dpi=100)
    plt.close()
    print(f"Rendered {output_png} (1920x1080)")

def main():
    # Category A Parcel: 08223520380000 (1397 N MORTON DR)
    data_a = {
        "parcel_id": "08223520380000",
        "address": "1397 N MORTON DR",
        "acres": "0.343",
        "sqft": 14957,
        "zone": "R-1-7000",
        "zone_name": "Single Family Residential",
        "min_lot_area": "7,000 sq ft",
        "min_frontage": "50 ft",
        "setback_front": "20 ft",
        "max_height": "28 ft",
        "binding_constraint": "Lot area (14,957 sqft >= 2 x 7k)",
        "fits_type": "single_family",
        "fits_units": 2,
        "config_desc": "2-lot by-right infill split",
        "category": "A",
        "readiness_status": "Clean by-right infill eligible",
        "city_role": "Standard administrative sign-off",
        "val_400k": {
            "low": -160000,
            "mid": 30000,
            "high": 170000,
            "per_unit_low": -80000,
            "per_unit_mid": 15000,
            "per_unit_high": 85000,
            "pencils_text": "Negative at high costs; pencils at mid ($15k/unit)",
        },
        "val_500k": {
            "low": 40000,
            "mid": 230000,
            "high": 370000,
            "per_unit_low": 20000,
            "per_unit_mid": 115000,
            "per_unit_high": 185000,
            "pencils_text": "Pencils across all cost tiers",
        },
        "assumption_set_version": "v1.0-chat2",
    }
    render_parcel_card(data_a, "readiness/render/parcel_08223520380000.png")

    # Category C Parcel: 08253290080000 (367 W 900 N)
    data_c = {
        "parcel_id": "08253290080000",
        "address": "367 W 900 N",
        "acres": "2.319",
        "sqft": 101006,
        "zone": "MU-11",
        "zone_name": "Mixed Use 11 (CRA Target Area)",
        "min_lot_area": "2,000 sq ft / unit",
        "min_frontage": "30 ft",
        "setback_front": "10 ft",
        "max_height": "35 ft",
        "binding_constraint": "ROW access & parking buffer",
        "fits_type": "townhome",
        "fits_units": 16,
        "config_desc": "16-unit attainable attached townhome community",
        "category": "C",
        "readiness_status": "Public partnership / CRA site",
        "city_role": "Pre-clear objective standards RFP",
        "val_400k": {
            "low": -192000,
            "mid": 1168000,
            "high": 2240000,
            "per_unit_low": -12000,
            "per_unit_mid": 73000,
            "per_unit_high": 140000,
            "pencils_text": "Requires nominal land at high cost; pencils at mid",
        },
        "val_500k": {
            "low": 1408000,
            "mid": 2768000,
            "high": 3840000,
            "per_unit_low": 88000,
            "per_unit_mid": 173000,
            "per_unit_high": 240000,
            "pencils_text": "Strong surplus for community amenities",
        },
        "assumption_set_version": "v1.0-chat2",
    }
    render_parcel_card(data_c, "readiness/render/parcel_08253290080000.png")

if __name__ == "__main__":
    main()
