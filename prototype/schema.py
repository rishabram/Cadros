"""PlanGraph schema — Pydantic subset of the company data model (build plan §2).

Coordinates are [x, y] pairs in a planar CRS documented per-input
(README + input files). Demo inputs use US survey feet in a local frame.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from pydantic import BaseModel, Field

Coord = List[float]  # [x, y]


class Parcel(BaseModel):
    parcel_id: str
    boundary: List[Coord]
    crs: str = "local-feet"
    source: str = "synthetic-demo"


class Lot(BaseModel):
    lot_id: str
    polygon: List[Coord]
    area_sqft: float
    frontage_ft: float


class Road(BaseModel):
    road_id: str
    centerline: List[Coord]
    width_ft: float
    length_ft: float


class RuleBinding(BaseModel):
    """A jurisdictional rule as a versioned, testable constraint (RuleGraph §3)."""

    rule_id: str
    description: str
    operator: str  # e.g. ">=", "=="
    value: float
    unit: str
    source: str  # where the rule came from + effective date if known


class CheckResult(BaseModel):
    rule_id: str
    status: str  # "pass" | "fail" | "warning"
    detail: str


class Scheme(BaseModel):
    scheme_id: str
    parcel_id: str
    lots: List[Lot] = Field(default_factory=list)
    roads: List[Road] = Field(default_factory=list)
    params: Dict[str, Any] = Field(default_factory=dict)  # seed params
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    fingerprint: str = ""


class ProForma(BaseModel):
    scheme_id: str
    assumptions: Dict[str, Any]
    lot_count: int
    revenue: float
    infra_cost: float
    soft_costs: float
    contingency: float
    total_cost: float
    profit: float
    margin: float  # profit / revenue


def fingerprint_geometry(scheme: Scheme) -> str:
    """Stable content hash of scheme geometry (tamper / provenance checks)."""
    canon = {
        "lots": [[round(x, 3), round(y, 3)] for lot in scheme.lots for x, y in lot.polygon],
        "roads": [[round(x, 3), round(y, 3)] for r in scheme.roads for x, y in r.centerline],
    }
    return hashlib.sha256(json.dumps(canon, sort_keys=True).encode()).hexdigest()[:16]
