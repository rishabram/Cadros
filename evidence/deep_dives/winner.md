# Evidence report — parcel `08214000240000`

> **machine-draft — not human-verified output**

This report describes what the pipeline and the RuleGraph computed, quoting the verified rule store verbatim. It introduces no new verdicts and never treats an UNKNOWN as a pass.

## Deep-dive narrative — archetype: the winner

> **Machine-generated narrative (machine-draft — not human-verified).** Every
> figure below is copied from this parcel's `report.json` and from
> `screening_results.csv`; no new facts, no verdicts, no recommendations.

**Why this parcel:** it is ranked **#1 of the 500 screened parcels** by
top-scheme projected profit in `screen/outputs/real_slco_v1/screening_results.csv`.

- Parcel `08214000240000` — Light Manufacturing (**M-1**), **15.07 acres**.
  District assignment is real (spatial join of the AGRC/SLC parcel against
  zoning); dimensional minimums are **PROVISIONAL** except as human-verified.
- The pipeline drew **8 schemes, all geometry-clean**. Top scheme `scheme_00`:
  **18 lots**, 994.8 ft of new road, revenue **$8,100,000**, total cost
  **$739,497**, profit **$7,360,503**, margin **90.87%**.

**What the headline hides (read before quoting the $7.36M):**

1. **The RuleGraph "8/8 PASS" is vacuous on this parcel.** The verified store
   holds 8 rules — seven for MU-11, one for PL. Every one of them evaluated
   `applicable: false` against this M-1 parcel ("not applicable: rule district
   MU-11 != parcel district M-1"). A PASS here means *"nothing in the store to
   check against"* — **no M-1 dimensional rule has been human-verified yet**.
2. **The geometry the profit assumes is provisional.** Lots were sized against
   illustrative M-1 dimensionals (20,000 sqft / 100 ft frontage), not verified
   ordinance values.
3. **The economics are assumption-grade.** Revenue confidence is labeled
   `assumption`: "$450,000/lot interpolated from regional industrial land
   benchmarks (~$350k–$600k/acre finished); **NO Salt Lake City
   finished-industrial-lot comp located**."
4. **23 RuleGraph context attributes are UNKNOWN** (building program facts the
   pipeline never had: height, setbacks, buffers, abutments).

**What would make this real:** human-verified M-1 dimensional rules in the
store, a real finished-lot comp set for the submarket, and a building program
so the RuleGraph has something to check. Until then, $7.36M is the best
*drawable* outcome under provisional rules — not a feasibility finding.

## 0. What this means (plain-English summary)


> **Machine-generated from the numbers in this report — not a recommendation, not human-verified.** Anything the pipeline could not determine is listed in Section 5; nothing there is treated as a pass.

- This parcel (`08214000240000`) covers **15.07 acres** in the **M-1** district. Zoning district assignment comes from the real parcel/zoning spatial join; dimensional minimums used for screening are **PROVISIONAL** unless the rule is human-verified (see Section 3).
- The pipeline drew **8 subdivision scheme(s)** (8 geometry-clean, 0 flagged). The top-ranked scheme, `scheme_00`, lays out **18 lots** with 994.8 ft of new road and projects **$7,360,503 profit** at **90.9% margin**.
- RuleGraph check: **8 scheme(s) PASS, 0 FAIL, 0 UNKNOWN** across the 8 rule(s) in the verified store.
  - **None of the store's rules apply to the M-1 district** (the 8 verified rules cover MU-11 and PL only), so every PASS above means 'nothing in the store to check against' — not 'compliant'. No in-district dimensional rule has been human-verified yet.
- Still unknown: **23 RuleGraph context attributes** could not be determined from the pipeline inputs (e.g. `lot_abuts_sf_tf_residential`, `landscape_buffer_provided`, `building_form`, `stories`, `height_ft`, `design_review_completed`). Resolving them needs real site/building facts — see Section 5 for each one.
- Economics confidence: **assumption**. Dollar figures rest on assumption-grade inputs (Section 4), not appraised comps or contractor pricing.
- Bottom line: the profit numbers are a geometry-and-assumption sketch. Compliance against M-1 rules has not been checked at all — no in-district rules exist in the verified store yet.

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


> 'clean' reflects geometric validation only. RuleGraph verdicts are reported separately; a scheme is compliance-confirmed only when its rulegraph verdict is PASS. 

| rank | scheme | lots | road ft | revenue | total cost | profit | margin | geometry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `scheme_00` | 18 | 995 | $8,100,000 | $739,497 | $7,360,503 | 90.9% | clean |
| 2 | `scheme_01` | 16 | 995 | $7,200,000 | $739,497 | $6,460,503 | 89.7% | clean |
| 3 | `scheme_02` | 14 | 1,153 | $6,300,000 | $830,858 | $5,469,142 | 86.8% | clean |
| 4 | `scheme_03` | 13 | 864 | $5,850,000 | $663,960 | $5,186,040 | 88.6% | clean |
| 5 | `scheme_04` | 12 | 659 | $5,400,000 | $545,804 | $4,854,196 | 89.9% | clean |
| 6 | `scheme_05` | 12 | 760 | $5,400,000 | $604,189 | $4,795,811 | 88.8% | clean |
| 7 | `scheme_06` | 11 | 760 | $4,950,000 | $604,189 | $4,345,811 | 87.8% | clean |
| 8 | `scheme_07` | 11 | 862 | $4,950,000 | $662,978 | $4,287,022 | 86.6% | clean |

Note: geometry `clean` reflects geometric validation only (lots inside parcel, no overlaps, min area/frontage). A `clean` scheme is NOT compliance-confirmed — see Section 3 rule verdicts.

## 3. Per-scheme RuleGraph verdicts


> **How to read this:** each rule shows its verdict for this scheme, followed by the rule's verbatim evidence from the verified store. **⚠ UNKNOWN** verdicts are listed first and are never treated as passes.

### Scheme `scheme_00` — rulegraph verdict: **PASS**

### `PL-04` — Landscape buffer abutting single/two-family residential — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district PL != parcel district M-1

**Claim:** When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers per Chapter 21A.48 are required.

**Verbatim source quote (from store):**

> G. Landscape Buffers: When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers, in accordance with the requirements of Chapter 21A.48, shall be required.

- Citation: section `21A.32.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-05` — Row house uses per story — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Row house: residential on all stories; live/work units permitted on the ground level only.

**Verbatim source quote (from store):**

> Uses Per Story | Residential on all stories; live/work units permitted on the ground level. (Table C.1, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"allowed_ground_uses": ["residential", "live_work"], "allowed_non_ground_uses": ["residential"], "applies_to_forms": ["row_house"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-06` — Maximum height; design review threshold — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Maximum 125 feet. Buildings in excess of 85 feet require design review per Chapter 21A.59.

**Verbatim source quote (from store):**

> Height | Maximum: 125 feet. Design Review: Buildings in excess of 85 feet require design review in accordance with Chapter 21A.59. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"bonus": {"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}, "design_review_threshold_ft": 85, "max_ft": 125}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-07` — Additional height to 150 ft in bonus areas — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Up to 150 ft in two bounded areas via Chapter 21A.59 design review, subject to >=10% ground-level open space with outdoor active space AND (100% enhanced active use per 21A.37.050.A.2 OR a midblock walkway >=20 ft wide).

**Verbatim source quote (from store):**

> Additional Height | Properties bounded by (1) 400 South to the I-15 West Temple Off-ramp and 300 West to I-15, or (2) McClelland Street along the eastern boundary of Fairmont Park to 1300 East and 2100 South to I-80, may be allowed up to 150 feet in height through the design review process of Chapter 21A.59, subject to: 1. At least 10% of the lot shall be open space area at the ground level with an outdoor active space... 2. The development includes at least one of: 100% enhanced active use within the required ground floor use area or a midblock walkway at least 20 feet wide. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: Bonus-area membership (in_height_bonus_area) must be determined geometrically against the two bounded areas; v1 takes it as a supplied fact.
- Params: `{"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-08` — Front and corner side yard setbacks — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none, except 5 ft on North Temple and 10 ft on 300 West, 400 South, 1700 South (West Temple to I-15), 2100 South (West Temple to I-15). Maximum: 20 ft.

**Verbatim source quote (from store):**

> Front and Corner Side Yard Setback | Minimum: None, except as listed below: 1. 5 feet on North Temple. 2. 10 feet, on the following streets: a. 300 West b. 400 South c. 1700 South, from West Temple to I-15 d. 2100 South, from West Temple to I-15. Maximum: 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: 1700 South and 2100 South minima apply only on the West Temple to I-15 segments; v1 requires the segment flag (front_street_within_listed_segment) and returns UNKNOWN when the street is segment-limited but the segment is unknown and the setback is below 10 ft.
- Params: `{"max_ft": 20, "min_10_streets": ["300 West", "400 South"], "min_10_streets_segment_limited": ["1700 South", "2100 South"], "min_5_streets": ["North Temple"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-09` — Interior side yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 ft.

**Verbatim source quote (from store):**

> Interior Side Yard | Minimum: None. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 10, "abuts_attr": "interior_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "interior_side_setback_ft", "yard": "interior_side", "yard_label": "interior side"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-10` — Rear yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 ft.

**Verbatim source quote (from store):**

> Rear Yard | Minimum: None. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 20, "abuts_attr": "rear_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "rear_setback_ft", "yard": "rear", "yard_label": "rear"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-11` — No minimum lot area or width (district sections) — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** No minimum lot area or minimum lot width is stated in 21A.25.070 or in the MU general provisions (21A.25.010).

**Verbatim source quote (from store):**

> Absence confirmed across the full text of 21A.25.070 (no minimum-lot-area or minimum-lot-width row) and 21A.25.010 (no minimum lot area or width for MU districts).

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: NARROW: absence verified only within the MU district sections. Title 20 subdivision ordinances have not been checked; a future SUBDIVISION rule may impose a minimum. Do not treat this as a universal legal conclusion.

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`


### Scheme `scheme_01` — rulegraph verdict: **PASS**

### `PL-04` — Landscape buffer abutting single/two-family residential — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district PL != parcel district M-1

**Claim:** When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers per Chapter 21A.48 are required.

**Verbatim source quote (from store):**

> G. Landscape Buffers: When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers, in accordance with the requirements of Chapter 21A.48, shall be required.

- Citation: section `21A.32.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-05` — Row house uses per story — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Row house: residential on all stories; live/work units permitted on the ground level only.

**Verbatim source quote (from store):**

> Uses Per Story | Residential on all stories; live/work units permitted on the ground level. (Table C.1, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"allowed_ground_uses": ["residential", "live_work"], "allowed_non_ground_uses": ["residential"], "applies_to_forms": ["row_house"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-06` — Maximum height; design review threshold — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Maximum 125 feet. Buildings in excess of 85 feet require design review per Chapter 21A.59.

**Verbatim source quote (from store):**

> Height | Maximum: 125 feet. Design Review: Buildings in excess of 85 feet require design review in accordance with Chapter 21A.59. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"bonus": {"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}, "design_review_threshold_ft": 85, "max_ft": 125}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-07` — Additional height to 150 ft in bonus areas — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Up to 150 ft in two bounded areas via Chapter 21A.59 design review, subject to >=10% ground-level open space with outdoor active space AND (100% enhanced active use per 21A.37.050.A.2 OR a midblock walkway >=20 ft wide).

**Verbatim source quote (from store):**

> Additional Height | Properties bounded by (1) 400 South to the I-15 West Temple Off-ramp and 300 West to I-15, or (2) McClelland Street along the eastern boundary of Fairmont Park to 1300 East and 2100 South to I-80, may be allowed up to 150 feet in height through the design review process of Chapter 21A.59, subject to: 1. At least 10% of the lot shall be open space area at the ground level with an outdoor active space... 2. The development includes at least one of: 100% enhanced active use within the required ground floor use area or a midblock walkway at least 20 feet wide. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: Bonus-area membership (in_height_bonus_area) must be determined geometrically against the two bounded areas; v1 takes it as a supplied fact.
- Params: `{"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-08` — Front and corner side yard setbacks — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none, except 5 ft on North Temple and 10 ft on 300 West, 400 South, 1700 South (West Temple to I-15), 2100 South (West Temple to I-15). Maximum: 20 ft.

**Verbatim source quote (from store):**

> Front and Corner Side Yard Setback | Minimum: None, except as listed below: 1. 5 feet on North Temple. 2. 10 feet, on the following streets: a. 300 West b. 400 South c. 1700 South, from West Temple to I-15 d. 2100 South, from West Temple to I-15. Maximum: 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: 1700 South and 2100 South minima apply only on the West Temple to I-15 segments; v1 requires the segment flag (front_street_within_listed_segment) and returns UNKNOWN when the street is segment-limited but the segment is unknown and the setback is below 10 ft.
- Params: `{"max_ft": 20, "min_10_streets": ["300 West", "400 South"], "min_10_streets_segment_limited": ["1700 South", "2100 South"], "min_5_streets": ["North Temple"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-09` — Interior side yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 ft.

**Verbatim source quote (from store):**

> Interior Side Yard | Minimum: None. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 10, "abuts_attr": "interior_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "interior_side_setback_ft", "yard": "interior_side", "yard_label": "interior side"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-10` — Rear yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 ft.

**Verbatim source quote (from store):**

> Rear Yard | Minimum: None. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 20, "abuts_attr": "rear_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "rear_setback_ft", "yard": "rear", "yard_label": "rear"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-11` — No minimum lot area or width (district sections) — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** No minimum lot area or minimum lot width is stated in 21A.25.070 or in the MU general provisions (21A.25.010).

**Verbatim source quote (from store):**

> Absence confirmed across the full text of 21A.25.070 (no minimum-lot-area or minimum-lot-width row) and 21A.25.010 (no minimum lot area or width for MU districts).

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: NARROW: absence verified only within the MU district sections. Title 20 subdivision ordinances have not been checked; a future SUBDIVISION rule may impose a minimum. Do not treat this as a universal legal conclusion.

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`


### Scheme `scheme_02` — rulegraph verdict: **PASS**

### `PL-04` — Landscape buffer abutting single/two-family residential — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district PL != parcel district M-1

**Claim:** When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers per Chapter 21A.48 are required.

**Verbatim source quote (from store):**

> G. Landscape Buffers: When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers, in accordance with the requirements of Chapter 21A.48, shall be required.

- Citation: section `21A.32.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-05` — Row house uses per story — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Row house: residential on all stories; live/work units permitted on the ground level only.

**Verbatim source quote (from store):**

> Uses Per Story | Residential on all stories; live/work units permitted on the ground level. (Table C.1, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"allowed_ground_uses": ["residential", "live_work"], "allowed_non_ground_uses": ["residential"], "applies_to_forms": ["row_house"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-06` — Maximum height; design review threshold — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Maximum 125 feet. Buildings in excess of 85 feet require design review per Chapter 21A.59.

**Verbatim source quote (from store):**

> Height | Maximum: 125 feet. Design Review: Buildings in excess of 85 feet require design review in accordance with Chapter 21A.59. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"bonus": {"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}, "design_review_threshold_ft": 85, "max_ft": 125}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-07` — Additional height to 150 ft in bonus areas — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Up to 150 ft in two bounded areas via Chapter 21A.59 design review, subject to >=10% ground-level open space with outdoor active space AND (100% enhanced active use per 21A.37.050.A.2 OR a midblock walkway >=20 ft wide).

**Verbatim source quote (from store):**

> Additional Height | Properties bounded by (1) 400 South to the I-15 West Temple Off-ramp and 300 West to I-15, or (2) McClelland Street along the eastern boundary of Fairmont Park to 1300 East and 2100 South to I-80, may be allowed up to 150 feet in height through the design review process of Chapter 21A.59, subject to: 1. At least 10% of the lot shall be open space area at the ground level with an outdoor active space... 2. The development includes at least one of: 100% enhanced active use within the required ground floor use area or a midblock walkway at least 20 feet wide. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: Bonus-area membership (in_height_bonus_area) must be determined geometrically against the two bounded areas; v1 takes it as a supplied fact.
- Params: `{"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-08` — Front and corner side yard setbacks — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none, except 5 ft on North Temple and 10 ft on 300 West, 400 South, 1700 South (West Temple to I-15), 2100 South (West Temple to I-15). Maximum: 20 ft.

**Verbatim source quote (from store):**

> Front and Corner Side Yard Setback | Minimum: None, except as listed below: 1. 5 feet on North Temple. 2. 10 feet, on the following streets: a. 300 West b. 400 South c. 1700 South, from West Temple to I-15 d. 2100 South, from West Temple to I-15. Maximum: 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: 1700 South and 2100 South minima apply only on the West Temple to I-15 segments; v1 requires the segment flag (front_street_within_listed_segment) and returns UNKNOWN when the street is segment-limited but the segment is unknown and the setback is below 10 ft.
- Params: `{"max_ft": 20, "min_10_streets": ["300 West", "400 South"], "min_10_streets_segment_limited": ["1700 South", "2100 South"], "min_5_streets": ["North Temple"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-09` — Interior side yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 ft.

**Verbatim source quote (from store):**

> Interior Side Yard | Minimum: None. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 10, "abuts_attr": "interior_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "interior_side_setback_ft", "yard": "interior_side", "yard_label": "interior side"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-10` — Rear yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 ft.

**Verbatim source quote (from store):**

> Rear Yard | Minimum: None. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 20, "abuts_attr": "rear_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "rear_setback_ft", "yard": "rear", "yard_label": "rear"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-11` — No minimum lot area or width (district sections) — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** No minimum lot area or minimum lot width is stated in 21A.25.070 or in the MU general provisions (21A.25.010).

**Verbatim source quote (from store):**

> Absence confirmed across the full text of 21A.25.070 (no minimum-lot-area or minimum-lot-width row) and 21A.25.010 (no minimum lot area or width for MU districts).

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: NARROW: absence verified only within the MU district sections. Title 20 subdivision ordinances have not been checked; a future SUBDIVISION rule may impose a minimum. Do not treat this as a universal legal conclusion.

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`


### Scheme `scheme_03` — rulegraph verdict: **PASS**

### `PL-04` — Landscape buffer abutting single/two-family residential — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district PL != parcel district M-1

**Claim:** When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers per Chapter 21A.48 are required.

**Verbatim source quote (from store):**

> G. Landscape Buffers: When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers, in accordance with the requirements of Chapter 21A.48, shall be required.

- Citation: section `21A.32.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-05` — Row house uses per story — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Row house: residential on all stories; live/work units permitted on the ground level only.

**Verbatim source quote (from store):**

> Uses Per Story | Residential on all stories; live/work units permitted on the ground level. (Table C.1, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"allowed_ground_uses": ["residential", "live_work"], "allowed_non_ground_uses": ["residential"], "applies_to_forms": ["row_house"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-06` — Maximum height; design review threshold — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Maximum 125 feet. Buildings in excess of 85 feet require design review per Chapter 21A.59.

**Verbatim source quote (from store):**

> Height | Maximum: 125 feet. Design Review: Buildings in excess of 85 feet require design review in accordance with Chapter 21A.59. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"bonus": {"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}, "design_review_threshold_ft": 85, "max_ft": 125}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-07` — Additional height to 150 ft in bonus areas — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Up to 150 ft in two bounded areas via Chapter 21A.59 design review, subject to >=10% ground-level open space with outdoor active space AND (100% enhanced active use per 21A.37.050.A.2 OR a midblock walkway >=20 ft wide).

**Verbatim source quote (from store):**

> Additional Height | Properties bounded by (1) 400 South to the I-15 West Temple Off-ramp and 300 West to I-15, or (2) McClelland Street along the eastern boundary of Fairmont Park to 1300 East and 2100 South to I-80, may be allowed up to 150 feet in height through the design review process of Chapter 21A.59, subject to: 1. At least 10% of the lot shall be open space area at the ground level with an outdoor active space... 2. The development includes at least one of: 100% enhanced active use within the required ground floor use area or a midblock walkway at least 20 feet wide. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: Bonus-area membership (in_height_bonus_area) must be determined geometrically against the two bounded areas; v1 takes it as a supplied fact.
- Params: `{"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-08` — Front and corner side yard setbacks — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none, except 5 ft on North Temple and 10 ft on 300 West, 400 South, 1700 South (West Temple to I-15), 2100 South (West Temple to I-15). Maximum: 20 ft.

**Verbatim source quote (from store):**

> Front and Corner Side Yard Setback | Minimum: None, except as listed below: 1. 5 feet on North Temple. 2. 10 feet, on the following streets: a. 300 West b. 400 South c. 1700 South, from West Temple to I-15 d. 2100 South, from West Temple to I-15. Maximum: 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: 1700 South and 2100 South minima apply only on the West Temple to I-15 segments; v1 requires the segment flag (front_street_within_listed_segment) and returns UNKNOWN when the street is segment-limited but the segment is unknown and the setback is below 10 ft.
- Params: `{"max_ft": 20, "min_10_streets": ["300 West", "400 South"], "min_10_streets_segment_limited": ["1700 South", "2100 South"], "min_5_streets": ["North Temple"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-09` — Interior side yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 ft.

**Verbatim source quote (from store):**

> Interior Side Yard | Minimum: None. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 10, "abuts_attr": "interior_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "interior_side_setback_ft", "yard": "interior_side", "yard_label": "interior side"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-10` — Rear yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 ft.

**Verbatim source quote (from store):**

> Rear Yard | Minimum: None. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 20, "abuts_attr": "rear_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "rear_setback_ft", "yard": "rear", "yard_label": "rear"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-11` — No minimum lot area or width (district sections) — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** No minimum lot area or minimum lot width is stated in 21A.25.070 or in the MU general provisions (21A.25.010).

**Verbatim source quote (from store):**

> Absence confirmed across the full text of 21A.25.070 (no minimum-lot-area or minimum-lot-width row) and 21A.25.010 (no minimum lot area or width for MU districts).

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: NARROW: absence verified only within the MU district sections. Title 20 subdivision ordinances have not been checked; a future SUBDIVISION rule may impose a minimum. Do not treat this as a universal legal conclusion.

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`


### Scheme `scheme_04` — rulegraph verdict: **PASS**

### `PL-04` — Landscape buffer abutting single/two-family residential — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district PL != parcel district M-1

**Claim:** When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers per Chapter 21A.48 are required.

**Verbatim source quote (from store):**

> G. Landscape Buffers: When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers, in accordance with the requirements of Chapter 21A.48, shall be required.

- Citation: section `21A.32.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-05` — Row house uses per story — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Row house: residential on all stories; live/work units permitted on the ground level only.

**Verbatim source quote (from store):**

> Uses Per Story | Residential on all stories; live/work units permitted on the ground level. (Table C.1, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"allowed_ground_uses": ["residential", "live_work"], "allowed_non_ground_uses": ["residential"], "applies_to_forms": ["row_house"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-06` — Maximum height; design review threshold — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Maximum 125 feet. Buildings in excess of 85 feet require design review per Chapter 21A.59.

**Verbatim source quote (from store):**

> Height | Maximum: 125 feet. Design Review: Buildings in excess of 85 feet require design review in accordance with Chapter 21A.59. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"bonus": {"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}, "design_review_threshold_ft": 85, "max_ft": 125}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-07` — Additional height to 150 ft in bonus areas — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Up to 150 ft in two bounded areas via Chapter 21A.59 design review, subject to >=10% ground-level open space with outdoor active space AND (100% enhanced active use per 21A.37.050.A.2 OR a midblock walkway >=20 ft wide).

**Verbatim source quote (from store):**

> Additional Height | Properties bounded by (1) 400 South to the I-15 West Temple Off-ramp and 300 West to I-15, or (2) McClelland Street along the eastern boundary of Fairmont Park to 1300 East and 2100 South to I-80, may be allowed up to 150 feet in height through the design review process of Chapter 21A.59, subject to: 1. At least 10% of the lot shall be open space area at the ground level with an outdoor active space... 2. The development includes at least one of: 100% enhanced active use within the required ground floor use area or a midblock walkway at least 20 feet wide. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: Bonus-area membership (in_height_bonus_area) must be determined geometrically against the two bounded areas; v1 takes it as a supplied fact.
- Params: `{"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-08` — Front and corner side yard setbacks — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none, except 5 ft on North Temple and 10 ft on 300 West, 400 South, 1700 South (West Temple to I-15), 2100 South (West Temple to I-15). Maximum: 20 ft.

**Verbatim source quote (from store):**

> Front and Corner Side Yard Setback | Minimum: None, except as listed below: 1. 5 feet on North Temple. 2. 10 feet, on the following streets: a. 300 West b. 400 South c. 1700 South, from West Temple to I-15 d. 2100 South, from West Temple to I-15. Maximum: 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: 1700 South and 2100 South minima apply only on the West Temple to I-15 segments; v1 requires the segment flag (front_street_within_listed_segment) and returns UNKNOWN when the street is segment-limited but the segment is unknown and the setback is below 10 ft.
- Params: `{"max_ft": 20, "min_10_streets": ["300 West", "400 South"], "min_10_streets_segment_limited": ["1700 South", "2100 South"], "min_5_streets": ["North Temple"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-09` — Interior side yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 ft.

**Verbatim source quote (from store):**

> Interior Side Yard | Minimum: None. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 10, "abuts_attr": "interior_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "interior_side_setback_ft", "yard": "interior_side", "yard_label": "interior side"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-10` — Rear yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 ft.

**Verbatim source quote (from store):**

> Rear Yard | Minimum: None. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 20, "abuts_attr": "rear_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "rear_setback_ft", "yard": "rear", "yard_label": "rear"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-11` — No minimum lot area or width (district sections) — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** No minimum lot area or minimum lot width is stated in 21A.25.070 or in the MU general provisions (21A.25.010).

**Verbatim source quote (from store):**

> Absence confirmed across the full text of 21A.25.070 (no minimum-lot-area or minimum-lot-width row) and 21A.25.010 (no minimum lot area or width for MU districts).

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: NARROW: absence verified only within the MU district sections. Title 20 subdivision ordinances have not been checked; a future SUBDIVISION rule may impose a minimum. Do not treat this as a universal legal conclusion.

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`


### Scheme `scheme_05` — rulegraph verdict: **PASS**

### `PL-04` — Landscape buffer abutting single/two-family residential — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district PL != parcel district M-1

**Claim:** When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers per Chapter 21A.48 are required.

**Verbatim source quote (from store):**

> G. Landscape Buffers: When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers, in accordance with the requirements of Chapter 21A.48, shall be required.

- Citation: section `21A.32.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-05` — Row house uses per story — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Row house: residential on all stories; live/work units permitted on the ground level only.

**Verbatim source quote (from store):**

> Uses Per Story | Residential on all stories; live/work units permitted on the ground level. (Table C.1, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"allowed_ground_uses": ["residential", "live_work"], "allowed_non_ground_uses": ["residential"], "applies_to_forms": ["row_house"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-06` — Maximum height; design review threshold — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Maximum 125 feet. Buildings in excess of 85 feet require design review per Chapter 21A.59.

**Verbatim source quote (from store):**

> Height | Maximum: 125 feet. Design Review: Buildings in excess of 85 feet require design review in accordance with Chapter 21A.59. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"bonus": {"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}, "design_review_threshold_ft": 85, "max_ft": 125}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-07` — Additional height to 150 ft in bonus areas — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Up to 150 ft in two bounded areas via Chapter 21A.59 design review, subject to >=10% ground-level open space with outdoor active space AND (100% enhanced active use per 21A.37.050.A.2 OR a midblock walkway >=20 ft wide).

**Verbatim source quote (from store):**

> Additional Height | Properties bounded by (1) 400 South to the I-15 West Temple Off-ramp and 300 West to I-15, or (2) McClelland Street along the eastern boundary of Fairmont Park to 1300 East and 2100 South to I-80, may be allowed up to 150 feet in height through the design review process of Chapter 21A.59, subject to: 1. At least 10% of the lot shall be open space area at the ground level with an outdoor active space... 2. The development includes at least one of: 100% enhanced active use within the required ground floor use area or a midblock walkway at least 20 feet wide. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: Bonus-area membership (in_height_bonus_area) must be determined geometrically against the two bounded areas; v1 takes it as a supplied fact.
- Params: `{"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-08` — Front and corner side yard setbacks — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none, except 5 ft on North Temple and 10 ft on 300 West, 400 South, 1700 South (West Temple to I-15), 2100 South (West Temple to I-15). Maximum: 20 ft.

**Verbatim source quote (from store):**

> Front and Corner Side Yard Setback | Minimum: None, except as listed below: 1. 5 feet on North Temple. 2. 10 feet, on the following streets: a. 300 West b. 400 South c. 1700 South, from West Temple to I-15 d. 2100 South, from West Temple to I-15. Maximum: 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: 1700 South and 2100 South minima apply only on the West Temple to I-15 segments; v1 requires the segment flag (front_street_within_listed_segment) and returns UNKNOWN when the street is segment-limited but the segment is unknown and the setback is below 10 ft.
- Params: `{"max_ft": 20, "min_10_streets": ["300 West", "400 South"], "min_10_streets_segment_limited": ["1700 South", "2100 South"], "min_5_streets": ["North Temple"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-09` — Interior side yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 ft.

**Verbatim source quote (from store):**

> Interior Side Yard | Minimum: None. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 10, "abuts_attr": "interior_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "interior_side_setback_ft", "yard": "interior_side", "yard_label": "interior side"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-10` — Rear yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 ft.

**Verbatim source quote (from store):**

> Rear Yard | Minimum: None. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 20, "abuts_attr": "rear_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "rear_setback_ft", "yard": "rear", "yard_label": "rear"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-11` — No minimum lot area or width (district sections) — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** No minimum lot area or minimum lot width is stated in 21A.25.070 or in the MU general provisions (21A.25.010).

**Verbatim source quote (from store):**

> Absence confirmed across the full text of 21A.25.070 (no minimum-lot-area or minimum-lot-width row) and 21A.25.010 (no minimum lot area or width for MU districts).

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: NARROW: absence verified only within the MU district sections. Title 20 subdivision ordinances have not been checked; a future SUBDIVISION rule may impose a minimum. Do not treat this as a universal legal conclusion.

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`


### Scheme `scheme_06` — rulegraph verdict: **PASS**

### `PL-04` — Landscape buffer abutting single/two-family residential — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district PL != parcel district M-1

**Claim:** When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers per Chapter 21A.48 are required.

**Verbatim source quote (from store):**

> G. Landscape Buffers: When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers, in accordance with the requirements of Chapter 21A.48, shall be required.

- Citation: section `21A.32.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-05` — Row house uses per story — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Row house: residential on all stories; live/work units permitted on the ground level only.

**Verbatim source quote (from store):**

> Uses Per Story | Residential on all stories; live/work units permitted on the ground level. (Table C.1, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"allowed_ground_uses": ["residential", "live_work"], "allowed_non_ground_uses": ["residential"], "applies_to_forms": ["row_house"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-06` — Maximum height; design review threshold — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Maximum 125 feet. Buildings in excess of 85 feet require design review per Chapter 21A.59.

**Verbatim source quote (from store):**

> Height | Maximum: 125 feet. Design Review: Buildings in excess of 85 feet require design review in accordance with Chapter 21A.59. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"bonus": {"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}, "design_review_threshold_ft": 85, "max_ft": 125}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-07` — Additional height to 150 ft in bonus areas — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Up to 150 ft in two bounded areas via Chapter 21A.59 design review, subject to >=10% ground-level open space with outdoor active space AND (100% enhanced active use per 21A.37.050.A.2 OR a midblock walkway >=20 ft wide).

**Verbatim source quote (from store):**

> Additional Height | Properties bounded by (1) 400 South to the I-15 West Temple Off-ramp and 300 West to I-15, or (2) McClelland Street along the eastern boundary of Fairmont Park to 1300 East and 2100 South to I-80, may be allowed up to 150 feet in height through the design review process of Chapter 21A.59, subject to: 1. At least 10% of the lot shall be open space area at the ground level with an outdoor active space... 2. The development includes at least one of: 100% enhanced active use within the required ground floor use area or a midblock walkway at least 20 feet wide. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: Bonus-area membership (in_height_bonus_area) must be determined geometrically against the two bounded areas; v1 takes it as a supplied fact.
- Params: `{"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-08` — Front and corner side yard setbacks — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none, except 5 ft on North Temple and 10 ft on 300 West, 400 South, 1700 South (West Temple to I-15), 2100 South (West Temple to I-15). Maximum: 20 ft.

**Verbatim source quote (from store):**

> Front and Corner Side Yard Setback | Minimum: None, except as listed below: 1. 5 feet on North Temple. 2. 10 feet, on the following streets: a. 300 West b. 400 South c. 1700 South, from West Temple to I-15 d. 2100 South, from West Temple to I-15. Maximum: 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: 1700 South and 2100 South minima apply only on the West Temple to I-15 segments; v1 requires the segment flag (front_street_within_listed_segment) and returns UNKNOWN when the street is segment-limited but the segment is unknown and the setback is below 10 ft.
- Params: `{"max_ft": 20, "min_10_streets": ["300 West", "400 South"], "min_10_streets_segment_limited": ["1700 South", "2100 South"], "min_5_streets": ["North Temple"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-09` — Interior side yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 ft.

**Verbatim source quote (from store):**

> Interior Side Yard | Minimum: None. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 10, "abuts_attr": "interior_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "interior_side_setback_ft", "yard": "interior_side", "yard_label": "interior side"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-10` — Rear yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 ft.

**Verbatim source quote (from store):**

> Rear Yard | Minimum: None. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 20, "abuts_attr": "rear_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "rear_setback_ft", "yard": "rear", "yard_label": "rear"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-11` — No minimum lot area or width (district sections) — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** No minimum lot area or minimum lot width is stated in 21A.25.070 or in the MU general provisions (21A.25.010).

**Verbatim source quote (from store):**

> Absence confirmed across the full text of 21A.25.070 (no minimum-lot-area or minimum-lot-width row) and 21A.25.010 (no minimum lot area or width for MU districts).

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: NARROW: absence verified only within the MU district sections. Title 20 subdivision ordinances have not been checked; a future SUBDIVISION rule may impose a minimum. Do not treat this as a universal legal conclusion.

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`


### Scheme `scheme_07` — rulegraph verdict: **PASS**

### `PL-04` — Landscape buffer abutting single/two-family residential — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district PL != parcel district M-1

**Claim:** When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers per Chapter 21A.48 are required.

**Verbatim source quote (from store):**

> G. Landscape Buffers: When a lot in the PL Public Lands District abuts a lot in a single-family or two-family residential district, landscape buffers, in accordance with the requirements of Chapter 21A.48, shall be required.

- Citation: section `21A.32.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-05` — Row house uses per story — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Row house: residential on all stories; live/work units permitted on the ground level only.

**Verbatim source quote (from store):**

> Uses Per Story | Residential on all stories; live/work units permitted on the ground level. (Table C.1, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"allowed_ground_uses": ["residential", "live_work"], "allowed_non_ground_uses": ["residential"], "applies_to_forms": ["row_house"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-06` — Maximum height; design review threshold — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Maximum 125 feet. Buildings in excess of 85 feet require design review per Chapter 21A.59.

**Verbatim source quote (from store):**

> Height | Maximum: 125 feet. Design Review: Buildings in excess of 85 feet require design review in accordance with Chapter 21A.59. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"bonus": {"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}, "design_review_threshold_ft": 85, "max_ft": 125}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-07` — Additional height to 150 ft in bonus areas — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Up to 150 ft in two bounded areas via Chapter 21A.59 design review, subject to >=10% ground-level open space with outdoor active space AND (100% enhanced active use per 21A.37.050.A.2 OR a midblock walkway >=20 ft wide).

**Verbatim source quote (from store):**

> Additional Height | Properties bounded by (1) 400 South to the I-15 West Temple Off-ramp and 300 West to I-15, or (2) McClelland Street along the eastern boundary of Fairmont Park to 1300 East and 2100 South to I-80, may be allowed up to 150 feet in height through the design review process of Chapter 21A.59, subject to: 1. At least 10% of the lot shall be open space area at the ground level with an outdoor active space... 2. The development includes at least one of: 100% enhanced active use within the required ground floor use area or a midblock walkway at least 20 feet wide. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: Bonus-area membership (in_height_bonus_area) must be determined geometrically against the two bounded areas; v1 takes it as a supplied fact.
- Params: `{"base_max_ft": 125, "bonus_max_ft": 150, "open_space_min_pct": 10, "walkway_min_ft": 20}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-08` — Front and corner side yard setbacks — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none, except 5 ft on North Temple and 10 ft on 300 West, 400 South, 1700 South (West Temple to I-15), 2100 South (West Temple to I-15). Maximum: 20 ft.

**Verbatim source quote (from store):**

> Front and Corner Side Yard Setback | Minimum: None, except as listed below: 1. 5 feet on North Temple. 2. 10 feet, on the following streets: a. 300 West b. 400 South c. 1700 South, from West Temple to I-15 d. 2100 South, from West Temple to I-15. Maximum: 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: 1700 South and 2100 South minima apply only on the West Temple to I-15 segments; v1 requires the segment flag (front_street_within_listed_segment) and returns UNKNOWN when the street is segment-limited but the segment is unknown and the setback is below 10 ft.
- Params: `{"max_ft": 20, "min_10_streets": ["300 West", "400 South"], "min_10_streets_segment_limited": ["1700 South", "2100 South"], "min_5_streets": ["North Temple"]}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-09` — Interior side yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 ft.

**Verbatim source quote (from store):**

> Interior Side Yard | Minimum: None. When the interior side yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone, the minimum is 10 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 10, "abuts_attr": "interior_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "interior_side_setback_ft", "yard": "interior_side", "yard_label": "interior side"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-10` — Rear yard setback — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** Minimum: none. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 ft.

**Verbatim source quote (from store):**

> Rear Yard | Minimum: None. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, RMF-35, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 feet. (Table C.2, 21A.25.070)

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Params: `{"abut_min_ft": 20, "abuts_attr": "rear_abuts_listed_zone", "default_min_ft": 0, "listed_zones": ["R-1", "R-2", "FR", "SR", "FB-UN1", "RMF-30", "RMF-35", "MU-2", "MU-3"], "setback_attr": "rear_setback_ft", "yard": "rear", "yard_label": "rear"}`

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`

### `MU-11-11` — No minimum lot area or width (district sections) — **PASS**

- Verdict: **PASS**
- Applicable to this scheme: `False`
- Reason: not applicable: rule district MU-11 != parcel district M-1

**Claim:** No minimum lot area or minimum lot width is stated in 21A.25.070 or in the MU general provisions (21A.25.010).

**Verbatim source quote (from store):**

> Absence confirmed across the full text of 21A.25.070 (no minimum-lot-area or minimum-lot-width row) and 21A.25.010 (no minimum lot area or width for MU districts).

- Citation: section `21A.25.070` — 
- Source edition: 2026 S-21 (live, codelibrary.amlegal.com)
- Caveats: NARROW: absence verified only within the MU district sections. Title 20 subdivision ordinances have not been checked; a future SUBDIVISION rule may impose a minimum. Do not treat this as a universal legal conclusion.

**Human verification (described from store record; the report creates no verdict):** result=`VERIFIED`, verified_by=`Rishab`, verified_on=`2026-09-23`


## 4. Economics breakdown — top-ranked scheme


Top scheme: `scheme_00` (18 lots).

| Line | Amount |
| --- | --- |
| Revenue | $8,100,000 |
| — infrastructure cost | $522,270 |
| — soft costs | $150,000 |
| — contingency | $67,227 |
| **Total cost** | **$739,497** |
| **Profit** | **$7,360,503** |
| **Margin** | **90.9%** |

**Finance assumptions and their source labels:**

| Assumption | Value | Source |
| --- | --- | --- |
| `sale_price_per_lot` | 450000.0 | |
| `road_cost_per_lf` | 525.0 | |
| `soft_costs_fixed` | 150000.0 | |
| `contingency_pct` | 0.1 | |
| `road_length_ft` | 994.8 | |

- Stated source text: derived from (in-memory) (district=M-1, economics build 2026-09-23); per-value sources inside the economics file
- Label: **sourced / stated**

## 5. Gaps & unknowns — what this report does NOT know


> Nothing in this section defaults to compliance. Every attribute the RuleGraph could not determine is listed explicitly, with what would be needed to resolve it.

- Program supplied to RuleGraph: `False`
- Rules evaluated per scheme: `8`

### Context attributes that were UNKNOWN (23 total)

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

### Rule outcomes that were UNKNOWN (by scheme)

- None: no UNKNOWN rule outcomes in any scheme.

## 6. Use allowance (21A.33) — integration placeholder


Caddy's use-allowance checker output merges here by rule ID — not yet integrated. This section is intentionally empty; no use-allowance engine was built as part of this report.

#### `MU-11-05` — use allowance

_Pending: merge Caddy's 21A.33 checker output for this rule ID._

#### `MU-11-06` — use allowance

_Pending: merge Caddy's 21A.33 checker output for this rule ID._

#### `MU-11-07` — use allowance

_Pending: merge Caddy's 21A.33 checker output for this rule ID._

#### `MU-11-08` — use allowance

_Pending: merge Caddy's 21A.33 checker output for this rule ID._

#### `MU-11-09` — use allowance

_Pending: merge Caddy's 21A.33 checker output for this rule ID._

#### `MU-11-10` — use allowance

_Pending: merge Caddy's 21A.33 checker output for this rule ID._

#### `MU-11-11` — use allowance

_Pending: merge Caddy's 21A.33 checker output for this rule ID._

#### `PL-04` — use allowance

_Pending: merge Caddy's 21A.33 checker output for this rule ID._

## 7. Provenance footer


- Rule store: `rulegraph/verified_rules.json`
- Store fingerprint recorded in report.json: `7935504ac8ab417812d2ee051a6105912531a33e1f0cc169790cb80481e0c38f`
- Store fingerprint recomputed now: `7935504ac8ab417812d2ee051a6105912531a33e1f0cc169790cb80481e0c38f`
- Fingerprint check: MATCH (store unchanged since pipeline run).
- Generated (UTC): 2026-09-24 03:22:32 UTC
- **machine-draft — not human-verified output**
