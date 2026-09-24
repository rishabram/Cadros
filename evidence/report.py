"""NERON per-parcel evidence report generator (canonical store edition).

Reads a pipeline outputs/report.json plus the RuleGraph verified rule store and
writes a human-readable markdown evidence report.

INVARIANTS (hard):
  - This module DESCRIBES human_verification records copied verbatim from the
    store. It never creates, edits, or implies a human verdict.
  - Missing info is never hidden and never defaults to compliance: UNKNOWN
    verdicts and unknown context attributes are surfaced prominently.
  - Verdict vocabulary is the canonical five-term set:
    PASS / CONDITIONAL_PASS / FAIL / UNKNOWN / MANUAL_REVIEW.
  - This module never touches rulegraph/engine.py or any baseline artifacts.
  - Output is deterministic: no wall-clock timestamps; the provenance footer
    carries content fingerprints instead, so regenerating from the same
    inputs yields byte-identical markdown.

Report shapes handled:
  - scheme parcels (status "ok", schemes present): full report.
  - no-scheme parcels (status "no_schemes_generated"): the
    scheme_generation diagnostics are named explicitly — never omitted.
  - error parcels: an explicit error report; never silently skipped.

Usage:
    venv/bin/python -m evidence.report REPORT_JSON \\
        --store rulegraph/verified_rules.json --out report.md
"""

import argparse
import json
import sys
from typing import Dict, List, Optional

MACHINE_DRAFT_LABEL = "machine-draft — not human-verified output"

UNKNOWN_MARKER = "⚠ UNKNOWN"

# Canonical five-term verdict vocabulary, most-severe-first for display.
VERDICTS = ("UNKNOWN", "FAIL", "MANUAL_REVIEW", "CONDITIONAL_PASS", "PASS")


def _money(v):
    if v is None:
        return "n/a"
    return "${:,.0f}".format(v)


def _pct(v):
    if v is None:
        return "n/a"
    return "{:.1%}".format(v)


def _is_placeholder(source_text):
    """Label an assumption source as placeholder vs sourced, based on its text.

    This only echoes the report's own source labels; it invents nothing.
    """
    if not source_text:
        return "unknown source"
    low = source_text.lower()
    if "placeholder" in low or "synthetic" in low:
        return "PLACEHOLDER (not sourced from real data)"
    return "sourced / stated"


def _key_rules(store):
    rules = store.get("rules", {})
    if isinstance(rules, dict):
        return rules
    return {r["rule_id"]: r for r in rules}


def store_fingerprint(store):
    """Recompute the engine's store fingerprint: canonical_hash({"rules": ...}).

    Matches RuleGraph.__init__ in rulegraph/engine.py. The report prints the
    recomputed value AND the fingerprint recorded in report.json; a mismatch
    is surfaced loudly, never silently.
    """
    from rulegraph.fingerprint import canonical_hash

    return canonical_hash({"rules": store["rules"]})


def report_fingerprint(report):
    """Deterministic content fingerprint of the source report.json.

    Replaces wall-clock generation timestamps: the provenance footer carries
    this value, so a report is traceable to its exact inputs without breaking
    byte-determinism.
    """
    from rulegraph.fingerprint import canonical_hash

    return canonical_hash({"report": report})


def _section_header(num, title):
    return "## {}. {}\n\n".format(num, title)


def _num(v):
    """Exact numeric formatting: never rounds beyond the source value."""
    if v is None:
        return "n/a"
    if isinstance(v, float) and v.is_integer():
        return "{:,.0f}".format(v)
    if isinstance(v, float):
        return "{:,.1f}".format(v)
    return "{:,}".format(v)


def _top_scheme(report):
    schemes = {s["scheme_id"]: s for s in report.get("schemes", [])}
    ranked = report.get("ranked_order", []) or []
    if not ranked:
        return None, schemes
    return schemes.get(ranked[0]), schemes


def _rule_districts(evidence):
    """District scope of a store record (handles the MU-OPENSPACE-01 list)."""
    if not evidence:
        return []
    ds = evidence.get("districts")
    if ds:
        return list(ds)
    d = evidence.get("district")
    return [d] if d else []


def _banner(parcel_id):
    return (
        "# Evidence report — parcel `{}`\n\n> **{}**\n\n"
        "This report describes what the pipeline, the RuleGraph, and the "
        "use-allowance engine computed, quoting the verified rule store and "
        "use-table packs verbatim. It introduces no new verdicts, grants no "
        "human verification, and never treats an UNKNOWN as a pass.\n"
        .format(parcel_id, MACHINE_DRAFT_LABEL)
    )


def _provisional_banner(report):
    z = report.get("zoning", {}) or {}
    src = z.get("source", "") or ""
    if "PROVISIONAL" in src.upper():
        return (
            "> **PROVISIONAL inputs:** the zoning dimensional minimums used "
            "for this screening are provisional except where a rule is "
            "human-verified (see Section 3). District assignment comes from "
            "the real parcel/zoning spatial join.\n\n"
        )
    return ""


def _section_0(report):
    """Plain-English summary, machine-generated from report.json only.

    Every figure below is copied from the pipeline output; this section adds
    no verdicts, no recommendations, and no new facts.
    """
    lines = [_section_header(0, "What this means (plain-English summary)")]
    lines.append(
        "> **Machine-generated from the numbers in this report — not a "
        "recommendation, not human-verified.** Anything the pipeline could "
        "not determine is listed in Section 5; nothing there is treated as "
        "a pass.\n"
    )
    z = report.get("zoning", {}) or {}
    district = z.get("district", "not specified")
    pid = report.get("parcel_id", "n/a")
    acres = report.get("parcel_area_acres", 0) or 0
    schemes = report.get("schemes", []) or []
    ranked = report.get("ranked_order", []) or []
    top, smap = _top_scheme(report)
    clean = sum(1 for s in schemes if s.get("clean") is True)
    flagged = sum(1 for s in schemes if s.get("clean") is False)
    rg = report.get("rulegraph") or {}
    verdicts = rg.get("scheme_verdicts") or {}
    gaps = rg.get("gaps") or []
    ua = report.get("use_allowance") or {}
    ua_verdicts = ua.get("scheme_verdicts") or {}

    lines.append(
        "- This parcel (`{}`) covers **{:.2f} acres** in the **{}** district. "
        "Zoning district assignment comes from the real parcel/zoning spatial "
        "join; dimensional minimums used for screening are **PROVISIONAL** "
        "unless the rule is human-verified (see Section 3).".format(pid, acres, district)
    )
    if top is not None:
        pf = top.get("proforma", {}) or {}
        road = pf.get("road_length_ft", top.get("road_ft"))
        lines.append(
            "- The pipeline drew **{} subdivision scheme(s)** ({} geometry-clean, "
            "{} flagged). The top-ranked scheme, `{}`, lays out **{} lots** with "
            "{} ft of new road and projects **{} profit** at **{} margin**."
            .format(len(ranked), clean, flagged, top.get("scheme_id", "?"),
                    pf.get("lot_count", top.get("lots", "n/a")),
                    _num(road) if road else "n/a", _money(pf.get("profit")), _pct(pf.get("margin")))
        )
    else:
        lines.append("- The pipeline produced no ranked schemes for this parcel.")

    # RuleGraph honesty: count applicable rules on the top scheme so a vacuous
    # PASS (no in-district rules in the store) cannot read as compliance.
    counts = " / ".join(
        "**{}** {}".format(verdicts.get(v, 0), v) for v in VERDICTS
    )
    lines.append(
        "- RuleGraph check (scheme verdicts): {} — across the {} rule(s) in "
        "the verified store.".format(counts, rg.get("rules_evaluated", "?"))
    )
    applicable = []
    if top is not None:
        applicable = [r for r in (top.get("rulegraph") or [])
                      if r.get("applicable") is True]
    if applicable:
        unk_ids = [r["rule_id"] for r in applicable if r.get("outcome") == "UNKNOWN"]
        if unk_ids:
            lines.append(
                "  - {} of the store's rules actually apply to the {} district on "
                "the top scheme, and **{} are UNKNOWN** ({}). Those checks could "
                "not run — the profit figure assumes answers that do not exist yet."
                .format(len(applicable), district, len(unk_ids), ", ".join("`{}`".format(r) for r in unk_ids))
            )
        else:
            lines.append(
                "  - {} rule(s) applied to the top scheme and all returned PASS. "
                "That is still not a compliance finding: {} context attributes "
                "remain unknown (Section 5).".format(len(applicable), len(gaps))
            )
    else:
        lines.append(
            "  - **None of the store's rules apply to the {} district**, so every "
            "PASS above means 'nothing in the store to check against' — not "
            "'compliant'. No in-district dimensional rule has been human-verified yet.".format(district)
        )

    # Use-allowance honesty: the mass screen runs without a building program.
    ua_prog = ua.get("proposed_uses_present")
    if ua_prog is False:
        lines.append(
            "- Use allowance: every scheme's use verdict is **UNKNOWN** because "
            "no building program was supplied (no proposed uses to check "
            "against the §21A.33 use-table packs). UNKNOWN is never treated "
            "as allowed — see Section 6."
        )
    elif ua_verdicts:
        lines.append(
            "- Use allowance (scheme verdicts): {}."
            .format(" / ".join("**{}** {}".format(ua_verdicts.get(v, 0), v)
                               for v in VERDICTS))
        )

    gap_attrs = [g.get("attribute", "?") for g in gaps[:6]]
    lines.append(
        "- Still unknown: **{} RuleGraph context attributes** could not be "
        "determined from the pipeline inputs (e.g. {}). Resolving them needs "
        "real site/building facts — see Section 5 for each one.".format(len(gaps), ", ".join("`{}`".format(a) for a in gap_attrs))
    )
    fin = report.get("finance_assumptions", {}) or {}
    econ = fin.get("economics", {}) or {}
    rev_conf = econ.get("revenue_confidence", "not labeled")
    lines.append(
        "- Economics confidence: **{}**. Dollar figures rest on assumption-"
        "grade inputs (Section 4), not appraised comps or contractor pricing."
        .format(rev_conf)
    )
    n_unk = verdicts.get("UNKNOWN", 0)
    if n_unk > 0:
        lines.append(
            "- Bottom line: **no scheme on this parcel has a confirmed compliance "
            "finding.** The profit numbers are a geometry-and-assumption sketch "
            "of what is physically drawable — not evidence the project is legal."
        )
    elif not applicable:
        lines.append(
            "- Bottom line: the profit numbers are a geometry-and-assumption "
            "sketch. Compliance against {} rules has not been checked at all — "
            "no in-district rules exist in the verified store yet.".format(district)
        )
    else:
        lines.append(
            "- Bottom line: the top scheme cleared the in-district rules in the "
            "store, but {} unknown attributes and assumption-grade economics "
            "mean this is a screening signal, not a feasibility finding.".format(len(gaps))
        )
    lines.append("")
    return "\n".join(lines)


def _section_1(report):
    z = report.get("zoning", {}) or {}
    zone_label = z.get("zone_label", "not specified")
    zoning_source = z.get("source", "not specified")
    lines = [_section_header(1, "Parcel facts")]
    lines.append("| Fact | Value |")
    lines.append("| --- | --- |")
    lines.append("| parcel_id | `{}` |".format(report.get("parcel_id", "n/a")))
    lines.append("| status | `{}` |".format(report.get("status", "n/a")))
    lines.append(
        "| area | {:,.0f} sqft ({:.2f} acres) |".format(
            report.get("parcel_area_sqft", 0) or 0,
            report.get("parcel_area_acres", 0) or 0,
        )
    )
    lines.append("| CRS | `{}` |".format(report.get("crs", "n/a")))
    lines.append("| zoning district | `{}` |".format(zone_label))
    lines.append(
        "| zoning config source | {} — **{}** |".format(
            zoning_source, _is_placeholder(zoning_source)
        )
    )
    # Geometry notes: clean/flagged counts and road-length range, all from
    # report.json — no external geometry facts are introduced here.
    schemes = report.get("schemes", []) or []
    clean = sum(1 for s in schemes if s.get("clean") is True)
    flagged = sum(1 for s in schemes if s.get("clean") is False)
    roads = []
    for s in schemes:
        pf = s.get("proforma", {}) or {}
        rf = pf.get("road_length_ft", s.get("road_ft"))
        if rf is not None:
            roads.append(rf)
    geom_note = "{} scheme(s): {} geometry-clean, {} flagged".format(len(schemes), clean, flagged)
    if roads:
        geom_note += "; new road {}–{} ft across schemes".format(_num(min(roads)), _num(max(roads)))
    lines.append("| geometry notes | {} |".format(geom_note))
    lines.append("")
    return "\n".join(lines)


def _section_2(report):
    lines = [_section_header(2, "Scheme ranking table (geometry + economics)")]
    note = (report.get("rulegraph") or {}).get("note", "")
    if note:
        lines.append("> {} ".format(note))
        lines.append("")
    lines.append(
        "| rank | scheme | lots | road ft | revenue | total cost | profit | margin | geometry | rg verdict | use verdict |"
    )
    lines.append(
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    schemes = {s["scheme_id"]: s for s in report.get("schemes", [])}
    for rank, sid in enumerate(report.get("ranked_order", []), start=1):
        s = schemes.get(sid, {})
        pf = s.get("proforma", {}) or {}
        clean = s.get("clean", None)
        geom = "clean" if clean is True else ("FLAGGED" if clean is False else "n/a")
        lines.append(
            "| {} | `{}` | {} | {:,.0f} | {} | {} | {} | {} | {} | {} | {} |".format(
                rank,
                sid,
                pf.get("lot_count", s.get("lots", "n/a")),
                pf.get("road_length_ft", s.get("road_ft", 0)) or 0,
                _money(pf.get("revenue")),
                _money(pf.get("total_cost")),
                _money(pf.get("profit")),
                _pct(pf.get("margin")),
                geom,
                _render_scheme_verdict(s),
                s.get("use_verdict", "n/a"),
            )
        )
    lines.append("")
    lines.append(
        "Note: geometry `clean` reflects geometric validation only (lots inside "
        "parcel, no overlaps, min area/frontage). A `clean` scheme is NOT "
        "compliance-confirmed — see Section 3 rule verdicts. `rg verdict` / "
        "`use verdict` use the canonical vocabulary "
        "(PASS / CONDITIONAL_PASS / FAIL / UNKNOWN / MANUAL_REVIEW); UNKNOWN "
        "is never treated as a pass. A scheme's `rg verdict` enum is rendered "
        "with its basis qualifier: 'evaluated against N applicable rules' or "
        "'no applicable rules in the canonical store (district not covered; "
        "compliance NOT confirmed)' — never a bare PASS."
    )
    lines.append("")
    return "\n".join(lines)


def _verdict_rank(outcome):
    # Sort order: most severe first — UNKNOWN, FAIL, MANUAL_REVIEW,
    # CONDITIONAL_PASS, PASS.
    return {v: i for i, v in enumerate(VERDICTS)}.get(outcome, 99)


def _applicable_count(scheme: Dict) -> int:
    """How many verified rules actually evaluated against this scheme.

    Prefers the pipeline-computed 'rulegraph_applicable_rules'; falls back
    to counting applicable:true in the per-rule list so legacy reports
    (pre-dating the count) still render honestly.
    """
    n = scheme.get("rulegraph_applicable_rules")
    if isinstance(n, int):
        return n
    return sum(
        1 for r in (scheme.get("rulegraph") or []) if r.get("applicable") is True
    )


def _render_scheme_verdict(scheme: Dict) -> str:
    """Human-facing scheme verdict carrying the rg_verdict_basis qualifier.

    Mirrors screen/screener.py's rg_verdict_basis semantics ("evaluated" /
    "no_applicable_rules"): the verdict enum itself is never relabeled, but a
    PASS is never rendered bare. A PASS with zero applicable verified rules
    renders the explicit NOT-confirmed qualifier; a PASS with N applicable
    rules names its evaluated count.
    """
    verdict = scheme.get("rulegraph_verdict", "n/a")
    n = _applicable_count(scheme)
    if verdict == "PASS" and n == 0:
        return ("**PASS — no applicable rules in the canonical store "
                "(district not covered; compliance NOT confirmed)**")
    if verdict == "PASS":
        return ("**PASS — evaluated against {} applicable rule{}**".format(
            n, "" if n == 1 else "s"))
    return "**{}**".format(verdict)


def _aliased(evidence, *keys):
    """First non-empty value under any of the alias keys (canonical store
    uses quote/citation; the old 10-rule store used source_quote/section)."""
    for key in keys:
        value = (evidence or {}).get(key)
        if value:
            return value
    return None


def _format_rule_evidence(rule, evidence):
    """Render one rule's section-3 block, quoting the store verbatim."""
    rid = rule.get("rule_id", "?")
    outcome = rule.get("outcome", "UNKNOWN")
    title = (evidence or {}).get("title") or (evidence or {}).get("claim") \
        or (evidence or {}).get("_caddy_rule_name") or ""
    tag = "**{}** {}".format(outcome, UNKNOWN_MARKER) if outcome == "UNKNOWN" else "**{}**".format(outcome)
    lines = []
    lines.append("### `{}` — {} — {}".format(rid, title, tag))
    lines.append("")
    lines.append("- Verdict: {}".format(tag))
    lines.append("- Applicable to this scheme: `{}`".format(rule.get("applicable")))
    lines.append("- Reason: {}".format(rule.get("reason", "not given")))
    lines.append("")
    if evidence is None:
        lines.append(
            "> **GAP:** rule `{}` was evaluated but is NOT present in the "
            "verified rule store. Its evidence cannot be shown.".format(rid)
        )
        lines.append("")
        return "\n".join(lines)
    hv = evidence.get("human_verification", {}) or {}
    dists = _rule_districts(evidence)
    lines.append("**Claim:** {}".format(
        _aliased(evidence, "claim", "_caddy_rule_name") or "n/a"))
    lines.append("")
    lines.append("**Verbatim source quote (from store):**")
    lines.append("")
    lines.append("> {}".format(_aliased(evidence, "quote", "source_quote") or "n/a"))
    lines.append("")
    lines.append("- Citation: section `{}` — {}".format(
        _aliased(evidence, "citation", "section") or "n/a",
        evidence.get("edition_hint", "")))
    lines.append("- District scope: `{}`".format(", ".join(dists) if dists else "n/a"))
    lines.append("- Source edition: {}".format(_edition_of(evidence)))
    if evidence.get("caveats"):
        lines.append("- Caveats: {}".format("; ".join(evidence["caveats"])))
    exec_params = evidence.get("params")
    canon_params = evidence.get("canonical_params")
    if exec_params:
        lines.append("- Execution params: `{}`".format(
            json.dumps(exec_params, sort_keys=True)))
    if canon_params:
        lines.append("- Canonical verified value: `{}`".format(
            json.dumps(canon_params, sort_keys=True)))
    lines.append("")
    lines.append(
        "**Human verification (described from store record; the report creates no verdict):** "
        "result=`{}`, verified_by=`{}`, verified_on=`{}`".format(
            hv.get("result", "n/a"), hv.get("verified_by", "n/a"), hv.get("verified_on", "n/a")
        )
    )
    lines.append("")
    return "\n".join(lines)


def _edition_of(evidence):
    return evidence.get("_edition", "")


def _section_3(report, rules_by_id, store):
    lines = [_section_header(3, "Per-scheme RuleGraph verdicts")]
    lines.append(
        "> **How to read this:** each rule shows its verdict for this scheme, "
        "followed by the rule's verbatim evidence from the verified store. "
        "**{}** verdicts are listed first and are never treated as passes. "
        "Rules district-scoped out of this parcel are summarized, not quoted "
        "in full.".format(UNKNOWN_MARKER)
    )
    lines.append("")
    schemes = {s["scheme_id"]: s for s in report.get("schemes", [])}
    for sid in report.get("ranked_order", []):
        s = schemes.get(sid, {})
        header_verdict = _render_scheme_verdict(s)
        lines.append("### Scheme `{}` — rulegraph verdict: {}".format(sid, header_verdict))
        lines.append("")
        evaluated = s.get("rulegraph") or []
        applicable = [r for r in evaluated if r.get("applicable") is True]
        scoped_out = [r for r in evaluated if r.get("applicable") is not True]
        for rule in sorted(applicable, key=lambda r: _verdict_rank(r.get("outcome"))):
            lines.append(_format_rule_evidence(rule, rules_by_id.get(rule.get("rule_id"))))
        if scoped_out:
            ids = ", ".join("`{}`".format(r.get("rule_id")) for r in scoped_out)
            lines.append(
                "- {} rule(s) district-scoped out of this parcel (not applicable, "
                "not evidence of anything): {}".format(len(scoped_out), ids)
            )
            lines.append("")
        lines.append("")
    return "\n".join(lines)


def _section_4(report):
    lines = [_section_header(4, "Economics breakdown — top-ranked scheme")]
    ranked = report.get("ranked_order", [])
    schemes = {s["scheme_id"]: s for s in report.get("schemes", [])}
    if not ranked:
        lines.append("No schemes ranked.\n")
        return "\n".join(lines)
    sid = ranked[0]
    s = schemes.get(sid, {})
    pf = s.get("proforma", {}) or {}
    asm = pf.get("assumptions", {}) or {}
    lines.append("Top scheme: `{}` ({} lots).".format(sid, pf.get("lot_count", s.get("lots", "n/a"))))
    lines.append("")
    lines.append("| Line | Amount |")
    lines.append("| --- | --- |")
    lines.append("| Revenue | {} |".format(_money(pf.get("revenue"))))
    lines.append("| — infrastructure cost | {} |".format(_money(pf.get("infra_cost"))))
    lines.append("| — soft costs | {} |".format(_money(pf.get("soft_costs"))))
    lines.append("| — contingency | {} |".format(_money(pf.get("contingency"))))
    lines.append("| **Total cost** | **{}** |".format(_money(pf.get("total_cost"))))
    lines.append("| **Profit** | **{}** |".format(_money(pf.get("profit"))))
    lines.append("| **Margin** | **{}** |".format(_pct(pf.get("margin"))))
    lines.append("")
    lines.append("**Finance assumptions and their source labels:**")
    lines.append("")
    lines.append("| Assumption | Value | Source |")
    lines.append("| --- | --- | --- |")
    for key in ("sale_price_per_lot", "road_cost_per_lf", "soft_costs_fixed", "contingency_pct", "road_length_ft"):
        if key in asm:
            lines.append("| `{}` | {} | |".format(key, asm[key]))
    src = asm.get("source", "") or report.get("finance_assumptions", {}).get("source", "")
    lines.append("")
    lines.append("- Stated source text: {}".format(src if src else "not specified"))
    lines.append("- Label: **{}**".format(_is_placeholder(src)))
    lines.append("")
    return "\n".join(lines)


def _section_5(report):
    lines = [_section_header(5, "Gaps & unknowns — what this report does NOT know")]
    lines.append(
        "> Nothing in this section defaults to compliance. Every attribute the "
        "RuleGraph could not determine is listed explicitly, with what would "
        "be needed to resolve it."
    )
    lines.append("")
    rg = report.get("rulegraph") or {}
    gaps = rg.get("gaps") or []
    ctx_prov = rg.get("context_provenance") or {}
    program = rg.get("program_supplied")
    lines.append("- Program supplied to RuleGraph: `{}`".format(program))
    lines.append("- Rules evaluated per scheme: `{}`".format(rg.get("rules_evaluated", "n/a")))
    lines.append("")
    lines.append("### Context attributes that were UNKNOWN ({} total)".format(len(gaps)))
    lines.append("")
    for g in gaps:
        attr = g.get("attribute", "?")
        prov = ctx_prov.get(attr, {}) or {}
        needed = prov.get("detail") or g.get("needed_from", "unknown")
        lines.append("- **`{}`** — needed from: {}".format(attr, needed))
    lines.append("")
    # Also surface every UNKNOWN rule outcome here so UNKNOWNs can never be
    # buried in per-scheme detail alone.
    lines.append("### Rule outcomes that were UNKNOWN (by scheme)")
    lines.append("")
    schemes = {s["scheme_id"]: s for s in report.get("schemes", [])}
    any_unknown = False
    for sid in report.get("ranked_order", []):
        s = schemes.get(sid, {})
        unk = [r for r in (s.get("rulegraph") or []) if r.get("outcome") == "UNKNOWN"]
        if unk:
            any_unknown = True
            lines.append("- Scheme `{}`: {} — {}".format(
                sid,
                ", ".join("`{}`".format(r.get("rule_id")) for r in unk),
                "; ".join("{} ({})".format(r.get("rule_id"), r.get("reason", "no reason")) for r in unk),
            ))
    if not any_unknown:
        lines.append("- None: no UNKNOWN rule outcomes in any scheme.")
    lines.append("")
    # Use-allowance unknowns live here too (detail in Section 6).
    ua = report.get("use_allowance") or {}
    if ua.get("proposed_uses_present") is False:
        lines.append(
            "### Use-allowance unknowns\n\n"
            "- No building program was supplied, so no proposed uses exist to "
            "check against the §21A.33 use-table packs. Every scheme's use "
            "verdict is **UNKNOWN** — explicitly not allowed (Section 6).\n"
        )
    lines.append("")
    return "\n".join(lines)


def _section_6(report):
    lines = [_section_header(6, "Use allowance (21A.33)")]
    lines.append(
        "> Use-allowance verdicts are **machine-evaluated** against the "
        "human-verified §21A.33 use-table packs. The machine evaluates; it "
        "never verifies. UNKNOWN is never treated as allowed."
    )
    lines.append("")
    ua = report.get("use_allowance") or {}
    fps = ua.get("pack_fingerprints") or {}
    lines.append("- Use pack source: `{}`".format(ua.get("pack", "n/a")))
    lines.append("- Pack fingerprints (recorded in report.json):")
    for key in ("m1_os_pl", "mu"):
        lines.append("  - `{}`: `{}`".format(key, fps.get(key, "n/a")))
    lines.append("- Combined pack fingerprint: `{}`".format(ua.get("pack_fingerprint", "n/a")))
    lines.append("- Rows parsed: `{}`".format(ua.get("rows_parsed", "n/a")))
    lines.append("- Program supplied: `{}`; proposed uses present: `{}`".format(
        ua.get("program_supplied"), ua.get("proposed_uses_present")))
    lines.append("")
    note = ua.get("note", "")
    if note:
        lines.append("> {}".format(note))
        lines.append("")
    if ua.get("proposed_uses_present") is False:
        lines.append(
            "**No building program was supplied to this run, so no proposed "
            "uses exist to evaluate. Every scheme's use verdict is UNKNOWN by "
            "design — this is a stated input gap, not a finding, and UNKNOWN "
            "is never treated as allowed.**"
        )
        lines.append("")
    verdicts = ua.get("scheme_verdicts") or {}
    lines.append(
        "Scheme use verdicts: {}".format(
            " / ".join("**{}** {}".format(verdicts.get(v, 0), v) for v in VERDICTS)
        )
    )
    lines.append("")
    schemes = {s["scheme_id"]: s for s in report.get("schemes", [])}
    if report.get("ranked_order"):
        lines.append("| scheme | use verdict | applicable rows | detail |")
        lines.append("| --- | --- | --- | --- |")
        for sid in report.get("ranked_order", []):
            s = schemes.get(sid, {})
            per_use = s.get("use_allowance") or []
            detail = "; ".join(
                "{}: {} ({})".format(p.get("use"), p.get("verdict"), p.get("reason", ""))
                for p in per_use
            ) if per_use else "no proposed uses — UNKNOWN by design"
            lines.append("| `{}` | {} | {} | {} |".format(
                sid, s.get("use_verdict", "n/a"),
                s.get("use_applicable_rows", "n/a"), detail))
        lines.append("")
    return "\n".join(lines)


def _section_7(report, store, recomputed_fp, report_fp):
    lines = [_section_header(7, "Provenance footer")]
    recorded = (report.get("rulegraph") or {}).get("store_fingerprint", "not recorded")
    lines.append("- Rule store: `{}`".format((report.get("rulegraph") or {}).get("store", "n/a")))
    lines.append("- Store fingerprint recorded in report.json: `{}`".format(recorded))
    lines.append("- Store fingerprint recomputed now: `{}`".format(recomputed_fp))
    if recorded != recomputed_fp:
        lines.append(
            "- **MISMATCH:** recomputed fingerprint does not match the fingerprint "
            "recorded in report.json. The store may have changed since the report "
            "was generated — treat rule evidence above with caution."
        )
    else:
        lines.append("- Fingerprint check: MATCH (store unchanged since pipeline run).")
    ua = report.get("use_allowance") or {}
    fps = ua.get("pack_fingerprints") or {}
    lines.append("- Use-pack fingerprints (recorded in report.json): "
                 "m1_os_pl=`{}`, mu=`{}`".format(fps.get("m1_os_pl", "n/a"),
                                                 fps.get("mu", "n/a")))
    lines.append("- Source report.json fingerprint: `{}`".format(report_fp))
    lines.append(
        "- Determinism: this report is regenerated byte-identically from the "
        "same report.json + rule store (no wall-clock timestamps anywhere)."
    )
    lines.append("- **{}**".format(MACHINE_DRAFT_LABEL))
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# No-scheme and error reports
# ---------------------------------------------------------------------------

def _section_0_no_schemes(report):
    lines = [_section_header(0, "What this means (plain-English summary)")]
    lines.append(
        "> **Machine-generated from the numbers in this report — not a "
        "recommendation, not human-verified.**\n"
    )
    z = report.get("zoning", {}) or {}
    district = z.get("district", "not specified")
    pid = report.get("parcel_id", "n/a")
    acres = report.get("parcel_area_acres", 0) or 0
    gen = report.get("scheme_generation") or {}
    lines.append(
        "- This parcel (`{}`) covers **{:.2f} acres** in the **{}** district. "
        "The pipeline drew **no subdivision schemes** for it — this is an "
        "explicit diagnostic outcome, not an omission.".format(pid, acres, district)
    )
    lines.append(
        "- Generation diagnostic: `{}`.".format(gen.get("verdict", "not recorded"))
    )
    reasons = gen.get("primary_blocking_reasons") or {}
    if reasons:
        lines.append(
            "- Blocking reasons ({} candidate configuration(s) evaluated): {}."
            .format(gen.get("candidates_evaluated", "?"),
                    "; ".join("`{}`: {}".format(k, v) for k, v in sorted(reasons.items())))
        )
    fb = gen.get("fallback_skipped_reason") or gen.get("fallback_used")
    if fb:
        lines.append("- Fallback note: {}".format(fb))
    lines.append(
        "- Bottom line: no geometry or economics were produced because no "
        "scheme could be drawn under the screening configuration. The "
        "diagnostic above names why; nothing was skipped silently."
    )
    lines.append("")
    return "\n".join(lines)


def _section_2_no_schemes(report):
    lines = [_section_header(2, "Scheme generation diagnostics")]
    lines.append(
        "No schemes were drawn for this parcel. The pipeline's generation "
        "diagnostics are reproduced verbatim below — a named reason, not a gap."
    )
    lines.append("")
    gen = report.get("scheme_generation") or {}
    lines.append("| Diagnostic | Value |")
    lines.append("| --- | --- |")
    for key in ("strategy", "verdict", "candidates_evaluated",
                "size_threshold_ratio", "area_min_lot_ratio",
                "primary_min_lots", "primary_schemes_kept",
                "top_blocking_reason", "fallback_used",
                "fallback_skipped_reason"):
        if key in gen:
            lines.append("| `{}` | {} |".format(key, gen[key]))
    reasons = gen.get("primary_blocking_reasons") or {}
    if reasons:
        lines.append("| `primary_blocking_reasons` | {} |".format(
            "; ".join("{}: {}".format(k, v) for k, v in sorted(reasons.items()))))
    lines.append("")
    return "\n".join(lines)


def _section_3_5_skipped():
    lines = [_section_header(3, "Per-scheme RuleGraph verdicts")]
    lines.append("Skipped: no schemes were drawn, so no rules were evaluated.\n")
    return "\n".join(lines)


def _section_4_no_schemes():
    lines = [_section_header(4, "Economics breakdown — top-ranked scheme")]
    lines.append("Not applicable: no schemes were drawn, so no economics were computed.\n")
    return "\n".join(lines)


def _section_5_no_schemes(report):
    lines = [_section_header(5, "Gaps & unknowns — what this report does NOT know")]
    lines.append(
        "> Nothing in this section defaults to compliance."
    )
    lines.append("")
    rg = report.get("rulegraph") or {}
    gaps = rg.get("gaps") or []
    lines.append(
        "- RuleGraph was not run against any scheme (none drawn). The context "
        "attributes below were already unknown at the parcel level:"
    )
    lines.append("")
    for g in gaps:
        lines.append("- **`{}`** — needed from: {}".format(
            g.get("attribute", "?"), g.get("needed_from", "unknown")))
    lines.append("")
    ua = report.get("use_allowance") or {}
    if ua.get("proposed_uses_present") is False:
        lines.append(
            "- Use allowance was not evaluated (no schemes, no building "
            "program). No use is treated as allowed.\n"
        )
    lines.append("")
    return "\n".join(lines)


def _section_6_no_schemes(report):
    lines = [_section_header(6, "Use allowance (21A.33)")]
    ua = report.get("use_allowance") or {}
    fps = ua.get("pack_fingerprints") or {}
    lines.append(
        "Not evaluated: no schemes were drawn and no building program was "
        "supplied. Use-pack fingerprints (recorded in report.json) for "
        "reference: m1_os_pl=`{}`, mu=`{}`.".format(
            fps.get("m1_os_pl", "n/a"), fps.get("mu", "n/a"))
    )
    lines.append("")
    return "\n".join(lines)


def generate_no_schemes(report, store, preface_md_path=None, append_md_path=None):
    """Evidence report for a parcel where the pipeline drew no schemes."""
    recomputed_fp = store_fingerprint(store)
    report_fp = report_fingerprint(report)
    parts = [_banner(report.get("parcel_id", "n/a"))]
    if preface_md_path:
        with open(preface_md_path) as f:
            parts.append(f.read().rstrip() + "\n")
    parts.append(_provisional_banner(report))
    parts.append(_section_0_no_schemes(report))
    parts.append(_section_1(report))
    parts.append(_section_2_no_schemes(report))
    parts.append(_section_3_5_skipped())
    parts.append(_section_4_no_schemes())
    parts.append(_section_5_no_schemes(report))
    parts.append(_section_6_no_schemes(report))
    if append_md_path:
        with open(append_md_path) as f:
            parts.append(f.read().rstrip() + "\n")
    parts.append(_section_7(report, store, recomputed_fp, report_fp))
    return "\n".join(parts)


def generate_error_report(parcel_id: str, error: str,
                          district: str = "unknown",
                          zone_label: str = "unknown") -> str:
    """Explicit error report for a parcel the screener could not process.

    Never silently skipped: the error text is quoted verbatim and every
    section states plainly that no results exist.
    """
    parts = [
        "# Evidence report — parcel `{}`\n\n> **{}**\n\n"
        "**ERROR — this parcel could not be screened.** The error below is "
        "quoted verbatim from the screening run. No schemes, no economics, "
        "and no compliance verdicts exist for this parcel — nothing was "
        "omitted, the run failed loudly.\n".format(parcel_id, MACHINE_DRAFT_LABEL),
        "## 0. What this means (plain-English summary)\n\n"
        "- The screening run raised an error for this parcel and recorded an "
        "explicit error row instead of silently dropping it.\n\n",
        "## 1. Parcel facts\n\n"
        "| Fact | Value |\n| --- | --- |\n"
        "| parcel_id | `{}` |\n| status | `error` |\n"
        "| zoning district | `{}` |\n| zone label | `{}` |\n\n".format(
            parcel_id, district, zone_label),
        "## 2. Error detail\n\n```\n{}\n```\n\n".format(error or "no error text recorded"),
        "## 3. Per-scheme RuleGraph verdicts\n\n"
        "Not evaluated: the parcel errored before scheme generation.\n\n",
        "## 4. Economics breakdown — top-ranked scheme\n\n"
        "Not computed: the parcel errored before scheme generation.\n\n",
        "## 5. Gaps & unknowns — what this report does NOT know\n\n"
        "- Everything: the parcel errored before any pipeline stage ran. "
        "Re-running the parcel (not reinterpreting this report) is the fix.\n\n",
        "## 6. Use allowance (21A.33)\n\n"
        "Not evaluated: the parcel errored before scheme generation.\n\n",
        "## 7. Provenance footer\n\n"
        "- No rule-store or use-pack fingerprints apply: no report.json was "
        "produced for this parcel.\n"
        "- **{}**\n".format(MACHINE_DRAFT_LABEL),
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def generate_from_objects(report: Dict, store: Dict,
                          preface_md_path: Optional[str] = None,
                          append_md_path: Optional[str] = None) -> str:
    """Build the report markdown from loaded objects (deterministic)."""
    status = report.get("status", "")
    schemes = report.get("schemes") or []
    if status == "error":
        return generate_error_report(
            report.get("parcel_id", "n/a"),
            (report.get("error") or ""),
            district=(report.get("zoning") or {}).get("district", "unknown"),
        )
    if status != "ok" or not schemes:
        return generate_no_schemes(report, store, preface_md_path, append_md_path)

    edition = store.get("edition", "")
    # Copy, never mutate the caller's store: the _edition annotation is a
    # report-local convenience, and the engine fingerprint is defined over
    # the un-annotated store.
    rules_by_id = {}
    for rid, r in _key_rules(store).items():
        rc = dict(r)
        rc["_edition"] = edition
        rules_by_id[rid] = rc
    recomputed_fp = store_fingerprint(store)
    report_fp = report_fingerprint(report)

    parts = [_banner(report.get("parcel_id", "n/a"))]
    if preface_md_path:
        with open(preface_md_path) as f:
            parts.append(f.read().rstrip() + "\n")
    parts.append(_provisional_banner(report))
    parts.append(_section_0(report))
    parts.append(_section_1(report))
    parts.append(_section_2(report))
    parts.append(_section_3(report, rules_by_id, store))
    parts.append(_section_4(report))
    parts.append(_section_5(report))
    parts.append(_section_6(report))
    if append_md_path:
        with open(append_md_path) as f:
            parts.append(f.read().rstrip() + "\n")
    parts.append(_section_7(report, store, recomputed_fp, report_fp))
    return "\n".join(parts)


def generate(report_json_path, rule_store_path, out_markdown_path,
             preface_md_path=None, append_md_path=None):
    """Build the per-parcel evidence report and write it to out_markdown_path.

    preface_md_path / append_md_path optionally inject raw markdown blocks
    (e.g. a deep-dive narrative): the preface goes after the header banner,
    the append block goes before the provenance footer. The injected text is
    inserted verbatim — the report never edits it.
    """
    with open(report_json_path) as f:
        report = json.load(f)
    with open(rule_store_path) as f:
        store = json.load(f)
    text = generate_from_objects(report, store, preface_md_path, append_md_path)
    with open(out_markdown_path, "w") as f:
        f.write(text)
    return out_markdown_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="NERON per-parcel evidence report")
    parser.add_argument("report_json", help="pipeline outputs/report.json")
    parser.add_argument("--store", required=True, help="RuleGraph verified_rules.json")
    parser.add_argument("--out", required=True, help="output markdown path")
    parser.add_argument("--preface", default=None,
                        help="markdown file inserted verbatim after the header banner")
    parser.add_argument("--append", default=None,
                        help="markdown file inserted verbatim before the provenance footer")
    args = parser.parse_args(argv)
    out = generate(args.report_json, args.store, args.out,
                   preface_md_path=args.preface, append_md_path=args.append)
    print("wrote: {}".format(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
