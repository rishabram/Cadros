"""Adapter: pipeline schemes -> RuleGraph context contract.

The subdivision pipeline produces lot/road geometry; the verified rules need
building-program and site facts (heights, stories, setbacks, streets,
abutments). This adapter maps what the pipeline genuinely knows and leaves
everything else None (-> UNKNOWN), with provenance recording exactly which
upstream source would supply each missing attribute.

The building program may carry a top-level "schemes" map (scheme id ->
program dict). split_program() pops it from the base program and
program_for_scheme() merges the per-scheme override over the base facts for
each scheme. Without a "schemes" map, the base program applies to every
scheme, exactly as before.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# The full RuleGraph context contract, in stable order.
CONTRACT_ATTRS: List[str] = [
    "district",
    "lot_abuts_sf_tf_residential",
    "landscape_buffer_provided",
    "building_form",
    "stories",
    "height_ft",
    "design_review_completed",
    "in_height_bonus_area",
    "open_space_ground_pct",
    "enhanced_active_use_100_pct",
    "midblock_walkway_ft",
    "front_setback_ft",
    "front_street",
    "front_street_within_listed_segment",
    "corner_side_setback_ft",
    "corner_street",
    "corner_street_within_listed_segment",
    "interior_side_setback_ft",
    "interior_abuts_listed_zone",
    "abuts_zones_side",
    "rear_setback_ft",
    "rear_abuts_listed_zone",
    "abuts_zones_rear",
    "is_corner_lot",
    # Caddy extraction v2 overlay (rulegraph/caddy_params_v2.json) — facts
    # the new MU evaluators read. Absent -> None -> UNKNOWN, as before.
    "building_forms",
    "ground_floor_use",
    # Caddy extraction v1 overlay (rulegraph/caddy_params_v1.json) — facts
    # the new M-1/OS/PL evaluators read. Absent -> None -> UNKNOWN, as before.
    "proposed_use_is_public_school",
    "proposed_use_pl_civic_listed",
    "has_recreation_equipment",
    "recreation_equipment_height_ft",
    "is_distillation_column_structure",
    "faa_max_elevation_ft",
    "in_m1_height_exception_zone",
    "is_slc_public_utilities_structure",
]

# Where each attribute would come from when the pipeline cannot supply it.
GAP_NOTES: Dict[str, str] = {
    "district": "zoning config 'district' or parcel jurisdiction lookup",
    "lot_abuts_sf_tf_residential": "neighbor-zone GIS overlay (abutment analysis)",
    "landscape_buffer_provided": "building program / site plan",
    "building_form": "building program",
    "building_forms": "building program (list of building forms proposed on the lot)",
    "ground_floor_use": "building program (ground-floor occupancy: 'residential' or 'non-residential')",
    "stories": "building program (story-by-story uses)",
    "height_ft": "building program (proposed building height)",
    "design_review_completed": "entitlement tracker",
    "in_height_bonus_area": "parcel geolocation vs MU-11 bonus-area polygons",
    "open_space_ground_pct": "site plan",
    "enhanced_active_use_100_pct": "site plan / use program",
    "midblock_walkway_ft": "site plan",
    "front_setback_ft": "building footprints + parcel boundary",
    "front_street": "street centerline names at parcel frontage",
    "front_street_within_listed_segment": "street segment data (1700/2100 South, West Temple to I-15)",
    "corner_side_setback_ft": "building footprints + parcel boundary",
    "corner_street": "street centerline names at parcel corner frontage",
    "corner_street_within_listed_segment": "street segment data (1700/2100 South, West Temple to I-15)",
    "interior_side_setback_ft": "building footprints + parcel boundary",
    "interior_abuts_listed_zone": "neighbor-zone GIS overlay (abutment analysis)",
    "abuts_zones_side": "building program (abutment survey) or neighbor-zone GIS overlay: zone codes abutting the interior side",
    "rear_setback_ft": "building footprints + parcel boundary",
    "rear_abuts_listed_zone": "neighbor-zone GIS overlay (abutment analysis)",
    "abuts_zones_rear": "building program (abutment survey) or neighbor-zone GIS overlay: zone codes abutting the rear",
    "is_corner_lot": "parcel boundary + street centerline intersections (corner detection)",
    "proposed_use_is_public_school": "building program (proposed use)",
    "proposed_use_pl_civic_listed": "building program (proposed use vs the PL-02 civic list)",
    "has_recreation_equipment": "site plan / building program",
    "recreation_equipment_height_ft": "site plan / building program",
    "is_distillation_column_structure": "building program (structure type)",
    "faa_max_elevation_ft": "FAA approach-surface data for the parcel",
    "in_m1_height_exception_zone": "parcel geolocation vs airport/I-80 polygons",
    "is_slc_public_utilities_structure": "building program (applicant/owner)",
}


# Program keys owned by another evaluator (the use-allowance adapter's
# "proposed_uses"). Accepted by the typo guard below, ignored by RuleGraph
# context building: one shared building program feeds both evaluators, so a
# key that is legitimate for the sibling evaluator must not trip this
# adapter's unknown-key guard. Truly unknown keys still raise loudly.
FOREIGN_PROGRAM_KEYS = ("proposed_uses",)


def build_context(
    zoning_cfg: Dict | None = None,
    program: Dict | None = None,
    program_source: str = "building program",
) -> Tuple[Dict, Dict]:
    """Build a RuleGraph context from pipeline-known facts + optional program.

    Returns (context, provenance). Provenance maps each attribute to
    ("known", source) or ("unknown", gap_note). Unknown program keys raise
    ValueError — a typo'd program file must be loud, not silently ignored.
    """
    context: Dict = {a: None for a in CONTRACT_ATTRS}
    provenance: Dict = {a: ("unknown", GAP_NOTES[a]) for a in CONTRACT_ATTRS}

    if zoning_cfg:
        district = zoning_cfg.get("district")
        if district is not None:
            context["district"] = district
            provenance["district"] = ("known", "zoning config 'district'")

    if program:
        unknown_keys = [k for k in program if not k.startswith("_") and k not in CONTRACT_ATTRS and k not in FOREIGN_PROGRAM_KEYS]
        if unknown_keys:
            raise ValueError(
                f"building program has unknown attributes: {', '.join(sorted(unknown_keys))} "
                f"— fix the program file; nothing was evaluated"
            )
        for attr in CONTRACT_ATTRS:
            if attr in program and program[attr] is not None:
                context[attr] = program[attr]
                provenance[attr] = ("known", f"{program_source}")

    return context, provenance


def summarize_gaps(provenances: List[Dict]) -> List[Dict]:
    """Attributes unknown in EVERY scheme: the punch list for meaningful verdicts."""
    gaps = []
    for attr in CONTRACT_ATTRS:
        if all(p[attr][0] == "unknown" for p in provenances):
            gaps.append({"attribute": attr, "needed_from": GAP_NOTES[attr]})
    return gaps


def split_program(program: Dict | None) -> Tuple[Dict | None, Dict]:
    """Split a per-scheme "schemes" map off the base building program.

    Returns (base_program, schemes_map). The "schemes" key is popped from the
    base so it never reaches build_context()'s typo guard; the map itself is
    {scheme_id: program-dict override}. A non-dict "schemes" value raises
    ValueError (loud). Returns (program, {}) when there is no "schemes" key —
    the base program then applies to every scheme, as before.
    """
    if not program:
        return None, {}
    base = dict(program)
    schemes_map = base.pop("schemes", None) or {}
    if not isinstance(schemes_map, dict):
        raise ValueError(
            "'schemes' in the building program must be a map of "
            "scheme id -> program dict; nothing was evaluated"
        )
    for scheme_id, override in schemes_map.items():
        if not isinstance(override, dict):
            raise ValueError(
                f"building program schemes[{scheme_id!r}] must be a dict of "
                "program attributes; nothing was evaluated"
            )
    return base, schemes_map


def program_for_scheme(
    base_program: Dict | None, schemes_map: Dict, scheme_id: str
) -> Dict | None:
    """Merged program for one scheme: the scheme's override over the base.

    Returns base_program UNCHANGED (same object) when the scheme has no
    override, so callers can share one built context across schemes. Override
    values win over base values; base keys not mentioned survive. A nested
    "schemes" key inside an override is left in place on purpose — it is not
    a valid context attribute and build_context() will reject it loudly.
    """
    override = schemes_map.get(scheme_id)
    if not override:
        return base_program
    merged = dict(base_program or {})
    merged.update(override)
    return merged
