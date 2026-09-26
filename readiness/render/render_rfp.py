#!/usr/bin/env python3
"""render_rfp.py — Generates rfp_excerpt.png (1920x1080) for Hack-A-House 2026.
Depicts Soarer's RFP template filled in for Category C parcel (367 W 900 N / Parcel 08253290080000).
Every number matches readiness/out/land_value_slc.csv.
"""

from __future__ import annotations

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def render_rfp_slide(output_png="readiness/render/rfp_excerpt.png", run_id="RUN-20260925-LANDVALUE"):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#080D1A")
    ax.axis("off")

    # Header
    ax.text(0.06, 0.93, "CADROS | MUNICIPAL RFP STARTER TEMPLATE", fontsize=14, fontweight="bold", color="#F59E0B")
    ax.text(0.06, 0.86, "City-Sponsored Attainable Housing RFP Excerpt", fontsize=34, fontweight="heavy", color="#F8FAFC")
    ax.text(0.06, 0.81, "Pre-Approved Category C Public Site · Pre-Engineered Dimensional Envelope & Residual Land Pricing", fontsize=16, color="#94A3B8")

    # Document Container
    doc_x = 0.055
    doc_y = 0.11
    doc_w = 0.89
    doc_h = 0.67

    doc_rect = patches.FancyBboxPatch(
        (doc_x, doc_y), doc_w, doc_h,
        boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=2,
        edgecolor="#F59E0B",
        facecolor="#0F172A",
        zorder=2
    )
    ax.add_patch(doc_rect)

    # Document Header Band
    doc_header = patches.FancyBboxPatch(
        (doc_x, doc_y + doc_h - 0.09), doc_w, 0.09,
        boxstyle="round,pad=0.015,rounding_size=0.015",
        linewidth=0,
        facecolor="#1E293B",
        zorder=3
    )
    ax.add_patch(doc_header)

    ax.text(doc_x + 0.02, doc_y + doc_h - 0.038, "SALT LAKE CITY REDEVELOPMENT AGENCY (CRA) & HOUSING LAB", fontsize=13, fontweight="bold", color="#F8FAFC", zorder=4)
    ax.text(doc_x + 0.02, doc_y + doc_h - 0.065, "RFP # 2026-SLC-HAH-008 · PUBLIC PARCEL DEVELOPMENT SOLICITATION", fontsize=11, color="#94A3B8", zorder=4)

    # Status Badge
    badge = patches.FancyBboxPatch(
        (doc_x + doc_w - 0.22, doc_y + doc_h - 0.062), 0.20, 0.035,
        boxstyle="round,pad=0.005,rounding_size=0.008",
        linewidth=1,
        edgecolor="#10B981",
        facecolor="#10B98122",
        zorder=4
    )
    ax.add_patch(badge)
    ax.text(doc_x + doc_w - 0.12, doc_y + doc_h - 0.045, "PRE-APPROVED SITE", fontsize=11, fontweight="bold", color="#10B981", ha="center", va="center", zorder=5)

    # Left Column: Site & Program Specification
    left_x = doc_x + 0.025
    left_w = 0.40
    col_y = doc_y + 0.03
    col_h = doc_h - 0.13

    left_box = patches.FancyBboxPatch(
        (left_x, col_y), left_w, col_h,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        linewidth=1,
        edgecolor="#334155",
        facecolor="#131D31",
        zorder=3
    )
    ax.add_patch(left_box)

    ax.text(left_x + 0.02, col_y + col_h - 0.035, "1. SITE & DEVELOPMENT SPECIFICATION", fontsize=13, fontweight="bold", color="#38BDF8", zorder=4)
    ax.plot([left_x + 0.02, left_x + left_w - 0.02], [col_y + col_h - 0.048, col_y + col_h - 0.048], color="#1E293B", lw=1, zorder=4)

    specs = [
        ("Property Location", "367 W 900 N, Salt Lake City, UT 84103"),
        ("Parcel Identifier", "08253290080000 (Salt Lake County Assessor)"),
        ("Site Acreage / Area", "2.319 Acres (101,006 sq ft) · Flat topography"),
        ("Zoning Classification", "MU-11 (Mixed Use High Density Residential)"),
        ("Pre-Approved Typology", "16 Attainable Townhome Units (Attached cluster)"),
        ("Dimensional Standard", "Pre-screened against Title 21A setbacks & height"),
        ("Infrastructure Access", "Direct curb, gutter, sewer & culinary water in ROW"),
        ("Permit Pathway", "60-Day Administrative Shot Clock (By-right track)"),
        ("Hearing Requirement", "Zero discretionary City Council hearings required"),
    ]

    sy = col_y + col_h - 0.08
    for label, val in specs:
        ax.text(left_x + 0.02, sy, label + ":", fontsize=10.5, fontweight="bold", color="#94A3B8", zorder=4)
        ax.text(left_x + 0.02, sy - 0.024, val, fontsize=11, color="#F8FAFC", zorder=4)
        sy -= 0.052

    # Right Column: Financial Terms & Evaluation Gates
    right_x = doc_x + 0.45
    right_w = 0.415

    right_box = patches.FancyBboxPatch(
        (right_x, col_y), right_w, col_h,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        linewidth=1,
        edgecolor="#334155",
        facecolor="#131D31",
        zorder=3
    )
    ax.add_patch(right_box)

    ax.text(right_x + 0.02, col_y + col_h - 0.035, "2. ATTAINABLE PRICING & LAND OFFERING BASIS", fontsize=13, fontweight="bold", color="#38BDF8", zorder=4)
    ax.plot([right_x + 0.02, right_x + right_w - 0.02], [col_y + col_h - 0.048, col_y + col_h - 0.048], color="#1E293B", lw=1, zorder=4)

    terms = [
        ("Target Unit Price Point", "$400,000 (Tier 1) or $500,000 (Tier 2) Maximum Sales Price"),
        ("Land Value at $400k Target", "$1,168,000 Mid ($73,000/unit) · Range: -$192k to $2,240,000"),
        ("Negative Value Policy", "If high costs yield negative land value, City conveys land at $0"),
        ("Land Value at $500k Target", "$2,768,000 Mid ($173,000/unit) · Range: $1,408k to $3,840,000"),
        ("Builder Margin Policy", "Assumes standard market builder overhead & return (12-15%)"),
        ("Affordability Covenant", "30-year deed restriction for buyers at or below 80% AMI"),
        ("Developer Submission", "Proposals scored on speed-to-groundbreak & design quality"),
        ("Execution Milestone", "Building permit submission within 90 days of award"),
    ]

    ty = col_y + col_h - 0.08
    for label, val in terms:
        ax.text(right_x + 0.02, ty, label + ":", fontsize=10.5, fontweight="bold", color="#94A3B8", zorder=4)
        ax.text(right_x + 0.02, ty - 0.024, val, fontsize=11, color="#F8FAFC", zorder=4)
        ty -= 0.052

    # Footer
    ax.plot([0.055, 0.95], [0.07, 0.07], color="#1E293B", lw=1.5)
    ax.text(0.055, 0.035, f"Run {run_id} · Template Authorized by Soarer (CCO) & Cadros Readiness Lab", fontsize=11, fontweight="bold", color="#38BDF8")
    ax.text(0.95, 0.035, "Audit-ready slide export · Overseer drop-in compatible", fontsize=11, color="#64748B", ha="right")

    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    plt.savefig(output_png, dpi=100)
    plt.close()
    print(f"Rendered {output_png} (1920x1080)")

if __name__ == "__main__":
    render_rfp_slide()
