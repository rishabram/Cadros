# Taylorsville Pack — Pilot Report (Pack-1, 2026-09-24)

## What was extracted

- **Chapter map**: `rulegraph/taylorsville_title13_map.md` — all 44 Title 13 chapters (13.01–13.44, 13.14 reserved) mapped from the code TOC; extraction status per chapter marked.
- **Draft overlay**: `rulegraph/taylorsville_params_draft.json` — DRAFT/UNVERIFIED, never touches `verified_rules.json` or MU overlays.
  - 13 district rows from §13.04.020 (min lot area; MH blank → gap)
  - Full §13.20.020 table for all 11 R-1/R-2 districts (front/side/rear setbacks, corner/cul-de-sac/elbow rules, height, accessory height, parking, zero-lot-line)
  - §13.20.060 RM district (density table positional, setbacks 20/8-15/15-20, height 35 max / 12 min, landscaping, screening) + R-2 §F standards
  - §13.21.100 street ROW widths (arterial 106+, collectors 80/66, local 50, local rebuild 42, private street 50 ROW/26 pavement, private lane 25/20) + cul-de-sac rules (92' turnaround, ≤400' residential)
  - §13.24.080 residential parking rows (SECONDARY source: staff report quoting the section — 2/unit SF/duplex/triplex-5plex; apartments 1.5/2.0/2.5 by bedroom + 0.25 guest)

## Sources & verification method

- American Legal HTML (primary): §13.04.020 / §13.20.020 / §13.20.060 / §13.21.100.
- Ord 24-04 Exhibit A PDF (utah.gov PMN): confirmed §13.20.020 table column order (R-1-40 … R-1-5, R-2-10, R-2-8) and the 2024 front-setback redlines; codified per the section's own history line.
- Every number cites its URL + section. Nulls with gap reasons, never fills.

## Gaps (what remains unknown)

1. **Min lot width/frontage** — not in the §13.20.020 table; may be in subdivision standards (13.21 beyond §100) — not checked.
2. **Lot coverage / max impervious** — not in pilot sections.
3. **RM density table column headers** — blank in source; sub-district names unverified (positional columns recorded).
4. **Primary §13.24.080 text** — amlegal section page not yet fetched; non-residential parking rows absent.
5. **Accessory-building setbacks** — §13.20.020 gives only accessory height.
6. **MH district min lot** — blank in §13.04.020 (likely §13.22).
7. **Non-residential** — §13.23 (commercial/office/hospital/industrial/TC/multifamily standards) not touched.
8. **Use tables** — §13.07/13.08 not extracted.
9. **Chapters 13.25–13.29, 13.37** (landscaping/signs/grading/fencing/addressing/design) not extracted.
10. **Overlays** — 13.12/13.15–13.18 not extracted; SSD districts (13.19, 13.38–13.42, 13.44) site-specific — deferred.
11. **Procedures** — 13.30–13.35, 13.43 not extracted.

## Full-pack effort estimate

- Pilot covered ~5 sections across 4 chapters in ~45 min of focused work (including column-header forensics on one table).
- Remaining Title 13 work: ~15 unextracted chapters with dimensional rules (13.07, 13.08, 13.09, 13.10, 13.11, 13.12, 13.13, 13.15–13.18, 13.22, 13.23, 13.25–13.29, 13.37) + primary fetch of §13.24.080 + use-table rows.
- Rule-volume estimate: pilot yielded ~120 numeric values from 5 sections. Full pack likely **400–700 numeric params** across **15–20 sections** — roughly **3–5 waves of this size**, or one large lane run of ~6–8 hours wall-clock with verification.
- Recommendation: next wave = §13.23 (non-residential dimensional) + §13.24.080 primary fetch + §13.07/13.08 use tables (uses-per-story analogs). After that, overlays 13.15–13.18 + 13.12.
