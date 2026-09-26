#!/usr/bin/env python3
"""render_process.py — Generates process.png (1920x1080) for Hack-A-House 2026.
Depicts: Check -> Classify -> Pre-approve (C parcels, with the city) -> Offer with RFP starter.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

def create_process_slide(output_path="readiness/render/process.png"):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#0A0F1D")
    ax.axis("off")

    # Header / Title Banner
    ax.text(0.06, 0.92, "CADROS | COUNTY HOUSING READINESS LAB", fontsize=15, fontweight="bold", color="#38BDF8", family="sans-serif")
    ax.text(0.06, 0.85, "Public Land Activation Workflow", fontsize=38, fontweight="heavy", color="#F8FAFC", family="sans-serif")
    ax.text(0.06, 0.80, "From fragmented county public land records to pre-approved, builder-ready attainable housing RFPs", fontsize=18, color="#94A3B8", family="sans-serif")

    # 4 Steps Architecture
    steps = [
        {
            "num": "01",
            "name": "CHECK",
            "sub": "Record & Constraint Ingestion",
            "color": "#3B82F6",
            "points": [
                "Ingest county GIS & assessor records",
                "Verify public/agency ownership",
                "Screen dimensional geometry & access",
                "Filter flood, slope, & hazard overlays",
                "Map utility proximity & ROW connections"
            ],
            "badge": "Automated Screen"
        },
        {
            "num": "02",
            "name": "CLASSIFY",
            "sub": "Readiness Stratification",
            "color": "#10B981",
            "points": [
                "Category A: Clean By-Right infill",
                "Category B: Minor administrative relief",
                "Category C: City pre-approval needed",
                "Category D: Unbuildable / constrained",
                "Flag unknowns — no silent compliance"
            ],
            "badge": "Deterministic Triage"
        },
        {
            "num": "03",
            "name": "PRE-APPROVE",
            "sub": "City & CRA Partnership",
            "color": "#F59E0B",
            "points": [
                "Focus on Category C public parcels",
                "City locks objective standards checklist",
                "Pre-clear density & building envelopes",
                "Remove legislative hearing bottlenecks",
                "Enact administrative 60-day shot clock"
            ],
            "badge": "Intervention Core"
        },
        {
            "num": "04",
            "name": "OFFER WITH RFP",
            "sub": "Turnkey Builder Dispatch",
            "color": "#8B5CF6",
            "points": [
                "Deploy standardized RFP starter kit",
                "Prescribe attainable home targets ($400k-$500k)",
                "Residual land pricing solves for feasibility",
                "Require local builder deed-restrictions",
                "Predictable, shovel-ready groundbreak"
            ],
            "badge": "Market Delivery"
        }
    ]

    card_width = 0.20
    card_gap = 0.035
    start_x = 0.055
    card_y = 0.22
    card_height = 0.50

    for i, s in enumerate(steps):
        cx = start_x + i * (card_width + card_gap)
        
        # Draw Card Box
        rect = patches.FancyBboxPatch(
            (cx, card_y), card_width, card_height,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            linewidth=2,
            edgecolor=s["color"],
            facecolor="#131D31",
            zorder=2
        )
        ax.add_patch(rect)

        # Header bar inside card
        header_bar = patches.FancyBboxPatch(
            (cx, card_y + card_height - 0.10), card_width, 0.10,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            linewidth=0,
            facecolor="#1E293B",
            zorder=3
        )
        ax.add_patch(header_bar)

        # Card Step Number & Title
        ax.text(cx + 0.015, card_y + card_height - 0.045, s["num"], fontsize=20, fontweight="bold", color=s["color"], zorder=4)
        ax.text(cx + 0.045, card_y + card_height - 0.045, s["name"], fontsize=22, fontweight="heavy", color="#FFFFFF", zorder=4)
        ax.text(cx + 0.015, card_y + card_height - 0.078, s["sub"], fontsize=11, fontweight="medium", color="#94A3B8", zorder=4)

        # Badge
        badge_box = patches.FancyBboxPatch(
            (cx + card_width - 0.085, card_y + card_height - 0.045), 0.075, 0.025,
            boxstyle="round,pad=0.005,rounding_size=0.008",
            linewidth=1,
            edgecolor=s["color"],
            facecolor=s["color"] + "22",
            zorder=4
        )
        ax.add_patch(badge_box)
        ax.text(cx + card_width - 0.0475, card_y + card_height - 0.033, s["badge"], fontsize=8, fontweight="bold", color=s["color"], ha="center", va="center", zorder=5)

        # Bullet Points
        bullet_y = card_y + card_height - 0.14
        for p in s["points"]:
            ax.plot([cx + 0.018], [bullet_y], marker="o", markersize=5, color=s["color"], zorder=4)
            ax.text(cx + 0.030, bullet_y - 0.006, p, fontsize=12.5, color="#E2E8F0", family="sans-serif", zorder=4)
            bullet_y -= 0.065

        # Arrow between cards
        if i < len(steps) - 1:
            arrow_start_x = cx + card_width + 0.006
            arrow_end_x = arrow_start_x + card_gap - 0.012
            arrow_y = card_y + card_height / 2
            ax.annotate(
                "",
                xy=(arrow_end_x, arrow_y),
                xytext=(arrow_start_x, arrow_y),
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color="#38BDF8", lw=3.5),
                zorder=5
            )

    # Footer
    footer_rect = patches.Rectangle((0, 0), 1, 0.12, facecolor="#070B14", zorder=1)
    ax.add_patch(footer_rect)
    ax.plot([0, 1], [0.12, 0.12], color="#1E293B", lw=1.5, zorder=2)

    ax.text(0.06, 0.065, "KEY INNOVATION", fontsize=11, fontweight="bold", color="#38BDF8")
    ax.text(0.06, 0.035, "De-risking public land development before RFP issuance: city absorbs entitlement uncertainty so builders compete on speed and affordability, not discretionary zoning battles.", fontsize=13, color="#CBD5E1")

    ax.text(0.94, 0.05, "Cadros Command Architecture · Hack-A-House 2026", fontsize=12, color="#64748B", ha="right")

    plt.savefig(output_path, dpi=100)
    plt.close()
    print(f"Rendered {output_path} (1920x1080)")

if __name__ == "__main__":
    create_process_slide()
