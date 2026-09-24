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
