
# Evidence report — parcel `08223510140000`

> **machine-draft — not human-verified output**

This report describes what the pipeline, the RuleGraph, and the use-allowance engine computed, quoting the verified rule store and use-table packs verbatim. It introduces no new verdicts, grants no human verification, and never treats an UNKNOWN as a pass.

> **PROVISIONAL inputs:** the zoning dimensional minimums used for this screening are provisional except where a rule is human-verified (see Section 3). District assignment comes from the real parcel/zoning spatial join.


## 0. What this means (plain-English summary)


> **Machine-generated from the numbers in this report — not a recommendation, not human-verified.**

- This parcel (`08223510140000`) covers **0.18 acres** in the **R-1-7000** district. The pipeline drew **no subdivision schemes** for it — this is an explicit diagnostic outcome, not an omission.
- Generation diagnostic: `no_schemes__below_size_threshold`.
- Blocking reasons (24 candidate configuration(s) evaluated): `no_conforming_lots`: 3; `parcel_too_small_for_config`: 21.
- Fallback note: parcel area fits 1.1x min_lot_area (< 2.0x size threshold); no-schemes is the expected result
- Bottom line: no geometry or economics were produced because no scheme could be drawn under the screening configuration. The diagnostic above names why; nothing was skipped silently.

## 1. Parcel facts


| Fact | Value |
| --- | --- |
| parcel_id | `08223510140000` |
| status | `no_schemes_generated` |
| area | 8,019 sqft (0.18 acres) |
| CRS | `local-feet` |
| zoning district | `Single Family Residential (real AGRC/SLC parcel; dimensionals PROVISIONAL except as verified)` |
| zoning config source | PROVISIONAL dimensional assumptions for mass-screen v1. District assignment is real (spatial join, see screen/real_parcels/SOURCES.md). 7000 sqft from district name; frontage/road provisional — **sourced / stated** |
| geometry notes | 0 scheme(s): 0 geometry-clean, 0 flagged |

## 2. Scheme generation diagnostics


No schemes were drawn for this parcel. The pipeline's generation diagnostics are reproduced verbatim below — a named reason, not a gap.

| Diagnostic | Value |
| --- | --- |
| `strategy` | spine_road |
| `verdict` | no_schemes__below_size_threshold |
| `candidates_evaluated` | 24 |
| `size_threshold_ratio` | 2.0 |
| `area_min_lot_ratio` | 1.15 |
| `primary_min_lots` | 4 |
| `primary_schemes_kept` | 0 |
| `top_blocking_reason` | parcel_too_small_for_config |
| `fallback_used` | False |
| `fallback_skipped_reason` | parcel area fits 1.1x min_lot_area (< 2.0x size threshold); no-schemes is the expected result |
| `primary_blocking_reasons` | no_conforming_lots: 3; parcel_too_small_for_config: 21 |

## 3. Per-scheme RuleGraph verdicts


Skipped: no schemes were drawn, so no rules were evaluated.

## 4. Economics breakdown — top-ranked scheme


Not applicable: no schemes were drawn, so no economics were computed.

## 5. Gaps & unknowns — what this report does NOT know


> Nothing in this section defaults to compliance.

- RuleGraph was not run against any scheme (none drawn). The context attributes below were already unknown at the parcel level:

- **`lot_abuts_sf_tf_residential`** — needed from: neighbor-zone GIS overlay (abutment analysis)
- **`landscape_buffer_provided`** — needed from: building program / site plan
- **`building_form`** — needed from: building program
- **`stories`** — needed from: building program (story-by-story uses)
- **`height_ft`** — needed from: building program (proposed building height)
- **`design_review_completed`** — needed from: entitlement tracker
- **`in_height_bonus_area`** — needed from: parcel geolocation vs MU-11 bonus-area polygons
- **`open_space_ground_pct`** — needed from: site plan
- **`enhanced_active_use_100_pct`** — needed from: site plan / use program
- **`midblock_walkway_ft`** — needed from: site plan
- **`front_setback_ft`** — needed from: building footprints + parcel boundary
- **`front_street`** — needed from: street centerline names at parcel frontage
- **`front_street_within_listed_segment`** — needed from: street segment data (1700/2100 South, West Temple to I-15)
- **`corner_side_setback_ft`** — needed from: building footprints + parcel boundary
- **`corner_street`** — needed from: street centerline names at parcel corner frontage
- **`corner_street_within_listed_segment`** — needed from: street segment data (1700/2100 South, West Temple to I-15)
- **`interior_side_setback_ft`** — needed from: building footprints + parcel boundary
- **`interior_abuts_listed_zone`** — needed from: neighbor-zone GIS overlay (abutment analysis)
- **`abuts_zones_side`** — needed from: building program (abutment survey) or neighbor-zone GIS overlay: zone codes abutting the interior side
- **`rear_setback_ft`** — needed from: building footprints + parcel boundary
- **`rear_abuts_listed_zone`** — needed from: neighbor-zone GIS overlay (abutment analysis)
- **`abuts_zones_rear`** — needed from: building program (abutment survey) or neighbor-zone GIS overlay: zone codes abutting the rear
- **`is_corner_lot`** — needed from: parcel boundary + street centerline intersections (corner detection)

- Use allowance was not evaluated (no schemes, no building program). No use is treated as allowed.


## 6. Use allowance (21A.33)


Not evaluated: no schemes were drawn and no building program was supplied. Use-pack fingerprints (recorded in report.json) for reference: m1_os_pl=`5a3a06db51f04b7cefafe57ae9339b44ebdec6e4a3f7404d67687faec4fbc90e`, mu=`bf741fd283b46ee39b937e5a5ff8c04fb5d9b3a3fb7a4a577bb4e3f8eb58bd6c`.

## 7. Provenance footer


- Rule store: `rulegraph/verified_rules.json`
- Store fingerprint recorded in report.json: `9cc91ac71f5f1de221b9609291ce264ca33d6c6ba9b98f7e7f898778fd0cfd1c`
- Store fingerprint recomputed now: `9cc91ac71f5f1de221b9609291ce264ca33d6c6ba9b98f7e7f898778fd0cfd1c`
- Fingerprint check: MATCH (store unchanged since pipeline run).
- Use-pack fingerprints (recorded in report.json): m1_os_pl=`5a3a06db51f04b7cefafe57ae9339b44ebdec6e4a3f7404d67687faec4fbc90e`, mu=`bf741fd283b46ee39b937e5a5ff8c04fb5d9b3a3fb7a4a577bb4e3f8eb58bd6c`
- Source report.json fingerprint: `4b6103ff690539ed3724a7aad6ce2f0fcc335f9f71f44dffacde5234da9fc465`
- Determinism: this report is regenerated byte-identically from the same report.json + rule store (no wall-clock timestamps anywhere).
- **machine-draft — not human-verified output**
