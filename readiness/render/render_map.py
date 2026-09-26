#!/usr/bin/env python3
"""render_map.py — Generates map.png (1920x1080) for Hack-A-House 2026.
Colors SLC public parcels:
  A: green (#10B981)
  B: yellow (#FBBF24)
  C: orange (#F97316)
  D: grey (#64748B)
  UNKNOWN: hatched (#94A3B8)
Includes legend and footer: "Run RUN-20260925-READINESS · <date> · N parcels".
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import shape

COLORS = {
    "A": "#10B981",       # Green
    "B": "#FBBF24",       # Yellow
    "C": "#F97316",       # Orange
    "D": "#64748B",       # Grey
    "UNKNOWN": "#94A3B8", # Hatched
}

def render_map(
    readiness_csv_path="readiness/out/readiness_slc.csv",
    parcels_geojson_path="screen/real_parcels/parcel_index.geojson",
    output_png="readiness/render/map.png",
    run_id="RUN-20260925-READINESS",
):
    if not os.path.exists(parcels_geojson_path):
        print(f"Error: {parcels_geojson_path} not found", file=sys.stderr)
        return False

    with open(parcels_geojson_path) as f:
        fc = json.load(f)

    # Load classification if available
    classifications = {}
    if os.path.exists(readiness_csv_path):
        with open(readiness_csv_path) as f:
            reader = csv.DictReader(f)
            for r in reader:
                pid = r.get("parcel_id") or r.get("id")
                cat = (r.get("category") or r.get("tier") or "UNKNOWN").strip().upper()
                if cat not in COLORS:
                    cat = "UNKNOWN"
                if pid:
                    classifications[pid] = cat

    # Figure 1920x1080 (19.2 x 10.8 inches at 100 dpi)
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#080D1A")

    # Header
    ax.text(0.05, 0.94, "CADROS | SALT LAKE CITY PUBLIC PARCEL READINESS MAP", fontsize=15, fontweight="bold", color="#38BDF8")
    ax.text(0.05, 0.89, "Municipal Land Attainable Housing Screen", fontsize=32, fontweight="heavy", color="#F8FAFC")
    ax.text(0.05, 0.85, "Spatial distribution of public land parcels triaged by by-right feasibility and pre-approval readiness", fontsize=16, color="#94A3B8")

    # Map area coordinates setup
    map_ax = fig.add_axes([0.05, 0.12, 0.65, 0.70])
    map_ax.set_facecolor("#0F172A")
    map_ax.tick_params(colors="#64748B", labelsize=9)
    for spine in map_ax.spines.values():
        spine.set_color("#334155")

    counts = {"A": 0, "B": 0, "C": 0, "D": 0, "UNKNOWN": 0}
    total_parcels = 0

    all_polys = []
    for feat in fc["features"]:
        geom = shape(feat["geometry"])
        pid = feat["properties"].get("parcel_id", "")
        cat = classifications.get(pid, "UNKNOWN")
        counts[cat] = counts.get(cat, 0) + 1
        total_parcels += 1

        color = COLORS.get(cat, COLORS["UNKNOWN"])
        is_unknown = (cat == "UNKNOWN")

        if geom.geom_type == "Polygon":
            geoms = [geom]
        elif geom.geom_type == "MultiPolygon":
            geoms = list(geom.geoms)
        else:
            continue

        for poly in geoms:
            xs, ys = poly.exterior.xy
            all_polys.append(poly)
            if is_unknown:
                map_ax.fill(xs, ys, facecolor="#1E293B", edgecolor=color, hatch="//", linewidth=0.8, alpha=0.9)
            else:
                map_ax.fill(xs, ys, facecolor=color, edgecolor="#FFFFFF", linewidth=0.6, alpha=0.85)

    if all_polys:
        from shapely.ops import unary_union
        bounds = unary_union(all_polys).bounds
        padx = (bounds[2] - bounds[0]) * 0.05
        pady = (bounds[3] - bounds[1]) * 0.05
        map_ax.set_xlim(bounds[0] - padx, bounds[2] + padx)
        map_ax.set_ylim(bounds[1] - pady, bounds[3] + pady)

    map_ax.set_xlabel("State Plane Easting (EPSG:3566 ftUS)", color="#94A3B8", fontsize=11)
    map_ax.set_ylabel("State Plane Northing (EPSG:3566 ftUS)", color="#94A3B8", fontsize=11)

    # Right Side: Legend & Statistics Panel
    panel_x = 0.73
    panel_w = 0.22
    panel_y = 0.12
    panel_h = 0.70

    panel_rect = patches.FancyBboxPatch(
        (panel_x, panel_y), panel_w, panel_h,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        linewidth=1.5,
        edgecolor="#334155",
        facecolor="#131D31"
    )
    ax.add_patch(panel_rect)

    ax.text(panel_x + 0.015, panel_y + panel_h - 0.04, "READINESS TIERS", fontsize=16, fontweight="bold", color="#F8FAFC")
    ax.text(panel_x + 0.015, panel_y + panel_h - 0.065, "Classification & counts", fontsize=11, color="#94A3B8")

    legend_items = [
        ("A", "Category A (Clean By-Right)", "Meets all zoning/dimensional standards without discretionary variance", COLORS["A"], counts["A"]),
        ("B", "Category B (Minor Relief)", "Minor dimensional relief or administrative adjustment needed", COLORS["B"], counts["B"]),
        ("C", "Category C (Pre-Approval)", "Public partnership / CRA site; pre-cleared by city for housing RFP", COLORS["C"], counts["C"]),
        ("D", "Category D (Constrained)", "Severe physical, access, or environmental impediments", COLORS["D"], counts["D"]),
        ("UNKNOWN", "UNKNOWN (Unverified)", "Missing utility, hazard, or cadastral boundary data", COLORS["UNKNOWN"], counts["UNKNOWN"]),
    ]

    item_y = panel_y + panel_h - 0.11
    for cat_id, title, desc, col, count in legend_items:
        # Patch icon
        if cat_id == "UNKNOWN":
            p = patches.Rectangle((panel_x + 0.015, item_y - 0.015), 0.02, 0.02, facecolor="#1E293B", edgecolor=col, hatch="//", linewidth=1.5)
        else:
            p = patches.Rectangle((panel_x + 0.015, item_y - 0.015), 0.02, 0.02, facecolor=col, edgecolor="#FFFFFF", linewidth=1)
        ax.add_patch(p)

        ax.text(panel_x + 0.042, item_y, title, fontsize=12, fontweight="bold", color="#F1F5F9")
        ax.text(panel_x + panel_w - 0.015, item_y, f"{count}", fontsize=13, fontweight="bold", color=col, ha="right")
        
        # Word wrap desc
        ax.text(panel_x + 0.015, item_y - 0.035, desc, fontsize=9.5, color="#94A3B8")
        item_y -= 0.105

    # Footer
    date_str = datetime.now().strftime("%Y-%m-%d")
    footer_text = f"Run {run_id} · {date_str} · {total_parcels} parcels"
    ax.plot([0.05, 0.95], [0.08, 0.08], color="#1E293B", lw=1.5)
    ax.text(0.05, 0.045, footer_text, fontsize=13, fontweight="bold", color="#38BDF8")
    ax.text(0.95, 0.045, "Salt Lake County Public Land Dataset · Cadros Platform Delivery", fontsize=11, color="#64748B", ha="right")

    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    plt.savefig(output_png, dpi=100)
    plt.close()
    print(f"Rendered {output_png} (1920x1080)")
    return True

if __name__ == "__main__":
    render_map()
