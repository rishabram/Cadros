# RuleGraph v1

Deterministic, human-gated zoning rule execution. Models interpret evidence;
this package owns rule evaluation — and it refuses to guess.

## The gate

A rule executes **only** when its `human_verification.result` is `VERIFIED`
or `CORRECTED`, with a named human verifier and date. Everything else —
`UNVERIFIED`, `REJECTED`, missing status — yields `UNKNOWN`. Unknown rule ids
raise `KeyError` (a code bug; loud, not silent).

## Three-valued logic

Every evaluation returns `PASS`, `FAIL`, or `UNKNOWN`:

- **PASS** — the rule's condition is established true on the supplied facts.
- **FAIL** — the rule's condition is established false.
- **UNKNOWN** — a needed fact is missing, applicability can't be determined,
  or the rule isn't verified. **UNKNOWN never becomes PASS.**

`scheme_verdict()` rolls up: any `FAIL` → `FAIL`; else any `UNKNOWN` →
`UNKNOWN`; else `PASS`.

## Layout

- `verified_rules.json` — the rule store. Each rule carries: id, district,
  section, claim, verbatim `source_quote`, `status`, `human_verification`
  (result, verified_by, verified_on, source_edition), `caveats`, `evaluator`
  name, `params` (all numeric/categorical values live here, not in code),
  and `requires` (context attributes the evaluator needs).
- `predicates.py` — the evaluators. Pure functions of `(params, context)`.
- `engine.py` — `RuleGraph`: load, gate, `evaluate`, `evaluate_all`,
  `scheme_verdict`.
- `fingerprint.py` — sha256 over the canonical rule JSON. The engine stamps
  every load; `test_rulegraph.py` pins the expected value. Any store edit
  breaks the pin until a human re-verifies and updates it deliberately.
- `test_rulegraph.py` — 77 tests: gate, district scoping, adapter, abutment
  zone lists, compliant PASS, per-rule FAIL, per-rule UNKNOWN, honest edge
  PASSes. Per-scheme program wiring is tested in
  `prototype/test_pipeline_program.py` (15 tests).
- `validate_store.py` — machine-side validator for the rule store (see
  "Store validation harness" below). Read-only with respect to verdicts:
  it checks machine-checkable facts and reports findings; humans judge.

## Context contract

The evaluator consumes facts; it never computes geometry. The caller
(pipeline, adapter, human) supplies a dict with any of:

| Attribute | Meaning |
|---|---|
| `lot_abuts_sf_tf_residential` | bool — PL lot abuts single/two-family district |
| `landscape_buffer_provided` | bool — Ch. 21A.48 buffer present |
| `building_form` | str — e.g. `row_house`, `multifamily` |
| `stories` | list of `{level, use}`; ground = lowest level; uses: `residential`, `live_work`, … |
| `height_ft` | float |
| `design_review_completed` | bool — Ch. 21A.59 review done |
| `in_height_bonus_area` | bool — inside a MU-11-07 bonus area (caller determines geometrically) |
| `open_space_ground_pct` | float |
| `enhanced_active_use_100_pct` | bool — per 21A.37.050.A.2 |
| `midblock_walkway_ft` | float |
| `front_setback_ft` / `front_street` / `front_street_within_listed_segment` | front yard facts |
| `corner_side_setback_ft` / `corner_street` / `corner_street_within_listed_segment` | corner side facts |
| `interior_side_setback_ft` / `interior_abuts_listed_zone` / `abuts_zones_side` | interior side facts; `abuts_zones_side` is a list of zone codes abutting the side (see Abutment below) |
| `rear_setback_ft` / `rear_abuts_listed_zone` / `abuts_zones_rear` | rear facts; `abuts_zones_rear` is a list of zone codes abutting the rear |
| `is_corner_lot` | bool — lot fronts two streets (corner detection; no rule consumes it yet) |

`None` (or absent) means **unknown** — never compliant-by-default.

## Abutment (MU-11-09 / MU-11-10)

The abutment minimum applies when the yard abuts one of the rule's listed
zones (R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, MU-3 — in the rule
params, not in code). Abutment is resolved in this order:

1. **Zone-code list** (`abuts_zones_side` / `abuts_zones_rear`) when present:
   the minimum applies iff a listed zone appears. An empty list is
   meaningful — the abutment survey is done and no listed zone abuts, so no
   minimum applies. A malformed (non-list) value is UNKNOWN, not evidence.
2. **Legacy boolean** (`interior_abuts_listed_zone` /
   `rear_abuts_listed_zone`) when no list is supplied.
3. **Neither** → UNKNOWN. Missing abutment info never defaults to the base
   (no-minimum) case.

A setback at or above the abutment minimum (10 ft interior, 20 ft rear)
still passes regardless of abutment — it satisfies the rule in all cases.

## Honest edges (deliberate, tested)

- MU-11-06's "Maximum: 125 feet" is qualified by MU-11-07's Additional Height
  row — they are one height regulation. A height in (125, 150] is evaluated
  against the bonus conditions inside MU-11-06 itself (shared helper with
  MU-11-07), so a compliant bonus tower passes both rules and a non-bonus
  tower fails both. Unknown bonus facts yield UNKNOWN, never a silent PASS.
- A setback ≥ 10 ft passes MU-11-08's minimum even with an unknown street,
  because 10 ft satisfies every minimum the rule contains.
- A setback ≥ the abutment minimum passes MU-11-09/10 even with unknown
  abutment, for the same reason.
- MU-11-11 (verified absence of a minimum) always passes, but carries the
  caveat: Title 20 subdivision ordinances are unchecked. A future
  `SUBDIVISION-*` rule can impose a minimum without touching this one.

## Adding a rule

1. Human verifies against the live code text; verdict recorded with name/date.
2. Append the rule JSON (claim, quote, params, requires, evaluator name).
3. Implement the evaluator in `predicates.py` — three-valued, no silent PASS.
4. Add FAIL, UNKNOWN, and edge PASS tests.
5. Update `PINNED_FINGERPRINT` in the test file to the new store hash.

## Store validation harness

`validate_store.py` validates a `verified_rules.json` file against
machine-checkable facts — no human judgment involved, and it never invents,
alters, or implies a human verdict. Usage:

```
python3 rulegraph/validate_store.py [store.json] [--zoning-dir DIR] [--corpus-glob GLOB]
```

Checks, per rule:

1. **Schema conformance** — every rule has `rule_id`, `district`, citation,
   quote, `params`, and `human_verification{result, verified_by, verified_on}`;
   `result` is one of `VERIFIED | CORRECTED | REJECTED | UNVERIFIED`. (The v1
   store uses the field names `section` / `source_quote`; the harness accepts
   these as aliases and notes each use.) It also reports whether the rule
   would pass the engine gate, derived from the recorded verdict.
2. **Citation resolvability** — every cited section (e.g. `21A.25.070`)
   appears in the retrieved code text under `~/workspace/neron-zoning/`
   (files matching `slc_code_*.md`).
3. **Quote fidelity** — the recorded quote appears verbatim in the retrieved
   text. Non-verbatim quotes are reported with the closest matching passage
   (distinctiveness-weighted token recall, section-scoped) and classified
   `MEANING-PRESERVED` (heuristic — a human must confirm the paraphrase) or
   `MISMATCH` (with a word diff). Absence claims (e.g. MU-11-11) get a
   machine-negative check instead: the cited sections are scanned for
   contradicting "minimum lot area/width/size" language
   (`ABSENCE-CONSISTENT` or `ABSENCE-CONTRADICTED`).
4. **Store fingerprint** (store-level) — recomputed with
   `fingerprint.canonical_hash` for both the full store and the
   engine-stamped `{"rules": rules}` form, and compared against the
   `PINNED_FINGERPRINT` in `test_rulegraph.py`. Duplicate `rule_id`s are also
   rejected.

Outcomes are `PASS` / `REVIEW` (needs human eyes; does not fail the run) /
`FAIL` (machine-checkable violation). Exit code is nonzero iff any check
fails.

Current 8-rule store (2026-09-23): schema PASS (with `section` /
`source_quote` alias notes), citations PASS, fingerprint MATCHES the pin.
All seven positive quotes are recorded as condensed paraphrases rather than
verbatim code text — flagged REVIEW with closest passages for human
confirmation. MU-11-11's absence claim is consistent with the cited sections
(REVIEW — absence cannot be machine-proved).

**Pending:** run this harness against the full 59-rule store once Rohan's
merge lands. No 59-rule file exists yet — do not fabricate one. At merge
time, run `python3 rulegraph/validate_store.py <merged-store.json>` and
append the findings to the shared verification channel's message log.

## District scoping

Each rule carries a `district`. If the context supplies a `district` and it
differs from the rule's, the rule evaluates to `PASS` with
`applicable: false` — a parcel is not judged by another district's code.
If the context district is unknown, the rule evaluates normally (missing
facts → UNKNOWN). The verification gate runs first: an unverified rule is
UNKNOWN even for a mismatched district.

## Pipeline integration (wired 2026-09-24)

`prototype/pipeline.py` now runs the RuleGraph over every scheme on each run:

- `rulegraph/adapter.py` — `build_context(zoning_cfg, program)` maps pipeline
  outputs onto the 24-attribute context contract. The subdivision pipeline
  produces lot/road geometry only, so without a building program nearly
  everything is `None` → UNKNOWN. Provenance records per attribute whether it
  is `known` (and from where) or `unknown` (and which upstream source would
  supply it). Unknown program keys raise `ValueError` — a typo'd program
  file is loud, not silently ignored. `summarize_gaps()` returns attributes
  unknown in every scheme: the punch list for making verdicts meaningful.
- Per scheme, `report.json` carries `rulegraph_verdict` (PASS/FAIL/UNKNOWN)
  and `rulegraph` (per-rule outcome, applicability, reason). A report-level
  `rulegraph` block adds the store fingerprint, verdict counts, gaps,
  context provenance, and the `clean` semantics note.
- `clean` is UNCHANGED: it still means geometric validation only. A scheme
  is compliance-confirmed only when its rulegraph verdict is PASS.
- Facts enter via `run.py --program <building-program.json>` (see
  `inputs/demo_program.json` — hypothetical demo values, labeled as such).
  The program applies to every scheme, but may carry a top-level `"schemes"`
  map (`{scheme_id: {attr: value, ...}}`) whose entries merge OVER the base
  program for that scheme only — e.g. per-scheme heights or setbacks. The
  `"schemes"` key is consumed by the pipeline and never reaches the adapter's
  typo guard. When a per-scheme program is used, `report.json`'s
  `rulegraph` block carries one `context_provenance` map per scheme and a
  `per_scheme_program: true` flag; without it the report shape is unchanged.
