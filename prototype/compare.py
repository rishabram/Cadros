"""Comparison — rank schemes by profit then yield; print table + CSV."""
from __future__ import annotations

import csv
from typing import Dict, List

from .schema import ProForma, Scheme
from .validation import CheckResult


def rank(schemes: List[Scheme], proformas: Dict[str, ProForma]) -> List[Scheme]:
    return sorted(
        schemes, key=lambda s: (-proformas[s.scheme_id].profit, -len(s.lots))
    )


def comparison_table(
    ranked: List[Scheme],
    proformas: Dict[str, ProForma],
    validations: Dict[str, List[CheckResult]],
) -> str:
    rows = []
    header = (
        f"{'scheme':<10} {'lots':>4} {'road_ft':>8} {'revenue':>12} "
        f"{'total_cost':>12} {'profit':>12} {'margin':>7} {'checks':>12}"
    )
    rows.append(header)
    rows.append("-" * len(header))
    for s in ranked:
        p = proformas[s.scheme_id]
        v = validations[s.scheme_id]
        fails = sum(1 for r in v if r.status == "fail")
        warns = sum(1 for r in v if r.status == "warning")
        status = "clean" if fails == 0 and warns == 0 else f"{fails}F/{warns}W"
        rows.append(
            f"{s.scheme_id:<10} {len(s.lots):>4} "
            f"{sum(r.length_ft for r in s.roads):>8.0f} "
            f"${p.revenue:>11,.0f} ${p.total_cost:>11,.0f} "
            f"${p.profit:>11,.0f} {p.margin:>6.1%} {status:>12}"
        )
    return "\n".join(rows)


def write_comparison_csv(
    path: str,
    ranked: List[Scheme],
    proformas: Dict[str, ProForma],
    validations: Dict[str, List[CheckResult]],
) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "scheme_id", "lots", "road_ft", "angle_deg", "road_offset_frac",
                "revenue", "infra_cost", "soft_costs", "contingency",
                "total_cost", "profit", "margin", "checks_fail", "checks_warning",
            ]
        )
        for s in ranked:
            p = proformas[s.scheme_id]
            v = validations[s.scheme_id]
            w.writerow(
                [
                    s.scheme_id, len(s.lots),
                    round(sum(r.length_ft for r in s.roads), 1),
                    s.params.get("angle_deg"), s.params.get("road_offset_frac"),
                    p.revenue, p.infra_cost, p.soft_costs, p.contingency,
                    p.total_cost, p.profit, p.margin,
                    sum(1 for r in v if r.status == "fail"),
                    sum(1 for r in v if r.status == "warning"),
                ]
            )
