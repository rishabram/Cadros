## Deep-dive narrative — archetype: awkward geometry

> **Machine-generated narrative (machine-draft — not human-verified).** Every
> figure below is copied from this parcel's `report.json`, from
> `screening_results.csv`, and from the parcel GeoJSON in
> `screen/real_parcels/`; no new facts, no verdicts, no recommendations.

**Why this parcel — selection documented:** the task called for a parcel with
schemes but irregular geometry or a marginal clean rate. Querying
`screening_results.csv` for `geometry_clean = false` on at least one scheme
returned 8 parcels; among the profitable ones, parcel `08253760610000` has
the most elongated footprint — a **3.86:1 bounding-box aspect ratio**
(computed from `screen/real_parcels/parcel_08253760610000.geojson`) — and a
**marginal clean rate of 4/5 schemes**.

- Parcel `08253760610000` — Light Manufacturing (**M-1**), **6.72 acres**.
- The pipeline drew **5 schemes**. Top-ranked scheme `scheme_00`: **6 lots**,
  profit **$2,321,036.25**, margin **85.96%** — and it is the **flagged** one:
  geometric validation shows R-1 (min area), R-2 (min frontage), R-3 (lots
  within parcel), R-4 (no overlap), and R-6 (6 lots vs 14.6 theoretical max)
  all pass, but **R-5 is a warning**: *"road meets parcel boundary in 1
  place(s) — stub end: verify turnaround/cul-de-sac standard."* That warning
  is what sets `clean = false`.
- The remaining four schemes (4 lots each, $1,042,390.75–$1,525,217.25
  profit) are all geometry-clean.

**The honest read:** ranking by profit alone promotes the one scheme whose
road dead-ends at the property line without a verified turnaround. On an
elongated 3.86:1 parcel, road termination and access geometry dominate what
is actually buildable — the clean 4-lot schemes are arguably the more
defensible candidates despite lower projected profit. The open item is a
single, concrete, checkable fact: does the stub end meet the applicable
turnaround/cul-de-sac standard? (Use-allowance for the proposed industrial
use is pending — the 21A.33 checker is not yet integrated.)
