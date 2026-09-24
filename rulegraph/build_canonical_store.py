"""Build the canonical 59-rule engine store from Caddy's store_view.

Reads:
  caddy_drop/store_view_lebron_schema.json  (59 canonical rules, LeBron schema)
  rulegraph/verified_rules.json             (old 10-rule store — ONLY for the
                                             structured execution params of
                                             the 10 already-executable rules)

Writes:
  rulegraph/verified_rules.json             (new canonical engine store)
after archiving the old file to:
  rulegraph/verified_rules.v1_10rule.json    (never deleted, never edited)

DESIGN (per the 2026-09-24 integration wave):
- Every canonical rule is ingested with its citation, quote, canonical
  value/unit, and human_verification record — the store is the complete
  verified dimensional record even where the engine cannot yet execute it.
- An "evaluator" key is assigned ONLY where execution is provably correct
  from the rule text alone:
    * the 10 already-executable rules (structured params carried over from
      the old store — their evaluators are tested and form-scoped correctly);
    * OS-01 ("None required" -> the existing no_district_minimum predicate);
    * M-1-02 (flat yard minima -> the new min_yards_flat predicate; no form,
      street, or abutment scoping in the rule text).
- All other rules (MU-5/MU-6/MU-11 height and yard tables, M-1-01/03/04/05/06,
  OS-02/03/04/05, PL-01/02/03, MU-OPENSPACE-01, ...) carry NO evaluator key:
  the engine yields UNKNOWN ("no evaluator registered") for them. This is
  deliberate — the store_view projection does not carry the building-form /
  use / location scoping the native store holds, and an evaluator written
  from the projection alone risks false FAILs. Executable coverage grows as
  scoped params arrive from Caddy's native store; it is NEVER grown by
  guessing.
- MU-OPENSPACE-01's district ("MU-5, MU-6, MU-11") is normalized to a
  "districts" list; the engine scopes by membership.

Re-running this script is idempotent (same inputs -> same store bytes).
"""
from __future__ import annotations

import json
import os
import shutil

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRATCH = os.path.dirname(_HERE)

STORE_VIEW = os.path.join(_SCRATCH, "caddy_drop", "store_view_lebron_schema.json")
OLD_STORE = os.path.join(_HERE, "verified_rules.json")
ARCHIVE = os.path.join(_HERE, "verified_rules.v1_10rule.json")

# Rules executable beyond the carried-over 10. Key: rule_id ->
# (evaluator_name, execution_params). Everything not listed here (and not in
# the old store) ingests WITHOUT an evaluator -> engine yields UNKNOWN.
EXTRA_EXECUTABLE = {
    "OS-01": (
        "no_district_minimum",
        {"district_label": "the OS Open Space District"},
    ),
    "M-1-02": (
        "min_yards_flat",
        {
            "min_front_ft": 15,
            "min_corner_side_ft": 15,
            "min_interior_side_ft": 0,
            "min_rear_ft": 0,
        },
    ),
}

# rule_ids whose comma-joined district string must become a districts list.
MULTI_DISTRICT = {
    "MU-OPENSPACE-01": ["MU-5", "MU-6", "MU-11"],
}


def main() -> None:
    with open(STORE_VIEW, encoding="utf-8") as fh:
        canonical = json.load(fh)["rules"]
    # Migration source of truth: the archived 10-rule store (written on the
    # first build). On the very first build it is OLD_STORE itself.
    old_source = ARCHIVE if os.path.exists(ARCHIVE) else OLD_STORE
    with open(old_source, encoding="utf-8") as fh:
        old_store = json.load(fh)
    old_by_id = {r["rule_id"]: r for r in old_store["rules"]}

    new_rules = []
    for cr in canonical:
        rid = cr["rule_id"]
        entry = {
            "rule_id": rid,
            "citation": cr["citation"],
            "quote": cr["quote"],
            "canonical_params": cr["params"],
            "human_verification": cr["human_verification"],
            "_caddy_rule_name": cr.get("_caddy_rule_name"),
            "_caddy_source_url": cr.get("_caddy_source_url"),
        }
        if rid in MULTI_DISTRICT:
            entry["districts"] = MULTI_DISTRICT[rid]
        else:
            entry["district"] = cr["district"]

        if rid in old_by_id:
            old = old_by_id[rid]
            entry["evaluator"] = old["evaluator"]
            entry["params"] = old["params"]
            # Carry verified sweep provenance forward (Caddy's human-verified
            # code-wide absence sweep, 2026-09-23) — it is evidence, not store
            # formatting, and must not be dropped by the migration.
            if "broadened_by_sweep" in old:
                entry["broadened_by_sweep"] = old["broadened_by_sweep"]
        elif rid in EXTRA_EXECUTABLE:
            evaluator, params = EXTRA_EXECUTABLE[rid]
            entry["evaluator"] = evaluator
            entry["params"] = params
        # else: no evaluator -> engine yields UNKNOWN (documented above)
        new_rules.append(entry)

    new_store = {
        "edition": "2026 S-21",
        "store": "caddy_canonical_store_view (adapted for RuleGraph execution)",
        "version": "2026-09-24",
        "rules": new_rules,
    }

    if not os.path.exists(ARCHIVE):
        shutil.copy2(OLD_STORE, ARCHIVE)
        print(f"archived old 10-rule store -> {ARCHIVE}")
    with open(OLD_STORE, "w", encoding="utf-8") as fh:
        json.dump(new_store, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    n_exec = sum(1 for r in new_rules if "evaluator" in r)
    print(f"wrote {len(new_rules)}-rule canonical store -> {OLD_STORE}")
    print(f"executable: {n_exec}; stored-but-not-executable: {len(new_rules) - n_exec}")


if __name__ == "__main__":
    main()
