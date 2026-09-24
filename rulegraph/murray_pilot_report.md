# Murray Pack — Pilot Report (Pack-4, 2026-09-24)

## Structural finding: Murray splits subdivision and zoning across two titles

Unlike Taylorsville (all land-use rules centralized in Title 13), Murray's code
puts **subdivision regulations in Title 16** and **zoning district dimensional
rules in Title 17** (chapters 17.96–17.128). Title 16 contains no zoning
dimensional tables. The pilot therefore maps Title 16 (subdivision/design) and
extracts residential zoning parameters from Title 17. Both titles are needed for
a full Murray pack.

## What was extracted (Pack-4)

- **Chapter map**: `rulegraph/murray_title16_map.md` — Title 16 ch-16.16
  sections (12 observed incl. 1 repealed), Title 17 residential chapter list
  (17.96–17.140) from the official TOC, extraction status per chapter.
- **Draft overlay**: `rulegraph/murray_params_draft.json` — DRAFT/UNVERIFIED,
  never touches `verified_rules.json` or MU overlays. 15 top-level keys.

**Subdivision (Title 16, primary code text):**
- §16.16.180 — streets: **49 ft** minimum street width; **25 ft** asphalted
  width; permanent cul-de-sac max length **1,000 ft**; permanent turnaround
  ROW radius **50 ft**; temporary stub street **over 100 ft** requires a
  turnaround on one temporary lot; stub street **under 100 ft** requires no
  temporary cul-de-sac. Source:
  https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-9269
- §16.16.090 — access: single-/two-family subdivision lots must abut a public
  street improved to chapter standards; private-street plans require engineer
  review (alignment, width, grades, materials, drainage, utilities, ownership,
  maintenance). Source:
  https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-9186

**Residential zoning (Title 17):**
- **R-M-10 (§17.116, primary):** min lot — SF 8,000 sq ft / duplex 10,000 sq
  ft / >2 units 7 u/acre (round down below 0.50, up at 0.50+), bonus to 10
  u/acre via ch 17.132 (§17.116.040); yards — front 25', side 8' each / 20'
  combined, street-side corner 20', rear 25', accessory 1' rear (≥6' behind
  main; ≥10' to adjacent dwelling; ≤25% of rear yard) (§17.116.060). Sources:
  https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12679 ,
  https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12697
- **R-M-15 (§17.120.040, primary):** min lot — SF 8,000 sq ft / duplex 10,000
  sq ft / >2 units 12 u/acre, bonus to 15 u/acre via ch 17.132. Source:
  https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12769
- **R-1-8 / R-M-15 (secondary, official city staff packet):** R-1-8 min lot
  8,000 sq ft + max main-dwelling height 35 ft; R-M-15 max height 40 ft
  (corroborates §17.120.040 lot-area figures). Source (official Murray City
  2021-03-04 PC packet):
  https://www.murray.utah.gov/DocumentCenter/View/11743/030421-Planning-Commission-Packet?bidId=
  — labeled `secondary_official_document` in the JSON; controlling code
  sections not yet fetched.

## Sources & verification method

- American Legal HTML (primary): §§16.16.180 / 16.16.090 / 17.116.040 /
  17.116.060 / 17.120.040; ch-16.16 index; Title 17 TOC.
- Murray City Planning Commission staff packets (secondary): 2021-03-04
  (R-1-8 lot size/height, R-M-15 height); 2025-06-05 (amendment watch).
- Every number cites its URL + section. Nulls carry explicit gap reasons,
  never fills. Per-value `source_tier` fields separate primary code text from
  secondary city documents.

## Gaps (explicit)

1. **R-1-6 / R-1-10 / R-1-12 / R-2-10 / R-M-20 / R-M-25** — all dimensional
   values null. Chapter section text not surfaced by indexed official search;
   amlegal chapter TOC pages render section lists client-side, so a full
   chapter-section crawl (JS-capable fetch or section-index endpoint) is the
   needed next step. Not yet evidenced absences.
2. **R-M-10 height / lot coverage / lot width** — height section not indexed;
   no whole-lot coverage maximum located (accessory capped at 25% of rear
   yard); width/frontage section not surfaced.
3. **R-M-15 yards / coverage / width** — sections beyond §17.120.040 not
   indexed during pilot.
4. **Residential parking (ch 17.72)** — section text not surfaced; ch 17.72
   confirmed to exist (§17.72.040 ADA, §17.72.070 cross-refs). SF/duplex/
   multifamily/guest ratios unsourced. (MCCD §17.170 Table D parking captured
   as context only — MCCD-specific, not ch 17.72.)
5. **2025 amendment watch** — June 2025 PC packet shows setback amendments
   under consideration for chapters 17.92–17.128 (non-enclosed roof
   structures in setbacks); adoption status unconfirmed. Re-check yard text
   against post-2025 code before treating as current.
6. **Title 16 remainder** — full Title 16 chapter list not yet mapped; ch-16.16
   section titles/content beyond §§16.16.090/16.16.180 not extracted.
7. **ch 17.132 incentive density bonus** — referenced, requirements not
   extracted. R-M-H (17.136), R-N-B (17.140), use tables (17.84), mixed-use
   districts, procedures — not extracted.

## Value delivered beyond the JSON

- **§16.16.180's 49-ft/25-ft road standard is now closed with verbatim primary
  text** — this is the stronger codified road-width route GreenRush-6 needs for
  a scoreable Murray subdivision candidate (SLC street rules lack a single
  citable pavement-width number).
- The Title 16/Title 17 split is documented once so no future wave pretends
  Title 16 contains zoning tables.

## Full-pack effort estimate

- Pilot covered ~6 sections across 2 titles in ~1 wave. Remaining work: full
  Title 16 chapter list + ch-16.16 section texts; R-1/R-2/M chapter-section
  crawls (9 chapters); ch 17.72 parking; ch 17.132 bonus; use tables; mixed-use
  districts; 2025 amendment reconciliation.
- Rule-volume estimate: pilot yielded ~30 primary numeric values. Full Murray
  pack likely **250–450 numeric params** across **15–20 sections** — roughly
  **3–4 waves of this size**, or one lane run of ~5–6 hours wall-clock with
  verification.
- Recommendation: next wave = JS-capable crawl of Title 17 residential
  chapters (17.96–17.128) + ch 17.72 parking + ch 17.132 bonus, then 2025
  amendment reconciliation.

## Files changed

- `rulegraph/murray_params_draft.json` (new, single-line JSON, validates)
- `rulegraph/murray_title16_map.md` (new)
- `rulegraph/murray_pilot_report.md` (new)

Canonical `verified_rules.json` and MU overlays untouched.
