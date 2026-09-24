## Deep-dive narrative — archetype: manual review (UNKNOWNs)

> **Machine-generated narrative (machine-draft — not human-verified).** Every
> figure below is copied from this parcel's `report.json` and from
> `screening_results.csv`; no new facts, no verdicts, no recommendations.

**Why this parcel:** it is the **only parcel in the 500-parcel screen with
UNKNOWN RuleGraph verdicts** — 48 UNKNOWN rule outcomes in total (8 schemes ×
6 rules each). Scheme-level verdicts: **0 PASS, 0 FAIL, 8 UNKNOWN**. This is
the parcel the machine correctly refused to decide.

- Parcel `08253290080000` — Mixed Use 11 (**MU-11**), **2.32 acres**. Top
  scheme `scheme_00`: **11 lots**, profit **$1,294,078.50**, margin **78.43%**
  — attractive on paper, undecidable on evidence.

**Exactly which rules are UNKNOWN, and what would resolve each:**

The 8 verified rules evaluated per scheme: `PL-04` is not applicable
(wrong district); **`MU-11-11` PASSES** (no minimum lot area/width in the MU
district sections — caveat: the Title 20 subdivision-ordinance sweep is
still pending, so the absence claim is narrow). The six UNKNOWNs are all
*applicable* MU-11 rules whose context attributes the pipeline never had:

| Rule (human-verified; quotes in §3) | What it checks | Why UNKNOWN | Evidence that would resolve it |
|---|---|---|---|
| `MU-11-05` — Row house uses per story | Residential on all stories; live/work ground level only | `building_form` unknown | Building program: is the product row house / live-work, story by story |
| `MU-11-06` — Max height 125 ft; design review > 85 ft | Height cap + 21A.59 design-review trigger | `height_ft` unknown | Proposed building height in feet; whether design review is pursued |
| `MU-11-07` — Bonus height to 150 ft | Bonus-area height via design review + open-space/active-use conditions | `height_ft`, `in_height_bonus_area`, `open_space_ground_pct` unknown | Height; parcel location vs MU-11 bonus-area polygons; site plan open-space % |
| `MU-11-08` — Front/corner side setbacks | Min none, except 5 ft North Temple / 10 ft on listed segments; max 20 ft | `front_setback_ft`, `front_street` unknown | Building footprints + parcel boundary; street centerline names at frontage |
| `MU-11-09` — Interior side setback | 10 ft min when abutting listed residential/mixed zones, else none | `interior_side_setback_ft`, abutment zones unknown | Footprints + boundary; **neighbor-zone GIS overlay** (abutment analysis) |
| `MU-11-10` — Rear setback | 20 ft min when abutting listed zones along rear lot line, else none | `rear_setback_ft`, abutment zones unknown | Footprints + boundary; **neighbor-zone GIS overlay** (abutment analysis) |

Two evidence bundles unlock all six: **(1) a building/site program** (form,
height, setbacks, open space) and **(2) a neighbor-zone abutment overlay**
(GIS: which zone codes touch the side and rear lot lines). Both are listed
per-attribute with their needed sources in §5.

**What a reviewer should do:** do not rank this parcel against PASS-verdict
parcels — it is in a different epistemic category. The $1,294,078.50 is a
geometry sketch awaiting six checkable facts; any one of the six could fail a
scheme outright (notably height and abutment-triggered setbacks). Economics
are assumption-grade ("lot-share math + SLC central-city premium; **no SLC
finished-lot comp pulled**"), and use-allowance under 21A.33 is pending
integration.
