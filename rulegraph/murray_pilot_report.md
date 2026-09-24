# Murray Pack — Pilot Report (Pack-4, 2026-09-24) + Wave 2 (Pack-5, 2026-09-24)

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

## Wave 2 (Pack-5, 2026-09-24) — closed Pack-4 nulls

Pack-5 fetched primary code text for the remaining R-M dimensional standards,
residential parking, and the density-bonus chapter. All values below are
**primary_code_text** (American Legal, fetched 2026-09-24) unless noted.

**R-M-10 (§17.116):**
- **Height 35 ft** (§17.116.080): maximum building height 35 ft; conditional-use height determined by Planning Commission but cannot exceed 35 ft; public/quasi-public buildings may exceed via conditional-use permit. (Ord. 13-31). Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12712
- Coverage: **still null** — §17.116.100 page (node 12716) rendered heading only with no controlling coverage text. Accessory cap (25% of rear yard) is NOT whole-lot coverage. Gap documented with 2026-09-24 date.

**R-M-15 (§17.120):**
- **Yards** (§17.120.060): front 25', side 8' each / 20' combined, street-side corner 20', rear 25', accessory 1' rear (≥6' behind main, ≥10' to adjacent dwelling, ≤25% of rear yard). Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12774
- **Height 40 ft** (§17.120.080, primary — supersedes 2021 staff-packet secondary). Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12789
- **Lot coverage 40%** (§17.120.100, primary). Same source as height.
- Width/frontage: **still null** — section not surfaced.

**R-M-20 (§17.124):**
- **Lot/density** (§17.124.040): SF 8,000 sq ft / duplex 10,000 sq ft / >2 units **17 u/acre** (round down below 0.50, up at 0.50+), bonus to **20 u/acre** via ch 17.132. Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12846
- **Yards** (§17.124.060): same 25'/8'/20'/20'/25' pattern + accessory rules. Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12851
- **Height 40 ft** (§17.124.080): max 40 ft; conditional-use height by PC but ≤40 ft; public/quasi-public may exceed via CUP. (Ord. 07-30 § 2). Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12866
- Coverage/width: **still null**.

**R-M-25 (§17.128):**
- **Lot/density** (§17.128.040): SF 8,000 sq ft / duplex 10,000 sq ft / >2 units **22 u/acre**, bonus to **25 u/acre** via ch 17.132. Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12923
- **Yards** (§17.128.060): same 25'/8'/20'/20'/25' pattern + accessory rules. Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12928
- **Height 40 ft** (§17.128.080): max 40 ft; same conditional-use/public-building provisions. (Ord. 07-30 § 2). Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12943
- Coverage/width: **still null**.

**Residential parking (Chapter 17.72):**
- **§17.72.100**: single-family **2 spaces/unit**; multifamily **2.5 spaces/unit** (2 designated stalls + 0.5 pooled visitor; ≥1 covered stall/unit). PC may require additional RV parking. Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-11412
- Scope caveat: MCCD uses its own Table D — do not apply citywide.

**Density bonus (Chapter 17.132):**
- **§17.132.050 full criteria table** (primary): 1/2/3 u/acre bonus tiers. Affordable housing: 20% @ 80% AMI (25 yrs) / 20% @ 60% AMI (25 yrs) / 20% @ 60% AMI (50 yrs). Urban design: 50%/75%/100% of perimeter buildings limited to adjacent height; setbacks ≥ surrounding. Landscaping: 30%/35%/40% of site; tree density increases. Structure design, parking, and building materials escalate per tier. Full text in JSON. Source: https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-12993

**R-1 primary — NOT found:**
- Indexed search did not surface primary §17.96/17.100/17.104/17.108/17.112 section text. R-1-8 lot (8,000) and height (35') remain **secondary_official_document** (2021 PC packet). Gap explicitly dated 2026-09-24. amlegal chapter pages render sections client-side; a JS-capable crawl is the recommended next step.

**Amendment watch (unchanged):**
- June 2025 proposed setback amendments (chapters 17.92–17.128) remain **unconfirmed/unadopted** as of 2026-09-24. Current §17.116.060/§17.120.060 histories show no 2025 setback amendment. Do not treat proposed text as adopted.

## Files changed

- `rulegraph/murray_params_draft.json` (Pack-5: R-M-10 height, R-M-15 yards/height/coverage, R-M-20 lot/yards/height, R-M-25 lot/yards/height, 17.72 parking, 17.132 bonus; JSON validates)
- `rulegraph/murray_title16_map.md` (Pack-5: updated chapter status table)
- `rulegraph/murray_pilot_report.md` (Pack-5: this Wave 2 section)

Canonical `verified_rules.json` and MU overlays untouched.
