# NERON Approved-Plat Accuracy Taxonomy

**Purpose.** Every scored plat gets exactly one primary failure layer:
`ranking | geometry | inputs | parent`. The layer names the cheapest place
to fix the miss. A miss can have secondary contributors, but the taxonomy
forces one accountable layer per scored plat so fixes stay targeted.

**Failure layers (definitions).**

| Layer | Meaning | Typical fix |
|---|---|---|
| `ranking` | Generation produced a scheme at/near the approved yield, but the ranker selected a different one as top. | Change the ranking objective / prior, not the geometry. |
| `geometry` | No generated scheme reached the approved yield — the generator cannot express what the human designer built. | Change the subdivision geometry code (new lot/road strategies). |
| `inputs` | The zoning/standard inputs fed to the harness were wrong or proxied, so even a perfect generator would miss. | Fix the input sourcing (rule-pack values, quoted minimums). |
| `parent` | The parent polygon fed to the pipeline was wrong (area, boundary, membership). | Fix parent reconstruction before any geometry work. |

**Status line (2026-09-24):** scored set 2/17, 0/2 within ±15%. Aim: ≥70% within ±15% at n=10 (stretch n=20).

---

## Plat 1 — TRIPP LANE SUBDIVISION (Murray, UT)

- **plat_id:** `tripp-lane-subdivision` (Project #22-088, Murray PC)
- **Approved:** 12 lots (final 2023-04-06, 6-0) + Parcel A detention (excluded)
- **NERON top-ranked:** 9 lots — **relative error −25% (under-yield), outside ±15%**
- **Scheme envelope:** 6–9 lots (schemes: 9, 8, 7, 7, 7, 6, 6, 6). No scheme reached 12.
- **Inputs:** R-1-6 — min lot area 6,000 sqft (Murray PC minutes 2023-04-06 p.4, official),
  min frontage 60 ft (PC minutes 2022-11-17 condition 11, 60-ft lot-width requirement at the
  20-ft setback line, used as frontage proxy per policy), road width 49 ft
  (Murray Code §16.16.180, primary).
- **Parent:** deterministic concave-hull reconstruction of the pre-subdivision parent from
  13 child parcels — 2.787 ac vs official 2.78 ac (0.3% diff). **Parent layer passes.**

**Failure layer: GEOMETRY (under-yield).**

**Evidence.** The generator's entire envelope (6–9 lots) sits below the approved 12.
The parent reconciles to 0.3%, and the inputs are official-record sourced, so neither
`inputs` nor `parent` is the binding constraint. The site is a narrow cul-de-sac
extension: human designers adapted lot widths to the street geometry and used the
cul-de-sac bulb for lots that a rigid rectangular subdivision generator cannot express.
This is a generator expressiveness gap, not a selection problem — ranking had no
12-lot scheme to pick.

**Named fix.** Add narrow-parcel / cul-de-sac-aware generation strategies to
`prototype/geometry.py`: (a) bulb-lot placement around cul-de-sac turnarounds
(§16.16.180: 50-ft turnaround ROW radius is citable), (b) width-adaptive lot
tiling that relaxes uniform frontage on constrained frontages, (c) depth-first
flag/cluster strategies for parcels too narrow for two-sided street layouts.

**What evidence would confirm the fix.** Re-run the harness on the same
`tripp-lane-subdivision` parent + inputs; the scheme envelope must contain a
scheme within ±15% of 12 (i.e., 10–14 lots) while the parent and inputs are
unchanged. If the envelope reaches 12 only by changing inputs, the layer was
misclassified as `inputs` — reclassify and source the real minimums.

**Secondary notes.** min_frontage_ft=60 is a proxy (lot-width-at-setback-line),
not a quoted frontage minimum; the rule-pack still carries R-1-6 width as a gap
(see `scripts/check_benchmark_inputs.py` — cross-lane consistency warning, not a fail).

---

## Plat 2 — DAYBREAK VILLAGE 12B PLAT 1 (South Jordan, UT)

- **plat_id:** `daybreak-v12b-plat1` (PLPP202400077, South Jordan PC)
- **Approved:** 61 single-family lots + 5 park lots (preliminary 2024-08-13, 4-0;
  preliminary approval — final recording not confirmed as of 2026-09-24)
- **NERON top-ranked:** 76 lots — **relative error +24.6% (over-yield), outside ±15%**
- **Scheme envelope:** 49–76 lots (schemes: 76, 73, 64, 62, 60, 59, 57, 49).
  **Schemes at 59, 60, and 62 lots exist inside ±15% tolerance.**
- **Inputs:** P-C (planned community, Daybreak) — min frontage 30 ft (QUOTED from the
  adopted Design Guidelines Small Lot product: "Min. 30′, Max. 70″ lot frontage"),
  min lot area 1,500 sqft (DERIVED and documented: 30 ft frontage × 50 ft min depth,
  not a quoted area), road width 28 ft (South Jordan Standard Drawing S-1, official).
- **Parent:** direct pre-subdivision UGRC parcel `26221030210000` — 14.253 ac vs
  official 14.306 ac (0.37% diff). **Parent layer passes.** Parent is not retired
  (final plat not yet parcelized).

**Failure layer: RANKING (over-yield).**

**Evidence.** Generation produced schemes at 59/60/62 lots — all within ±15% of the
approved 61. The generator demonstrably expresses the right answer. The ranker
(`prototype/compare.py::rank`, sorting by −profit then −lot count) selected the
76-lot scheme because it optimizes under the most permissive Small Lot minimums
(30 ft frontage / 1,500 sqft). The human designer mixed Small / Standard / Large
products (approved lots range 2,671–10,867 sqft per the staff report); NERON
assumed every lot is the smallest legal lot. This is a selection problem, not a
generation problem — changing geometry here would be fixing the wrong layer.

**Named fix.** Replace max-yield/profit ranking with a **product-mix prior**:
rank schemes by likelihood under the observed lot-product distribution for the
jurisdiction/developer (see `benchmark/ranking_prior_design.md`). At minimum,
penalize schemes whose lot-size distribution deviates from the approved mix
(Small/Standard/Large per the Daybreak Design Guidelines).

**What evidence would confirm the fix.** Re-run the harness on the same
`daybreak-v12b-plat1` parent + inputs with the mix prior active; the top-ranked
scheme must fall within 55–70 lots (±15% of 61) **without** changing the generator.
Additionally, the fix must not regress Tripp Lane: the mix prior must not push a
geometry-bound site further under yield — re-run both plats on every ranking change.

**Secondary notes.** min_lot_area=1,500 is derived (30×50), not quoted — keep the
DERIVED label; do not let repetition promote it to a quoted fact. P-C has no
South Jordan rule-pack draft yet, so cross-lane consistency for this plat is
WARN-skip, not verified (see consistency script).

---

## Taxonomy maintenance rules

1. Every newly scored plat gets a taxonomy entry within the same commit wave.
2. One primary layer per plat. Secondary contributors go in "Secondary notes".
3. A fix is confirmed only by re-running the harness on unchanged parent + inputs
   with the layer's fix applied — the envelope/top-rank must move into tolerance.
4. Never change the generator to fix a `ranking` miss; never change the ranker to
   fix a `geometry` miss. The layer assignment exists to prevent exactly this.
5. `UNKNOWN` inputs never silently become passing inputs (see ZONING_POLICY.md).
