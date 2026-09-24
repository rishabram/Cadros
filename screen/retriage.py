"""UNKNOWN re-triage: recompute the per-district blocker map on demand.

Reads every parcel's report.json under a mass-screen output directory and
regenerates UNKNOWN_TRIAGE.md from the per-scheme `rulegraph` detail —
deterministically, with no hand counting, so the triage never goes stale
when Caddy's native-store params land (feeds the rescreen-delta wave).

Blocker classes are derived from the engine's own UNKNOWN reason strings:
  - "no evaluator registered ..." -> stored-but-not-executable
  - anything else                 -> context gap (needs site/building facts)

A hand-maintained notes file (<screen-dir>/UNKNOWN_TRIAGE_NOTES.md by
default) is appended verbatim after the machine-computed sections; the
script never edits it.

Deterministic: parcels and rules processed in sorted order; no wall-clock
timestamps anywhere (provenance is the screen dir + store fingerprint).

Usage:
    venv/bin/python -m screen.retriage --screen-dir screen/outputs/real_slco_v3 \\
        --store rulegraph/verified_rules.json [--out <path>] [--notes <path>]
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from rulegraph.fingerprint import canonical_hash  # noqa: E402

VERDICTS = ("UNKNOWN", "FAIL", "MANUAL_REVIEW", "CONDITIONAL_PASS", "PASS")


def _store_fingerprint(store_path):
    with open(store_path) as f:
        store = json.load(f)
    return canonical_hash({"rules": store["rules"]})


def _key_rules(store):
    rules = store.get("rules", {})
    if isinstance(rules, dict):
        return rules
    return {r["rule_id"]: r for r in rules}


def _descriptor(evidence):
    """Short human descriptor for a store record (never invents one)."""
    if not evidence:
        return ""
    name = (
        evidence.get("title")
        or evidence.get("claim")
        or evidence.get("_caddy_rule_name")
        or ""
    )
    name = " ".join(str(name).split())
    return name[:60]


def _blocker_class(reasons):
    """Classify from the engine's own UNKNOWN reason strings."""
    if reasons and all(r.startswith("no evaluator registered") for r in reasons):
        return "stored-but-not-executable"
    return "context gap (needs site/building facts)"


def aggregate(screen_dir, store):
    """Walk every parcel report.json; return the triage aggregates."""
    rules_by_id = _key_rules(store)
    scheme_verdicts = Counter()
    n_schemes = 0
    # district -> verdict -> count
    district_verdicts = defaultdict(Counter)
    # district -> rule_id -> outcome -> count ; and reasons per rule
    rule_outcomes = defaultdict(lambda: defaultdict(Counter))
    rule_reasons = defaultdict(lambda: defaultdict(set))
    vacuous = defaultdict(int)  # district -> vacuous-PASS scheme count

    parcel_ids = sorted(
        name
        for name in os.listdir(screen_dir)
        if os.path.isdir(os.path.join(screen_dir, name))
        and os.path.isfile(os.path.join(screen_dir, name, "report.json"))
    )
    if not parcel_ids:
        raise RuntimeError("no parcel report.json files under %s" % screen_dir)

    for pid in parcel_ids:
        with open(os.path.join(screen_dir, pid, "report.json")) as f:
            rep = json.load(f)
        district = (rep.get("zoning") or {}).get("district", "unknown")
        for s in rep.get("schemes") or []:
            n_schemes += 1
            verdict = s.get("rulegraph_verdict", "n/a")
            scheme_verdicts[verdict] += 1
            district_verdicts[district][verdict] += 1
            n_applicable = s.get("rulegraph_applicable_rules")
            if verdict == "PASS" and n_applicable == 0:
                vacuous[district] += 1
            for rule in s.get("rulegraph") or []:
                if rule.get("applicable") is not True:
                    continue
                rid = rule.get("rule_id", "?")
                outcome = rule.get("outcome", "UNKNOWN")
                rule_outcomes[district][rid][outcome] += 1
                if outcome == "UNKNOWN":
                    rule_reasons[district][rid].add(rule.get("reason", ""))

    return {
        "n_schemes": n_schemes,
        "scheme_verdicts": scheme_verdicts,
        "district_verdicts": district_verdicts,
        "rule_outcomes": rule_outcomes,
        "rule_reasons": rule_reasons,
        "vacuous": vacuous,
        "descriptors": {rid: _descriptor(ev) for rid, ev in rules_by_id.items()},
    }


def _rule_list(rule_ids, descriptors):
    parts = []
    for rid in sorted(rule_ids):
        d = descriptors.get(rid, "")
        parts.append("`{}`{}".format(rid, " ({})".format(d) if d else ""))
    return ", ".join(parts)


def render(agg, screen_name, store_fp):
    """Render the machine-computed triage markdown (deterministic)."""
    sv = agg["scheme_verdicts"]
    lines = [
        "# UNKNOWN triage — {} (canonical 59-rule store)".format(screen_name),
        "",
        "> **machine-draft — not human-verified output.** Recomputed deterministically "
        "from the per-scheme `rulegraph` detail in each parcel's `report.json` "
        "({} schemes; no hand counting). Rule store fingerprint `{}`. "
        "UNKNOWN is never treated as compliance; zero new verdicts are created "
        "by this file.".format(agg["n_schemes"], store_fp),
        "",
        "## Headline",
        "",
    ]
    counts = " / ".join(
        "**{}** {}".format(sv.get(v, 0), v) for v in VERDICTS
    )
    lines.append(
        "{} schemes: {} at the scheme verdict level (verdict = most restrictive "
        "applicable rule outcome; any applicable UNKNOWN tips the scheme to "
        "UNKNOWN — UNKNOWN never defaults to compliance).".format(
            agg["n_schemes"], counts
        )
    )
    lines.append("")
    if sv.get("FAIL", 0):
        lines.append("**{} scheme-level FAIL(s) — see blocker map.**".format(sv["FAIL"]))
        lines.append("")
    vac = agg["vacuous"]
    if vac:
        total_vac = sum(vac.values())
        by_dist = ", ".join(
            "{} ×{}".format(d, c) for d, c in sorted(vac.items())
        )
        lines.append(
            "The **{}** PASS schemes are all in districts with **no rules in the "
            "canonical store** ({}) — every rule district-scopes out, so they "
            "PASS vacuously (basis: `no_applicable_rules`). No substantive "
            "compliance was confirmed on any scheme.".format(total_vac, by_dist)
        )
        lines.append("")
    lines.append("## Blocker map (applicable rules with UNKNOWN outcome, per district)")
    lines.append("")
    lines.append("| District | Schemes | Blocked by | Blocker class |")
    lines.append("|---|---|---|---|")
    for district in sorted(agg["rule_outcomes"]):
        n_dist = sum(agg["district_verdicts"][district].values())
        # Group UNKNOWN rules by blocker class; keep one row per class so the
        # table stays readable and stable.
        by_class = defaultdict(set)
        for rid, outcomes in agg["rule_outcomes"][district].items():
            if outcomes.get("UNKNOWN", 0) == 0:
                continue
            cls = _blocker_class(agg["rule_reasons"][district][rid])
            by_class[cls].add(rid)
        for cls in sorted(by_class):
            lines.append(
                "| {} | {} | {} | {} |".format(
                    district, n_dist,
                    _rule_list(by_class[cls], agg["descriptors"]), cls,
                )
            )
        # PASSing applicable rules (absence claims etc.) get their own row so
        # they are never mistaken for blockers.
        passed = [
            rid for rid, outcomes in sorted(agg["rule_outcomes"][district].items())
            if outcomes.get("UNKNOWN", 0) == 0 and outcomes.get("PASS", 0) > 0
        ]
        if passed:
            lines.append(
                "| {} | {} | {} | PASS (verified absence / executable) |".format(
                    district, n_dist, _rule_list(passed, agg["descriptors"])
                )
            )
    lines.append("")
    lines.append("## Rule-level totals (applicable only)")
    lines.append("")
    for district in sorted(agg["rule_outcomes"]):
        totals = Counter()
        for outcomes in agg["rule_outcomes"][district].values():
            totals.update(outcomes)
        lines.append(
            "- {}: {}".format(
                district,
                ", ".join(
                    "{} {}".format(totals.get(v, 0), v) for v in VERDICTS
                    if totals.get(v, 0)
                ) or "no applicable rule outcomes",
            )
        )
    lines.append("")
    return "\n".join(lines)


def retriage(screen_dir, store_path, out_path=None, notes_path=None):
    with open(store_path) as f:
        store = json.load(f)
    store_fp = _store_fingerprint(store_path)
    agg = aggregate(screen_dir, store)
    screen_name = os.path.basename(os.path.normpath(screen_dir))
    text = render(agg, screen_name, store_fp)
    if notes_path is None:
        notes_path = os.path.join(screen_dir, "UNKNOWN_TRIAGE_NOTES.md")
    if os.path.isfile(notes_path):
        with open(notes_path) as f:
            text += "\n---\n\n" + f.read().rstrip() + "\n"
    else:
        text += ("\n---\n\n> No analyst notes file found at `{}`. Create one "
                 "to attach hand-maintained analysis; it is appended verbatim "
                 "and never edited by the script.\n").format(notes_path)
    out_path = out_path or os.path.join(screen_dir, "UNKNOWN_TRIAGE.md")
    with open(out_path, "w") as f:
        f.write(text)
    return out_path, agg


def main(argv=None):
    parser = argparse.ArgumentParser(description="UNKNOWN re-triage")
    parser.add_argument("--screen-dir", required=True,
                        help="mass-screen output dir")
    parser.add_argument("--store", required=True,
                        help="RuleGraph verified_rules.json")
    parser.add_argument("--out", default=None,
                        help="output path (default: <screen-dir>/UNKNOWN_TRIAGE.md)")
    parser.add_argument("--notes", default=None,
                        help="analyst notes file (default: <screen-dir>/UNKNOWN_TRIAGE_NOTES.md)")
    args = parser.parse_args(argv)
    out_path, agg = retriage(args.screen_dir, args.store, args.out, args.notes)
    sv = agg["scheme_verdicts"]
    print("wrote {}".format(out_path))
    print("schemes: {} | {}".format(
        agg["n_schemes"],
        ", ".join("{} {}".format(sv.get(v, 0), v) for v in VERDICTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
