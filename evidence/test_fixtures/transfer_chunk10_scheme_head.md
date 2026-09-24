
# Evidence report — parcel `08214000240000`

> **machine-draft — not human-verified output**

This report describes what the pipeline, the RuleGraph, and the use-allowance engine computed, quoting the verified rule store and use-table packs verbatim. It introduces no new verdicts, grants no human verification, and never treats an UNKNOWN as a pass.

> **PROVISIONAL inputs:** the zoning dimensional minimums used for this screening are provisional except where a rule is human-verified (see Section 3). District assignment comes from the real parcel/zoning spatial join.


## 0. What this means (plain-English summary)


> **Machine-generated from the numbers in this report — not a recommendation, not human-verified.** Anything the pipeline could not determine is listed in Section 5; nothing there is treated as a pass.

- This parcel (`08214000240000`) covers **15.07 acres** in the **M-1** district. Zoning district assignment comes from the real parcel/zoning spatial join; dimensional minimums used for screening are **PROVISIONAL** unless the rule is human-verified (see Section 3).
- The pipeline drew **8 subdivision scheme(s)** (8 geometry-clean, 0 flagged). The top-ranked scheme, `scheme_00`, lays out **18 lots** with 994.8 ft of new road and projects **$7,360,503 profit** at **90.9% margin**.
- RuleGraph check (scheme verdicts): **8** UNKNOWN / **0** FAIL / **0** MANUAL_REVIEW / **0** CONDITIONAL_PASS / **0** PASS — across the 59 rule(s) in the verified store.
  - 6 of the store's rules actually apply to the M-1 district on the top scheme, and **6 are UNKNOWN** (`M-1-01`, `M-1-02`, `M-1-03`, `M-1-04`, `M-1-05`, `M-1-06`). Those checks could not run — the profit figure assumes answers that do not exist yet.
- Use allowance: every scheme's use verdict is **UNKNOWN** because no building program was supplied (no proposed uses to check against the §21A.33 use-table packs). UNKNOWN is never treated as allowed — see Section 6.
- Still unknown: **23 RuleGraph context attributes** could not be determined from the pipeline inputs (e.g. `lot_abuts_sf_tf_residential`, `landscape_buffer_provided`, `building_form`, `stories`, `height_ft`, `design_review_completed`). Resolving them needs real site/building facts — see Section 5 for each one.
- Economics confidence: **assumption**. Dollar figures rest on assumption-grade inputs (Section 4), not appraised comps or contractor pricing.
- Bottom line: **no scheme on this parcel has a confirmed compliance finding.** The profit numbers are a geometry-and-assumption sketch of what is physically drawable — not evidence the project is legal.

## 1. Parcel facts


| Fact | Value |
| --- | --- |
| parcel_id | `08214000240000` |
| status | `ok` |
| area | 656,354 sqft (15.07 acres) |
| CRS | `local-feet` |
| zoning district | `Light Manufacturing (real AGRC/SLC parcel; dimensionals PROVISIONAL except as verified)` |
| zoning config source | PROVISIONAL dimensional assumptions for mass-screen v1. District assignment is real (spatial join, see screen/real_parcels/SOURCES.md). illustrative industrial; provisional — **sourced / stated** |
| geometry notes | 8 scheme(s): 8 geometry-clean, 0 flagged; new road 659.4–1,153 ft across schemes |

## 2. Scheme ranking table (geometry + economics)


> 'clean' reflects geometric validation only. RuleGraph verdicts are reported separately with a per-scheme applicable-rule count ('rulegraph_applicable_rules'). A scheme is compliance-confirmed only when its rulegraph verdict is PASS with at least one applicable verified rule. A PASS with zero applicable rules means no verified rule in the store covered the parcel's district — that is 'no applicable verified rules', not a compliance finding. 

| rank | scheme | lots | road ft | revenue | total cost | profit | margin | geometry | rg verdict | use verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `scheme_00` | 18 | 995 | $8,100,000 | $739,497 | $7,360,503 | 90.9% | clean | UNKNOWN | UNKNOWN |
| 2 | `scheme_01` | 16 | 995 | $7,200,000 | $739,497 | $6,460,503 | 89.7% | clean | UNKNOWN | UNKNOWN |
| 3 | `scheme_02` | 14 | 1,153 | $6,300,000 | $830,858 | $5,469,142 | 86.8% | clean | UNKNOWN | UNKNOWN |
| 4 | `scheme_03` | 13 | 864 | $5,850,000 | $663,960 | $5,186,040 | 88.6% | clean | UNKNOWN | UNKNOWN |
| 5 | `scheme_04` | 12 | 659 | $5,400,000 | $545,804 | $4,854,196 | 89.9% | clean | UNKNOWN | UNKNOWN |
| 6 | `scheme_05` | 12 | 760 | $5,400,000 | $604,189 | $4,795,811 | 88.8% | clean | UNKNOWN | UNKNOWN |
| 7 | `scheme_06` | 11 | 760 | $4,950,000 | $604,189 | $4,345,811 | 87.8% | clean | UNKNOWN | UNKNOWN |
| 8 | `scheme_07` | 11 | 862 | $4,950,000 | $662,978 | $4,287,022 | 86.6% | clean | UNKNOWN | UNKNOWN |

Note: geometry `clean` reflects geometric validation only (lots inside parcel, no overlaps, min area/frontage). A `clean` scheme is NOT compliance-confirmed — see Section 3 rule verdicts. `rg verdict` / `use verdict` use the canonical vocabulary (PASS / CONDITIONAL_PASS / FAIL / UNKNOWN / MANUAL_REVIEW); UNKNOWN is never treated as a pass.

## 3. Per-scheme RuleGraph verdicts


> **How to read this:** each rule shows its verdict for this scheme, followed by the rule's verbatim evidence from the verified store. **⚠ UNKNOWN** verdicts are listed first and are never treated as passes. Rules district-scoped out of this parcel are summarized, not quoted in full.

### Scheme `scheme_00` — rulegraph verdict: **UNKNOWN**

### `M-1-01` — Minimum lot area and width — **UNKNOWN** ⚠ UNKNOWN

- Verdict: **UNKNOWN** ⚠ UNKNOWN
- Applicable to this scheme: `True`
- Reason: no evaluator registered for None

**Claim:** Minimum lot area and width

**Verbatim source quote (from store):**

> 1. Minimum Lot Area: Ten thousand (10,000) square feet. 2. Minimum Lot Width: Eighty feet (80'). 3. Existing Lots: Lots legally existing as of April 12, 1995, shall be considered legal conforming lots.

- Citation: section `21A.28.020.C` — 
- District scope: `M-1`
- Source edition: 2026 S-21
- Canonical verified value: `{"unit": "square feet / feet", "value": "10,000 sqft; 80 ft width"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rohan`, verified_on=`2026-09-23`

### `M-1-02` — Minimum yard requirements — **UNKNOWN** ⚠ UNKNOWN

- Verdict: **UNKNOWN** ⚠ UNKNOWN
- Applicable to this scheme: `True`
- Reason: front setback value is unknown

**Claim:** Minimum yard requirements

**Verbatim source quote (from store):**

> 1. Front Yard: Fifteen feet (15'). 2. Corner Side Yard: Fifteen feet (15'). 3. Interior Side Yard: None required. 4. Rear Yard: None required.

- Citation: section `21A.28.020.D` — 
- District scope: `M-1`
- Source edition: 2026 S-21
- Execution params: `{"min_corner_side_ft": 15, "min_front_ft": 15, "min_interior_side_ft": 0, "min_rear_ft": 0}`
- Canonical verified value: `{"unit": "feet", "value": "Front 15; corner side 15; interior none; rear none"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rohan`, verified_on=`2026-09-23`



> [TRUNCATED BY D-WADE — 2026-09-24] This sample is cut at a section boundary at 7128 of 65073 bytes (verbatim to this point, no rewording). It carries Sections 0 (plain-English summary), 1 (parcel facts), 2 (scheme table, 8 schemes) and the first two full rule entries (M-1-01, M-1-02 with verbatim quotes). The remainder — M-1-03 onward, Sections 4-7 (economics, gaps, use allowance, provenance footer) — rides the full 500 via Drive.