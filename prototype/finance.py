"""Financial engine — simple deterministic pro forma (build plan §4).

The model never calculates the pro forma in free text: it chooses scenarios
(here: fixed config) and this module computes. All assumptions are explicit
and overridable via finance JSON config.
"""
from __future__ import annotations

from typing import Dict

from .schema import ProForma, Scheme


def run_proforma(scheme: Scheme, finance: Dict) -> ProForma:
    required = ("sale_price_per_lot", "road_cost_per_lf", "soft_costs_fixed")
    missing = [k for k in required if k not in finance]
    if missing:
        raise ValueError(
            f"finance config missing required keys: {', '.join(missing)}"
        )
    price = float(finance["sale_price_per_lot"])
    road_cost = float(finance["road_cost_per_lf"])
    soft = float(finance["soft_costs_fixed"])
    contingency_pct = float(finance.get("contingency_pct", 0.0))
    for label, val in (("sale_price_per_lot", price),
                       ("road_cost_per_lf", road_cost),
                       ("soft_costs_fixed", soft),
                       ("contingency_pct", contingency_pct)):
        if val < 0:
            raise ValueError(
                f"finance config has negative {label}: {val} — refusing to price"
            )

    n = len(scheme.lots)
    road_len = sum(r.length_ft for r in scheme.roads)

    revenue = n * price
    infra = road_len * road_cost
    subtotal = infra + soft
    contingency = subtotal * contingency_pct
    total = subtotal + contingency
    profit = revenue - total
    margin = profit / revenue if revenue else 0.0

    return ProForma(
        scheme_id=scheme.scheme_id,
        assumptions={
            "sale_price_per_lot": price,
            "road_cost_per_lf": road_cost,
            "soft_costs_fixed": soft,
            "contingency_pct": contingency_pct,
            "road_length_ft": round(road_len, 1),
            "source": finance.get("source", "inputs/finance.json"),
        },
        lot_count=n,
        revenue=round(revenue, 2),
        infra_cost=round(infra, 2),
        soft_costs=round(soft, 2),
        contingency=round(contingency, 2),
        total_cost=round(total, 2),
        profit=round(profit, 2),
        margin=round(margin, 4),
    )
