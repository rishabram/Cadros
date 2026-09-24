"""RuleGraph v1 predicates: three-valued (PASS / FAIL / UNKNOWN) evaluators.

Core contract: missing information NEVER defaults to compliance. Any input the
evaluator needs but the context does not supply yields UNKNOWN, never PASS.
"""
from enum import Enum


class Outcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


def _known(value):
    """True when a context value is actually supplied (None means unknown)."""
    return value is not None


def pl_landscape_buffer(params, ctx):
    """PL-04: buffer required when a PL lot abuts single/two-family residential."""
    abuts = ctx.get("lot_abuts_sf_tf_residential")
    if not _known(abuts):
        return Outcome.UNKNOWN, "unknown whether the lot abuts a single/two-family residential district"
    if not abuts:
        return Outcome.PASS, "lot does not abut a single/two-family residential district; rule not triggered"
    provided = ctx.get("landscape_buffer_provided")
    if not _known(provided):
        return Outcome.UNKNOWN, "lot abuts single/two-family residential but buffer status is unknown"
    if provided:
        return Outcome.PASS, "required Ch. 21A.48 landscape buffer is provided"
    return Outcome.FAIL, "lot abuts single/two-family residential but no Ch. 21A.48 landscape buffer"


def mu11_uses_per_story(params, ctx):
    """MU-11-05: row house — residential on all stories; live/work ground level only."""
    form = ctx.get("building_form")
    if not _known(form):
        return Outcome.UNKNOWN, "building form is unknown"
    if form not in params["applies_to_forms"]:
        return Outcome.PASS, f"rule applies to {params['applies_to_forms']}; form is {form}"
    stories = ctx.get("stories")
    if not stories:
        return Outcome.UNKNOWN, "story-by-story uses are unknown"
    levels = [s.get("level") for s in stories if _known(s.get("level"))]
    if not levels:
        return Outcome.UNKNOWN, "story levels are unknown"
    ground = min(levels)
    for s in stories:
        use = s.get("use")
        level = s.get("level")
        if not _known(use) or not _known(level):
            return Outcome.UNKNOWN, "a story has unknown level or use"
        if level == ground:
            if use not in params["allowed_ground_uses"]:
                return Outcome.FAIL, f"ground-level story use is {use!r}; only {params['allowed_ground_uses']} allowed"
        else:
            if use not in params["allowed_non_ground_uses"]:
                return Outcome.FAIL, f"non-ground story use is {use!r}; only residential allowed"
    return Outcome.PASS, "residential on all stories; live/work on ground level only"


def _bonus_conditions(bp, ctx):
    """Shared MU-11-07 bonus logic: assumes 125 < height <= 150 already checked."""
    in_area = ctx.get("in_height_bonus_area")
    if not _known(in_area):
        return Outcome.UNKNOWN, "bonus-area membership is unknown"
    if not in_area:
        return Outcome.FAIL, "outside the height bonus areas"
    dr = ctx.get("design_review_completed")
    if not _known(dr):
        return Outcome.UNKNOWN, "design-review status is unknown"
    if not dr:
        return Outcome.FAIL, "bonus height requires Chapter 21A.59 design review"
    os_pct = ctx.get("open_space_ground_pct")
    if not _known(os_pct):
        return Outcome.UNKNOWN, "ground-level open-space percentage is unknown"
    if os_pct < bp["open_space_min_pct"]:
        return Outcome.FAIL, f"open space {os_pct}% below required {bp['open_space_min_pct']}%"
    active = ctx.get("enhanced_active_use_100_pct")
    walkway = ctx.get("midblock_walkway_ft")
    if active:
        return Outcome.PASS, "design review, open space, and 100% enhanced active use"
    if _known(walkway) and walkway >= bp["walkway_min_ft"]:
        return Outcome.PASS, f"design review, open space, and {walkway} ft midblock walkway"
    if not _known(active) or not _known(walkway):
        return Outcome.UNKNOWN, "neither 100% enhanced active use nor walkway width is established"
    return Outcome.FAIL, "bonus requires 100% enhanced active use or a 20 ft midblock walkway"


def mu11_max_height(params, ctx):
    """MU-11-06: 125 ft max, qualified by the MU-11-07 additional-height bonus.

    The table's "Maximum: 125 feet" and the "Additional Height" row are one
    height regulation: 125 ft by right, up to 150 ft where the bonus applies.
    """
    h = ctx.get("height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, "building height is unknown"
    base = params["max_ft"]
    bp = params["bonus"]
    if h > bp["bonus_max_ft"]:
        return Outcome.FAIL, f"height {h} ft exceeds bonus maximum {bp['bonus_max_ft']} ft"
    if h > base:
        oc, reason = _bonus_conditions(bp, ctx)
        if oc == Outcome.PASS:
            return Outcome.PASS, f"height {h} ft within 150 ft bonus ({reason})"
        if oc == Outcome.FAIL:
            return Outcome.FAIL, f"height {h} ft exceeds base maximum {base} ft and {reason}"
        return Outcome.UNKNOWN, f"height {h} ft exceeds base maximum {base} ft and {reason}"
    if h > params["design_review_threshold_ft"]:
        dr = ctx.get("design_review_completed")
        if not _known(dr):
            return Outcome.UNKNOWN, f"height {h} ft exceeds {params['design_review_threshold_ft']} ft but design-review status is unknown"
        if dr:
            return Outcome.PASS, f"height {h} ft within maximum; design review completed"
        return Outcome.FAIL, f"height {h} ft exceeds {params['design_review_threshold_ft']} ft without design review"
    return Outcome.PASS, f"height {h} ft within maximum; no design review required"


def mu11_additional_height(params, ctx):
    """MU-11-07: up to 150 ft in the two bonus areas via design review + conditions."""
    h = ctx.get("height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, "building height is unknown"
    base, bonus = params["base_max_ft"], params["bonus_max_ft"]
    if h <= base:
        return Outcome.PASS, f"height {h} ft within base maximum {base} ft; bonus provisions not triggered"
    if h > bonus:
        return Outcome.FAIL, f"height {h} ft exceeds bonus maximum {bonus} ft"
    oc, reason = _bonus_conditions(params, ctx)
    if oc == Outcome.PASS:
        return Outcome.PASS, f"150 ft bonus satisfied: {reason}"
    return oc, f"150 ft bonus: {reason}"


def _yard_min_for_street(params, street, segment_in_range):
    """Resolve the applicable minimum for a street frontage.

    Returns (min_ft, known_bool, reason). Unknown street or unknown
    segment (for segment-limited streets) yields known=False.
    """
    if not _known(street):
        return None, False, "fronting street is unknown"
    if street in params["min_5_streets"]:
        return 5, True, f"{street}: 5 ft minimum"
    if street in params["min_10_streets"]:
        return 10, True, f"{street}: 10 ft minimum"
    if street in params["min_10_streets_segment_limited"]:
        if not _known(segment_in_range):
            return None, False, f"{street}: 10 ft minimum applies only on the listed segment; segment unknown"
        if segment_in_range:
            return 10, True, f"{street} (listed segment): 10 ft minimum"
        return 0, True, f"{street} (outside listed segment): no minimum"
    return 0, True, f"{street}: no minimum"


def _check_one_yard(params, setback, street, segment_in_range, yard_name):
    if not _known(setback):
        return Outcome.UNKNOWN, f"{yard_name} setback value is unknown"
    if setback < 0:
        return Outcome.FAIL, f"{yard_name} setback {setback} ft is negative"
    if setback > params["max_ft"]:
        return Outcome.FAIL, f"{yard_name} setback {setback} ft exceeds maximum {params['max_ft']} ft"
    min_ft, known, why = _yard_min_for_street(params, street, segment_in_range)
    if not known:
        # A setback >= 10 satisfies every possible minimum in this rule.
        if setback >= 10:
            return Outcome.PASS, f"{yard_name} setback {setback} ft satisfies any applicable minimum ({why})"
        return Outcome.UNKNOWN, f"{yard_name} setback {setback} ft: {why}"
    if setback >= min_ft:
        return Outcome.PASS, f"{yard_name} setback {setback} ft satisfies minimum ({why})"
    return Outcome.FAIL, f"{yard_name} setback {setback} ft below minimum ({why})"


def mu11_street_setback(params, ctx):
    """MU-11-08: front/corner side setbacks, street-specific minima, 20 ft max."""
    for yard, s_key, st_key, seg_key in (
        ("front", "front_setback_ft", "front_street", "front_street_within_listed_segment"),
        ("corner side", "corner_side_setback_ft", "corner_street", "corner_street_within_listed_segment"),
    ):
        outcome, reason = _check_one_yard(
            params, ctx.get(s_key), ctx.get(st_key), ctx.get(seg_key), yard
        )
        if outcome != Outcome.PASS:
            return outcome, reason
    return Outcome.PASS, "front and corner side setbacks satisfy the street-specific minima and 20 ft maximum"


# Zone-code list attributes parallel to the legacy boolean abutment attributes.
# The mapping lives in code (not in verified_rules.json) because the store is
# human-verified and frozen: only the human re-verification pass may edit it.
_ABUTS_ZONES_ATTR = {
    "interior_abuts_listed_zone": "abuts_zones_side",
    "rear_abuts_listed_zone": "abuts_zones_rear",
}


def mu11_abutment_setback(params, ctx):
    """MU-11-09 / MU-11-10: abutment-triggered minima; yard selected via params.

    Abutment is resolved in this order:
      1. A zone-code list (abuts_zones_side / abuts_zones_rear) when present:
         the abutment minimum applies iff any listed zone appears. An empty
         list means the abutment survey is done and no listed zone abuts.
      2. The legacy boolean attribute (interior/rear_abuts_listed_zone).
      3. Neither present -> UNKNOWN. A malformed (non-list) zone list is also
         UNKNOWN: it is not evidence of compliance.
    """
    setback = ctx.get(params["setback_attr"])
    yard = params["yard_label"]
    if not _known(setback):
        return Outcome.UNKNOWN, f"{yard} setback value is unknown"
    if setback < 0:
        return Outcome.FAIL, f"{yard} setback {setback} ft is negative"
    if setback >= params["abut_min_ft"]:
        return Outcome.PASS, f"{yard} setback {setback} ft satisfies the abutment minimum in all cases"

    zones_attr = _ABUTS_ZONES_ATTR.get(params["abuts_attr"])
    listed = set(params.get("listed_zones", []))
    zones = ctx.get(zones_attr)

    if zones is None:
        # No zone list: fall back to the direct boolean; absent both -> UNKNOWN.
        abuts = ctx.get(params["abuts_attr"])
        if not _known(abuts):
            return Outcome.UNKNOWN, f"{yard} setback {setback} ft: abutment against a listed zone is unknown"
        if abuts:
            return Outcome.FAIL, f"{yard} setback {setback} ft below {params['abut_min_ft']} ft abutment minimum"
        return Outcome.PASS, f"{yard} setback {setback} ft: no abutment, no minimum applies"

    if not isinstance(zones, (list, tuple)):
        return Outcome.UNKNOWN, f"{yard}: {zones_attr} must be a list of zone codes; abutment cannot be determined"
    hits = sorted({z for z in zones if z in listed})
    if hits:
        return Outcome.FAIL, (
            f"{yard} setback {setback} ft below {params['abut_min_ft']} ft abutment minimum "
            f"(abuts listed zone(s): {', '.join(hits)})"
        )
    surveyed = ", ".join(zones) if zones else "no abutting zones recorded"
    return Outcome.PASS, f"{yard} setback {setback} ft: abuts {surveyed} — no listed zone, no minimum applies"


def min_yards_flat(params, ctx):
    """M-1-02: flat minimum yards — front 15 ft, corner side 15 ft, interior
    side none, rear none (21A.28.020.D, human-verified).

    Unlike the MU abutment rules, these minima are unconditional: no building
    form, listed-zone, or street scoping. A "none" minimum (0) means any
    non-negative setback passes that yard.
    """
    for yard, attr, min_key in (
        ("front", "front_setback_ft", "min_front_ft"),
        ("corner side", "corner_side_setback_ft", "min_corner_side_ft"),
        ("interior side", "interior_side_setback_ft", "min_interior_side_ft"),
        ("rear", "rear_setback_ft", "min_rear_ft"),
    ):
        setback = ctx.get(attr)
        minimum = params[min_key]
        if not _known(setback):
            return Outcome.UNKNOWN, f"{yard} setback value is unknown"
        if setback < 0:
            return Outcome.FAIL, f"{yard} setback {setback} ft is negative"
        if setback < minimum:
            return (
                Outcome.FAIL,
                f"{yard} setback {setback} ft below {minimum} ft minimum",
            )
    return (
        Outcome.PASS,
        "front, corner side, interior side, and rear setbacks satisfy the flat minima",
    )


def no_district_minimum(params, ctx):
    """Absence rules (MU-5-16, MU-6-16, MU-11-11): verified absence — no
    minimum lot area or width anywhere in Title 21A (2026 S-21) per the
    code-wide human-verified sweep; Title 20 (Subdivisions) defers lot
    dimensions to the Title 21A district, so it adds none either."""
    label = params.get("district_label", "the district")
    return Outcome.PASS, (
        f"no minimum lot area or width applies to {label} anywhere in Title 21A "
        "(2026 S-21) — code-wide human-verified sweep; Title 20 Sec. 20.26.090.C "
        "defers to the district, which states none"
    )


# ---------------------------------------------------------------------------
# Caddy extraction v2 overlay (rulegraph/caddy_params_v2.json) — MU numeric
# height/yard/setback params. Same three-valued contract: a form-scoped rule
# whose building form is unknown yields UNKNOWN; a fact the context does not
# supply yields UNKNOWN, never PASS. Building-form vocabulary (snake_case,
# e.g. "row_house") is defined by the overlay's applies_to_forms lists, which
# encode the stored quotes' applies_to scoping machine-readably.
# ---------------------------------------------------------------------------

def _mu_form_check(params, ctx):
    """Shared MU building-form scoping.

    Returns (form, None) when the rule applies to this scheme's form, else
    (None, (outcome, reason)): UNKNOWN when the form is unknown, PASS with an
    explicit not-applicable reason when the form is known but out of scope.
    """
    form = ctx.get("building_form")
    if not _known(form):
        return None, (Outcome.UNKNOWN, "building form is unknown")
    applies = params.get("applies_to_forms")
    if applies and form not in applies:
        return None, (
            Outcome.PASS,
            f"rule applies to {applies}; building form is {form!r}",
        )
    return form, None


def mu_max_height(params, ctx):
    """MU height maxima (MU-5-01/05/10, MU-6-01/05/10, MU-11-01).

    Form-scoped single maximum. MU-11-06's tiered 125/150 ft bonus keeps its
    own mu11_max_height evaluator (already wired in the canonical store).
    """
    _form, short = _mu_form_check(params, ctx)
    if short:
        return short
    h = ctx.get("height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, "building height is unknown"
    if h > params["max_ft"]:
        return Outcome.FAIL, f"height {h} ft exceeds maximum {params['max_ft']} ft"
    return Outcome.PASS, f"height {h} ft within maximum {params['max_ft']} ft"


def mu_yard_range(params, ctx):
    """MU front/corner-side yard range (MU-5-06/11, MU-6-06/11).

    Flat min+max; the -11 rules additionally require a residential ground
    floor (required_ground_floor_use param). Ground-floor occupancy is read
    from the context's ground_floor_use attribute — never classified from
    use names by the engine.
    """
    _form, short = _mu_form_check(params, ctx)
    if short:
        return short
    req_use = params.get("required_ground_floor_use")
    if req_use:
        use = ctx.get("ground_floor_use")
        if not _known(use):
            return Outcome.UNKNOWN, "ground-floor occupancy is unknown"
        if use != req_use:
            return Outcome.PASS, (
                f"rule applies to {req_use} ground floor; ground floor is {use!r}"
            )
    for yard, attr in (("front", "front_setback_ft"),
                       ("corner side", "corner_side_setback_ft")):
        setback = ctx.get(attr)
        if not _known(setback):
            return Outcome.UNKNOWN, f"{yard} setback value is unknown"
        if setback < 0:
            return Outcome.FAIL, f"{yard} setback {setback} ft is negative"
        if setback < params["min_ft"]:
            return Outcome.FAIL, (
                f"{yard} setback {setback} ft below minimum {params['min_ft']} ft"
            )
        if setback > params["max_ft"]:
            return Outcome.FAIL, (
                f"{yard} setback {setback} ft exceeds maximum {params['max_ft']} ft"
            )
    return Outcome.PASS, (
        f"front and corner side setbacks within "
        f"{params['min_ft']}-{params['max_ft']} ft range"
    )


def _mu_abutment_applies(yp, ctx):
    """Resolve whether an abutment-triggered minimum applies.

    Returns (applies: bool | None, reason); None means the abutment facts are
    unknown. Resolution order mirrors mu11_abutment_setback: zone-code list
    first, legacy boolean second, UNKNOWN when neither is present.
    """
    zones_attr = _ABUTS_ZONES_ATTR.get(yp["abuts_attr"])
    listed = set(yp.get("listed_zones", []))
    zones = ctx.get(zones_attr) if zones_attr else None
    if zones is None:
        abuts = ctx.get(yp["abuts_attr"])
        if not _known(abuts):
            return None, "abutment against a listed zone is unknown"
        return bool(abuts), ("abutment confirmed" if abuts else "no abutment")
    if not isinstance(zones, (list, tuple)):
        return None, f"{zones_attr} must be a list of zone codes"
    hits = sorted({z for z in zones if z in listed})
    if hits:
        return True, f"abuts listed zone(s): {', '.join(hits)}"
    return False, "no listed zone abuts"


def mu_yard_min_abutment(params, ctx):
    """MU yard minima, some with abutment-triggered higher minima.

    Each entry in params["yards"] carries yard_label, setback_attr,
    base_min_ft, and optionally abut_min_ft + abuts_attr + listed_zones.
    A setback below the base minimum FAILs even when the abutment facts are
    unknown — the base minimum is unconditional.
    """
    _form, short = _mu_form_check(params, ctx)
    if short:
        return short
    for yp in params["yards"]:
        label = yp["yard_label"]
        setback = ctx.get(yp["setback_attr"])
        if not _known(setback):
            return Outcome.UNKNOWN, f"{label} setback value is unknown"
        if setback < 0:
            return Outcome.FAIL, f"{label} setback {setback} ft is negative"
        abut_min = yp.get("abut_min_ft")
        if abut_min is None:
            if setback < yp["base_min_ft"]:
                return Outcome.FAIL, (
                    f"{label} setback {setback} ft below minimum "
                    f"{yp['base_min_ft']} ft"
                )
            continue
        if setback >= abut_min:
            continue  # satisfies the minimum in every abutment case
        applies, why = _mu_abutment_applies(yp, ctx)
        if applies is None:
            if setback < yp["base_min_ft"]:
                return Outcome.FAIL, (
                    f"{label} setback {setback} ft below base minimum "
                    f"{yp['base_min_ft']} ft ({why})"
                )
            return Outcome.UNKNOWN, f"{label} setback {setback} ft: {why}"
        min_ft = abut_min if applies else yp["base_min_ft"]
        if setback < min_ft:
            return Outcome.FAIL, (
                f"{label} setback {setback} ft below minimum {min_ft} ft ({why})"
            )
    return Outcome.PASS, "yard setbacks satisfy the applicable minima"


def _mu_street_min(params, street, segment_in_range):
    """Resolve the street-specific minimum for mu_street_yard.

    Returns (min_ft, known, reason). Unlisted streets take the base minimum;
    segment-limited streets need the segment fact.
    """
    if not _known(street):
        return None, False, "fronting street is unknown"
    if street in params["min_10_streets"]:
        return 10, True, f"{street}: 10 ft minimum"
    if street in params["min_10_streets_segment_limited"]:
        if not _known(segment_in_range):
            return None, False, (
                f"{street}: 10 ft minimum applies only on the listed segment; "
                "segment unknown"
            )
        if segment_in_range:
            return 10, True, f"{street} (listed segment): 10 ft minimum"
        base = params["base_min_ft"]
        return base, True, f"{street} (outside listed segment): base minimum {base} ft"
    base = params["base_min_ft"]
    return base, True, f"{street}: base minimum {base} ft"


def mu_street_yard(params, ctx):
    """MU-11-02: street-specific front/corner-side minima over a base minimum,
    plus a flat maximum."""
    _form, short = _mu_form_check(params, ctx)
    if short:
        return short
    for yard, s_key, st_key, seg_key in (
        ("front", "front_setback_ft", "front_street",
         "front_street_within_listed_segment"),
        ("corner side", "corner_side_setback_ft", "corner_street",
         "corner_street_within_listed_segment"),
    ):
        setback = ctx.get(s_key)
        if not _known(setback):
            return Outcome.UNKNOWN, f"{yard} setback value is unknown"
        if setback < 0:
            return Outcome.FAIL, f"{yard} setback {setback} ft is negative"
        if setback > params["max_ft"]:
            return Outcome.FAIL, (
                f"{yard} setback {setback} ft exceeds maximum {params['max_ft']} ft"
            )
        min_ft, known, why = _mu_street_min(params, ctx.get(st_key), ctx.get(seg_key))
        if not known:
            # 10 ft satisfies every minimum in this rule (base 5, listed 10).
            if setback >= 10:
                continue
            return Outcome.UNKNOWN, f"{yard} setback {setback} ft: {why}"
        if setback < min_ft:
            return Outcome.FAIL, f"{yard} setback {setback} ft below minimum ({why})"
    return Outcome.PASS, (
        "front and corner side setbacks satisfy the street-specific minima "
        "and maximum"
    )


def mu_street_yard_minmax(params, ctx):
    """MU-5-12 / MU-6-12: non-residential ground floor with street-specific
    minima AND maxima (North Temple / 400 South differ from other streets)."""
    _form, short = _mu_form_check(params, ctx)
    if short:
        return short
    req_use = params.get("required_ground_floor_use", "non-residential")
    use = ctx.get("ground_floor_use")
    if not _known(use):
        return Outcome.UNKNOWN, "ground-floor occupancy is unknown"
    if use != req_use:
        return Outcome.PASS, (
            f"rule applies to {req_use} ground floor; ground floor is {use!r}"
        )
    for yard, s_key, st_key in (
        ("front", "front_setback_ft", "front_street"),
        ("corner side", "corner_side_setback_ft", "corner_street"),
    ):
        setback = ctx.get(s_key)
        if not _known(setback):
            return Outcome.UNKNOWN, f"{yard} setback value is unknown"
        if setback < 0:
            return Outcome.FAIL, f"{yard} setback {setback} ft is negative"
        street = ctx.get(st_key)
        if not _known(street):
            return Outcome.UNKNOWN, (
                f"{yard} setback {setback} ft: fronting street is unknown"
            )
        min_ft = params["street_min_ft"].get(street, params["default_min_ft"])
        max_ft = params["street_max_ft"].get(street, params["default_max_ft"])
        if setback < min_ft:
            return Outcome.FAIL, (
                f"{yard} setback {setback} ft below {min_ft} ft minimum on {street}"
            )
        if setback > max_ft:
            return Outcome.FAIL, (
                f"{yard} setback {setback} ft exceeds {max_ft} ft maximum on {street}"
            )
    return Outcome.PASS, (
        "front and corner side setbacks satisfy the street-specific minima "
        "and maxima"
    )


def mu_building_form_separation(params, ctx):
    """MU-5-15 / MU-6-15: 6 ft separation when multiple building forms share a
    lot. The pipeline carries no form-to-form separation distances, so a
    multi-form lot honestly yields UNKNOWN naming the missing site-plan fact.
    """
    forms = ctx.get("building_forms")
    if not _known(forms):
        return Outcome.UNKNOWN, "building forms on the lot are unknown"
    if len(forms) < 2:
        return Outcome.PASS, (
            "single building form on the lot; separation rule not triggered"
        )
    return Outcome.UNKNOWN, (
        "multiple building forms present but form-to-form separation distances "
        "are not in the pipeline context (site plan / building footprints)"
    )


EVALUATORS = {
    "pl_landscape_buffer": pl_landscape_buffer,
    "mu11_uses_per_story": mu11_uses_per_story,
    "mu11_max_height": mu11_max_height,
    "mu11_additional_height": mu11_additional_height,
    "mu11_street_setback": mu11_street_setback,
    "mu11_abutment_setback": mu11_abutment_setback,
    "min_yards_flat": min_yards_flat,
    "no_district_minimum": no_district_minimum,
    "mu_max_height": mu_max_height,
    "mu_yard_range": mu_yard_range,
    "mu_yard_min_abutment": mu_yard_min_abutment,
    "mu_street_yard": mu_street_yard,
    "mu_street_yard_minmax": mu_street_yard_minmax,
    "mu_building_form_separation": mu_building_form_separation,
}


def _scheme_lots(ctx):
    """Per-scheme lot facts [{area_sqft, frontage_ft}] or (None, reason)."""
    lots = ctx.get("scheme_lots")
    if lots is None:
        return None, "per-lot areas/widths are unknown"
    if not isinstance(lots, (list, tuple)) or not lots:
        return None, "per-lot areas/widths are unknown"
    return lots, ""


def min_lot_area_width(params, ctx):
    """M-1-01: minimum lot area 10,000 sqft and width 80 ft, every lot.

    The quote's existing-lot clause (legal conforming if existing as of
    1995-04-12) is honored: a below-minimum lot whose existing status is
    unknown yields UNKNOWN, never FAIL — the exception could apply.
    """
    lots, why = _scheme_lots(ctx)
    if lots is None:
        return Outcome.UNKNOWN, why
    min_area, min_width = params["min_area_sqft"], params["min_width_ft"]
    for i, lot in enumerate(lots):
        area, width = lot.get("area_sqft"), lot.get("frontage_ft")
        label = lot.get("lot_id", f"lot {i}")
        if not _known(area) or not _known(width):
            return Outcome.UNKNOWN, f"{label}: area or width is unknown"
        if area < min_area or width < min_width:
            return Outcome.UNKNOWN, (
                f"{label}: {area} sqft / {width} ft below "
                f"{min_area} sqft / {min_width} ft minimum, but existing-lot "
                f"status (conforming if existing as of "
                f"{params['existing_conforming_date']}) is unknown"
            )
    return Outcome.PASS, (
        f"all {len(lots)} lots satisfy {min_area} sqft / {min_width} ft minima"
    )


def _abuts_districts(ctx, districts):
    """True/False/None: does any side/rear abut one of the listed districts?"""
    hits, unknown = False, False
    for attr in ("abuts_zones_side", "abuts_zones_rear"):
        zones = ctx.get(attr)
        if zones is None:
            unknown = True
            continue
        if not isinstance(zones, (list, tuple)):
            unknown = True
            continue
        if any(z in districts for z in zones):
            hits = True
    if hits:
        return True
    if unknown:
        return None
    return False


def m1_abutment_setback(params, ctx):
    """M-1-03: +1 ft setback per ft of height above 30 ft when abutting
    AG-2/AG-5, measured beyond the 21A.48.080 landscape buffer.

    The buffer's numeric depth is a recorded extraction gap: with height
    above 30 ft and abutment confirmed, the required total cannot be
    computed -> UNKNOWN. Height at/below 30 ft needs no additional setback
    regardless of abutment -> PASS.
    """
    districts = params["trigger_districts"]
    threshold, rate = params["height_threshold_ft"], params["rate_ft_per_ft"]
    h = ctx.get("height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, "building height is unknown"
    if h <= threshold:
        return Outcome.PASS, (
            f"height {h} ft at/below the {threshold} ft threshold: no "
            "additional setback required"
        )
    abuts = _abuts_districts(ctx, districts)
    if abuts is False:
        return Outcome.PASS, (
            f"height {h} ft above {threshold} ft but the lot abuts no "
            f"{'/'.join(districts)} district: rule not triggered"
        )
    if abuts is None:
        return Outcome.UNKNOWN, (
            f"height {h} ft above {threshold} ft but abutment against "
            f"{'/'.join(districts)} is unknown"
        )
    return Outcome.UNKNOWN, (
        f"height {h} ft above {threshold} ft abutting "
        f"{'/'.join(districts)}: required additional setback "
        f"{(h - threshold) * rate:.1f} ft beyond the landscape buffer, but "
        "the 21A.48.080 buffer depth is a recorded gap — required total "
        "cannot be computed"
    )


def m1_max_height(params, ctx):
    """M-1-04: 65 ft base maximum; emission-free distillation columns
    necessary for manufacture processing up to the most restrictive
    FAA-imposed minimal approach surface elevation, or 120 ft max,
    whichever is less."""
    h = ctx.get("height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, "building height is unknown"
    base, col_max = params["base_max_ft"], params["distillation_column_max_ft"]
    if h <= base:
        return Outcome.PASS, f"height {h} ft within {base} ft base maximum"
    if h > col_max:
        return Outcome.FAIL, (
            f"height {h} ft exceeds the {col_max} ft absolute maximum for "
            "distillation-column exceptions"
        )
    is_col = ctx.get("is_distillation_column_structure")
    if not _known(is_col):
        return Outcome.UNKNOWN, (
            f"height {h} ft exceeds {base} ft base maximum; whether the "
            "structure is an emission-free distillation column necessary "
            "for manufacture processing is unknown"
        )
    if not is_col:
        return Outcome.FAIL, (
            f"height {h} ft exceeds {base} ft base maximum and the structure "
            "is not a qualifying distillation column"
        )
    faa = ctx.get("faa_max_elevation_ft")
    if not _known(faa):
        return Outcome.UNKNOWN, (
            f"qualifying distillation column at {h} ft: the most restrictive "
            "FAA-imposed minimal approach surface elevation is unknown"
        )
    limit = min(col_max, faa)
    if h <= limit:
        return Outcome.PASS, (
            f"qualifying distillation column at {h} ft within "
            f"{limit} ft (FAA/120 ft limit)"
        )
    return Outcome.FAIL, (
        f"qualifying distillation column at {h} ft exceeds {limit} ft "
        "(FAA/120 ft limit)"
    )


def m1_height_exception_zone(params, ctx):
    """M-1-05: west of SLC International Airport and north of I-80,
    buildings may exceed 65 ft subject to Ch. 21A.59 design review;
    never above 85 ft."""
    h = ctx.get("height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, "building height is unknown"
    base, exc_max = params["base_max_ft"], params["exception_max_ft"]
    if h <= base:
        return Outcome.PASS, (
            f"height {h} ft within {base} ft base maximum; the "
            "airport/I-80 exception is not needed"
        )
    if h > exc_max:
        return Outcome.FAIL, (
            f"height {h} ft exceeds the {exc_max} ft absolute maximum of the "
            "airport/I-80 exception zone"
        )
    in_zone = ctx.get("in_m1_height_exception_zone")
    if not _known(in_zone):
        return Outcome.UNKNOWN, (
            f"height {h} ft exceeds {base} ft: whether the parcel is west of "
            "the airport and north of I-80 is unknown"
        )
    if not in_zone:
        return Outcome.FAIL, (
            f"height {h} ft exceeds {base} ft base maximum and the parcel is "
            "not in the airport/I-80 exception zone"
        )
    dr = ctx.get("design_review_completed")
    if not _known(dr):
        return Outcome.UNKNOWN, (
            f"height {h} ft in the exception zone: Ch. 21A.59 design-review "
            "status is unknown"
        )
    if dr:
        return Outcome.PASS, (
            f"height {h} ft within {exc_max} ft; parcel in exception zone "
            "with design review completed"
        )
    return Outcome.FAIL, (
        f"height {h} ft in the exception zone without Ch. 21A.59 design review"
    )


def _lot_acres(lot):
    area = lot.get("area_sqft")
    if not _known(area):
        return None
    return area / 43560.0


def os_max_height_tiered(params, ctx):
    """OS-02: height caps tiered by lot size — 35 ft on lots <= 4 acres;
    35-45 ft on lots > 4 acres where permitted; 45-60 ft via design review.
    Yard inflation over the tier thresholds is enforced jointly by OS-04;
    this evaluator covers the height caps. SLC Public Utilities critical
    infrastructure is exempt."""
    lots, why = _scheme_lots(ctx)
    if lots is None:
        return Outcome.UNKNOWN, why
    h = ctx.get("height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, "building height is unknown"
    if ctx.get("is_slc_public_utilities_structure") is True:
        return Outcome.PASS, (
            "SLC Public Utilities critical infrastructure: exempt from "
            "district height restrictions"
        )
    tier_acres = params["tier_acres"]
    worst = None
    for i, lot in enumerate(lots):
        acres = _lot_acres(lot)
        label = lot.get("lot_id", f"lot {i}")
        if acres is None:
            return Outcome.UNKNOWN, f"{label}: lot area is unknown"
        tier = "le4ac" if acres <= tier_acres else "gt4ac"
        cap = params["max_le4ac_ft"] if tier == "le4ac" else params["max_gt4ac_ft"]
        if h <= cap:
            continue
        if tier == "gt4ac":
            dr = ctx.get("design_review_completed")
            if h <= params["max_design_review_ft"] and dr is True:
                continue
            if h <= params["max_design_review_ft"] and not _known(dr):
                worst = (Outcome.UNKNOWN, (
                    f"{label}: {acres:.2f} ac, height {h} ft above {cap} ft: "
                    "design-review status unknown (45-60 ft needs it)"
                ))
                continue
        worst = (Outcome.FAIL, (
            f"{label}: {acres:.2f} ac, height {h} ft exceeds "
            f"{cap} ft tier maximum"
        ))
    if worst is not None:
        return worst
    return Outcome.PASS, (
        f"height {h} ft within the tiered maxima on all {len(lots)} lots"
    )


def os_rec_equipment_height(params, ctx):
    """OS-03: recreation equipment (not buildings) up to 80 ft where needed
    for the equipment/use to operate safely."""
    has = ctx.get("has_recreation_equipment")
    if not _known(has):
        return Outcome.UNKNOWN, (
            "whether recreation equipment is proposed is unknown"
        )
    if not has:
        return Outcome.PASS, "no recreation equipment proposed: rule not triggered"
    h = ctx.get("recreation_equipment_height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, "recreation equipment height is unknown"
    if h <= params["max_ft"]:
        return Outcome.PASS, (
            f"recreation equipment {h} ft within {params['max_ft']} ft maximum"
        )
    return Outcome.FAIL, (
        f"recreation equipment {h} ft exceeds {params['max_ft']} ft maximum"
    )


def os_min_yards_tiered(params, ctx):
    """OS-04: yard minima tiered by lot size (10 ft front/corner always;
    10 ft interior/rear on <= 4 ac lots, 15 ft on > 4 ac lots), with the
    OS-02 yard inflation applied jointly: each required yard grows 1 ft per
    ft of height over the tier threshold (20 ft <= 4 ac, 35 ft > 4 ac)."""
    lots, why = _scheme_lots(ctx)
    if lots is None:
        return Outcome.UNKNOWN, why
    h = ctx.get("height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, (
            "building height is unknown: the OS-02 yard inflation cannot be computed"
        )
    setbacks = {}
    for yard, attr in (("front", "front_setback_ft"),
                       ("corner side", "corner_side_setback_ft"),
                       ("interior side", "interior_side_setback_ft"),
                       ("rear", "rear_setback_ft")):
        setbacks[yard] = ctx.get(attr)
        if not _known(setbacks[yard]):
            return Outcome.UNKNOWN, f"{yard} setback value is unknown"
    infl = params["yard_inflation_from_os02"]
    required = {}
    for i, lot in enumerate(lots):
        acres = _lot_acres(lot)
        label = lot.get("lot_id", f"lot {i}")
        if acres is None:
            return Outcome.UNKNOWN, f"{label}: lot area is unknown"
        tier = "le4ac" if acres <= params["tier_acres"] else "gt4ac"
        t = infl[tier]
        bump = max(0.0, (h - t["threshold_ft"]) * t["rate_ft_per_ft"])
        if tier == "le4ac":
            req = {"front": params["front_ft"], "corner side": params["corner_side_ft"],
                   "interior side": params["interior_side_le4ac_ft"],
                   "rear": params["rear_le4ac_ft"]}
        else:
            req = {"front": params["front_ft"], "corner side": params["corner_side_ft"],
                   "interior side": params["interior_side_gt4ac_ft"],
                   "rear": params["rear_gt4ac_ft"]}
        for yard, base in req.items():
            need = base + bump
            if setbacks[yard] < need:
                return Outcome.FAIL, (
                    f"{label} ({acres:.2f} ac): {yard} setback "
                    f"{setbacks[yard]} ft below required {need:.1f} ft "
                    f"(base {base} ft + {bump:.1f} ft OS-02 inflation)"
                )
            required[yard] = max(required.get(yard, 0), need)
    detail = ", ".join(f"{y} {required[y]:.1f} ft" for y in
                       ("front", "corner side", "interior side", "rear"))
    return Outcome.PASS, (
        f"all yards satisfy the tiered minima with OS-02 inflation: {detail}"
    )


def pl_min_lot_area_width(params, ctx):
    """PL-01: public schools 5 ac / 150 ft; other permitted uses
    20,000 sqft / 75 ft. The row is selected by the proposed use —
    unknown use yields UNKNOWN, never the more permissive row."""
    is_school = ctx.get("proposed_use_is_public_school")
    if not _known(is_school):
        return Outcome.UNKNOWN, (
            "proposed use is unknown: cannot select the public-school vs "
            "other-uses row"
        )
    row = params["public_school"] if is_school else params["other_uses"]
    if is_school:
        min_area_sqft = row["min_area_acres"] * 43560
        row_label = (f"public school: {row['min_area_acres']} ac / "
                     f"{row['min_width_ft']} ft")
    else:
        min_area_sqft = row["min_area_sqft"]
        row_label = (f"other permitted uses: {row['min_area_sqft']} sqft / "
                     f"{row['min_width_ft']} ft")
    lots, why = _scheme_lots(ctx)
    if lots is None:
        return Outcome.UNKNOWN, why
    for i, lot in enumerate(lots):
        area, width = lot.get("area_sqft"), lot.get("frontage_ft")
        label = lot.get("lot_id", f"lot {i}")
        if not _known(area) or not _known(width):
            return Outcome.UNKNOWN, f"{label}: area or width is unknown"
        if area < min_area_sqft or width < row["min_width_ft"]:
            return Outcome.FAIL, (
                f"{label}: {area} sqft / {width} ft below {row_label}"
            )
    return Outcome.PASS, f"all {len(lots)} lots satisfy {row_label}"


def pl_max_height(params, ctx):
    """PL-02: civic-listed uses 75 ft (abutting-greater-height exception is
    a recorded gap — its numeric value is not in the quote, so a civic
    building above 75 ft with unknown abutment yields UNKNOWN); K-12
    public schools 125 ft; other uses 35 ft."""
    h = ctx.get("height_ft")
    if not _known(h):
        return Outcome.UNKNOWN, "building height is unknown"
    if h <= params["other_uses_max_ft"]:
        return Outcome.PASS, (
            f"height {h} ft within {params['other_uses_max_ft']} ft: "
            "satisfies every PL-02 row"
        )
    is_school = ctx.get("proposed_use_is_public_school")
    civic = ctx.get("proposed_use_pl_civic_listed")
    if is_school is True:
        cap, row = params["k12_public_max_ft"], "K-12 public school"
    elif civic is True:
        cap, row = params["civic_listed_max_ft"], "civic-listed use"
    elif is_school is False and civic is False:
        cap, row = params["other_uses_max_ft"], "other use"
    else:
        return Outcome.UNKNOWN, (
            f"height {h} ft above {params['other_uses_max_ft']} ft: the "
            "proposed-use row cannot be selected"
        )
    if h <= cap:
        return Outcome.PASS, f"height {h} ft within {cap} ft ({row})"
    if row == "civic-listed use":
        return Outcome.UNKNOWN, (
            f"height {h} ft above {cap} ft ({row}): the abutting "
            "greater-height exception could apply but its numeric value is "
            "a recorded gap"
        )
    return Outcome.FAIL, f"height {h} ft exceeds {cap} ft ({row})"


def _pl_zone_class(params, zone):
    """Classify an abutting zone for PL-03's residential/manufacturing vs
    other branch. Returns 'res_mfg', 'other', or None (unmapped -> UNKNOWN).
    The 'M-' hyphen keeps MU-* out of manufacturing; 'other' requires an
    explicit known-district listing, never a guess."""
    for prefix in params["residential_zone_prefixes"]:
        if zone.startswith(prefix):
            return "res_mfg"
    for prefix in params["manufacturing_zone_prefixes"]:
        if zone.startswith(prefix):
            return "res_mfg"
    if zone in params.get("other_districts", []):
        return "other"
    return None


def pl_min_yards(params, ctx):
    """PL-03: K-12 public schools — 30 ft front/corner; interior/rear
    50 ft next to residential/manufacturing districts, 30 ft otherwise.
    Other uses — 30/30/20/30. Unknown use, unknown setbacks, or an
    unmapped abutting zone code all yield UNKNOWN."""
    is_school = ctx.get("proposed_use_is_public_school")
    if not _known(is_school):
        return Outcome.UNKNOWN, (
            "proposed use is unknown: cannot select the K-12 vs other-uses row"
        )
    setbacks = {}
    for yard, attr in (("front", "front_setback_ft"),
                       ("corner side", "corner_side_setback_ft"),
                       ("interior side", "interior_side_setback_ft"),
                       ("rear", "rear_setback_ft")):
        setbacks[yard] = ctx.get(attr)
        if not _known(setbacks[yard]):
            return Outcome.UNKNOWN, f"{yard} setback value is unknown"
    if is_school:
        row = params["k12_public"]
        classes = {}
        for yard, attr in (("interior side", "abuts_zones_side"),
                           ("rear", "abuts_zones_rear")):
            zones = ctx.get(attr)
            if zones is None or not isinstance(zones, (list, tuple)):
                return Outcome.UNKNOWN, (
                    f"{yard} abutting-zone survey is unknown: cannot select "
                    "the residential/manufacturing vs other row"
                )
            mapped = [_pl_zone_class(params, z) for z in zones]
            if any(m is None for m in mapped):
                bad = sorted({z for z, m in zip(zones, mapped) if m is None})
                return Outcome.UNKNOWN, (
                    f"{yard} abuts unmapped zone code(s) "
                    f"{', '.join(bad)}: residential/manufacturing vs other "
                    "cannot be determined"
                )
            classes[yard] = ("res_mfg" if "res_mfg" in mapped else "other")
        req = {
            "front": row["front_ft"],
            "corner side": row["corner_side_ft"],
            "interior side": row["interior_side_res_mfg_ft"]
            if classes["interior side"] == "res_mfg"
            else row["interior_side_other_ft"],
            "rear": row["rear_res_mfg_ft"]
            if classes["rear"] == "res_mfg" else row["rear_other_ft"],
        }
        row_label = "K-12 public school"
    else:
        row = params["other_uses"]
        req = {"front": row["front_ft"], "corner side": row["corner_side_ft"],
               "interior side": row["interior_side_ft"], "rear": row["rear_ft"]}
        row_label = "other uses"
    for yard, need in req.items():
        if setbacks[yard] < need:
            return Outcome.FAIL, (
                f"{yard} setback {setbacks[yard]} ft below {need} ft "
                f"({row_label})"
            )
    return Outcome.PASS, (
        f"all yards satisfy the PL-03 minima ({row_label})"
    )


# Caddy extraction v1 overlay (rulegraph/caddy_params_v1.json). Params are
# machine-extracted from Rohan-verified quotes; every evaluator above is
# three-valued and honest: a missing fact yields UNKNOWN, never PASS.
# Registered here (after the defs) so the module-level EVALUATORS dict
# above never references names before they are defined.
EVALUATORS.update({
    "min_lot_area_width": min_lot_area_width,
    "m1_abutment_setback": m1_abutment_setback,
    "m1_max_height": m1_max_height,
    "m1_height_exception_zone": m1_height_exception_zone,
    "os_max_height_tiered": os_max_height_tiered,
    "os_rec_equipment_height": os_rec_equipment_height,
    "os_min_yards_tiered": os_min_yards_tiered,
    "pl_min_lot_area_width": pl_min_lot_area_width,
    "pl_max_height": pl_max_height,
    "pl_min_yards": pl_min_yards,
})
