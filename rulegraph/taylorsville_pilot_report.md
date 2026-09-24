# Taylorsville Pack — Pilot Report (Pack-1, 2026-09-24)

## Pack-2 gap closure (2026-09-24)

Closed 5 of Pack-1's 7 assigned gaps (2 closed fully, 3 closed partially; the remainder stay null with explicit reasons after a bounded search):

1. **MH minimum lot size — CLOSED.** §13.20.070: *no* minimum area per lot (C), *no* minimum lot width (M); manufactured-home *subdivisions* need ≥5 acres total development (B); *manufactured-home parks* (ch. 13.22, distinct from the MH district) need ≥10-acre site + ≥25 spaces before first occupancy (§13.22.020/030). Also extracted: MH setbacks (5' front, 7'6"/15' total side, 3' accessory side/rear, 10' corner street side, 10' rear separation), 75% max lot coverage (L), 25'/12' height limits (G). Sources: https://codelibrary.amlegal.com/codes/taylorsvilleut/latest/taylorsville_ut/0-0-0-7714 , https://codelibrary.amlegal.com/codes/taylorsvilleut/latest/taylorsville_ut/0-0-0-7979 , https://codelibrary.amlegal.com/codes/taylorsvilleut/latest/taylorsville_ut/0-0-0-7987.
2. **Accessory-building setbacks — PARTIAL.** MH = 3' side/rear (§13.20.070 E/F); RM/RM-S/R-2 = up to 3' from property line (§13.20.060). General R-1 accessory setback not found after bounded sweep — null with reason (§13.20.020 gives accessory *height* only; note 4 is a fire-code rule, not a setback).
3. **RM density-table column headers — PARTIAL.** §13.07.010 lists current RM districts RM-6, RM-8, RM-10, RM-12, RM-16, RM-S (https://codelibrary.amlegal.com/codes/taylorsvilleut/latest/taylorsville_ut/0-0-0-5686) — columns 2–7 assigned by name-density match. Column 1 (4 u/acre) label unverified; no RM-4 in §13.07.010 — do not infer.
4. **§13.24.080 residential parking — PARTIAL (strengthened).** Rows now backed by Nov 2024 PC staff report Exhibit A (File 8Z24-DCA-000496-2024) quoting current code text + Ord 24-05 (SB-13 school/microeducation amendments, https://www.utah.gov/pmn/files/1159289.pdf). Added: ≥1.5 covered spaces/unit note, assisted-living/nursing 0.5/bed + bus stall, senior housing 1/unit, unlisted-use rule (§13.24.080(A)). Still secondary (amlegal section page not fetched); non-residential rows absent.
5. **Scoped §13.23 non-residential — PARTIAL.** §13.23.090 trash enclosures extracted: masonry ≥6' high; 5' side/rear commercial lines; 10' side/rear adjacent residential. Main §13.23 dimensional table not located after bounded search.
6. **R-1/R-2 lot width/frontage — REMAINS NULL.** Not in §13.20.020 table; §13.21.100 covers streets only; no Taylorsville lot-width/frontage standard located after bounded search (12+ searches, 4 page fetches). Explicit absence recorded, not a default.
7. **Lot-coverage maximums (R-1/R-2) — REMAINS NULL.** No R-1/R-2 lot-coverage maximum found in Title 13 sweep. (MH capped at 75%.)

## What was extracted (Pack-1)

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

## Gaps (Pack-1 original list; status as of Pack-2)

1. **Min lot width/frontage** — REMAINS UNKNOWN after Pack-2 bounded sweep (was: "may be in 13.21 — not checked"; now checked — absent).
2. **Lot coverage / max impervious** — REMAINS UNKNOWN for R-1/R-2 after Pack-2 sweep; MH = 75% (new).
3. **RM density table column headers** — PARTIAL after Pack-2: columns 2–7 named per §13.07.010; column 1 unverified.
4. **Primary §13.24.080 text** — PARTIAL after Pack-2: residential rows backed by two official city docs quoting current text; amlegal section page still not fetched; non-residential rows absent.
5. **Accessory-building setbacks** — PARTIAL after Pack-2: MH + RM/RM-S/R-2 closed; general R-1 unknown.
6. **MH district min lot** — CLOSED by Pack-2 (no per-lot minimum; 5-acre subdivision minimum; 10-acre park minimum).
7. **Non-residential** — PARTIAL after Pack-2: §13.23.090 trash enclosures extracted; main §13.23 dimensional table still not located.
8. **Use tables** — §13.07/13.08 not extracted (unchanged).
9. **Chapters 13.25–13.29, 13.37** (landscaping/signs/grading/fencing/addressing/design) not extracted (unchanged).
10. **Overlays** — 13.12/13.15–13.18 not extracted; SSD districts (13.19, 13.38–13.42, 13.44) site-specific — deferred (unchanged).
11. **Procedures** — 13.30–13.35, 13.43 not extracted (unchanged).

## Full-pack effort estimate

- Pilot covered ~5 sections across 4 chapters in ~45 min of focused work (including column-header forensics on one table).
- Remaining Title 13 work: ~15 unextracted chapters with dimensional rules (13.07, 13.08, 13.09, 13.10, 13.11, 13.12, 13.13, 13.15–13.18, 13.22, 13.23, 13.25–13.29, 13.37) + primary fetch of §13.24.080 + use-table rows.
- Rule-volume estimate: pilot yielded ~120 numeric values from 5 sections. Full pack likely **400–700 numeric params** across **15–20 sections** — roughly **3–5 waves of this size**, or one large lane run of ~6–8 hours wall-clock with verification.
- Recommendation: next wave = §13.23 (non-residential dimensional) + §13.24.080 primary fetch + §13.07/13.08 use tables (uses-per-story analogs). After that, overlays 13.15–13.18 + 13.12.

## Pack-3 (Wave 2) — 2026-09-24: gap-closure results

**Closed / materially advanced:**

1. **RM density column 1 → RM-4 (PROVISIONAL).** Was: unnamed, "do not infer RM-4". Now: assigned RM-4 as a draft inference on two independent legs — (a) the RM-N = N u/acre naming correspondence is exact for all six code-listed columns, and (b) RM-4 appears as an applied district label on official City zoning maps in 7 Planning Commission staff reports spanning 2022-01-14 to 2025-06-02. Honest caveat recorded in-file: current §13.07.010 text (fetched primary, amlegal 0-0-0-5686) lists only RM-6/8/10/12/16/S — the code text and the zoning map disagree, so this stays PROVISIONAL until a code-text source confirms RM-4.
2. **R-1/R-2 lot width/frontage → EVIDENCED ABSENCE.** Fetched the primary §13.04.020 page (amlegal 0-0-0-5538): the district table has a minimum-lot-size column only — no width column exists. Combined with the full §13.20.020 table read (no width/frontage rows) and §13.21.210 (frontage required on dedicated/improved street, no numeric value), the file now records that Taylorsville's code states no numeric R-1/R-2 lot-width or frontage minimum, rather than "not found yet".
3. **R-1/R-2 lot coverage → EVIDENCED ABSENCE.** Full §13.20.020 table (primary page) contains no coverage row. MH remains 75% per §13.20.070(L).
4. **§13.23.070 screening wall — NEW.** Captured from the Jan 2022 PC staff report for File #48C21 (quoting code text, Ord. 18-07): opaque masonry wall 6–8 ft where commercial/industrial abuts residential. Secondary source; recorded as such.
5. **RM-16 blank column explained.** Ord. 20-12 (April 2020) added the 16-u/acre tier per council minutes; the codified table's value cells were left blank. Recorded in the density-table gap note.

**Strengthened but still open:**

6. **R-1 accessory setback.** No codified standard located (bounded ch-13.24 search added). New secondary context: Oct 2024 PC minutes paraphrase staff that detached residential structures need "minimum 5 feet from the property line" (no section cited) — recorded as context, not a standard; consistent with §13.20.020 note 4's 5-ft fire-wall threshold.
7. **Primary §13.24.080 page.** Still not indexed on amlegal after additional bounded searches. Residential rows remain backed by two official-city secondary sources (Nov 2024 PC staff report Exhibit A quoting current text; Ord 24-05 for school/microeducation rows).

**Not attempted this wave (unchanged):** use tables §13.07/13.08, chapters 13.25–13.29/13.37, overlays, procedures, non-residential §13.24.080 rows, main §13.23 dimensional table (alternate angles exhausted for now: site-plan staff reports yielded §13.23.070/13.23.240(B) references but no dimensional table).

**Files changed:** `rulegraph/taylorsville_params_draft.json` (single-line format preserved; JSON parses), `rulegraph/taylorsville_title13_map.md`, `rulegraph/taylorsville_pilot_report.md`. Canonical `verified_rules.json` and MU overlays untouched.
