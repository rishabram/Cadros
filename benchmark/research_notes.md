# Phase C — Plat Discovery Research Notes

Worker: **PlatScout** (subagent, Phase C plat discovery)
Date: 2026-09-24
Scope: Salt Lake County only. Discovery only — no scoring, no geometry.
Standards: `ZONING_POLICY.md` (scoring tiers: T1 = NERON verified rules, T2 = official city code,
T3 = plat-specific staff report; "unknown inputs stay gaps"), `SAMPLES.md` worked-evidence bar.

Every candidate below lists all six requested fields (plat name, `plat_pdf`, zoning, `lot_areas`,
`lot_dims` frontage, approval status), plus parent parcel ID(s), metes-and-bounds, and
entry/book/page/date when stated. Unknowns are explicit gaps — never invented.
All URLs are verbatim search-returned or fetched URLs; none were constructed or guessed.

Zoning-status mapping used: `verified` = matches a verified NERON rule with sourced dims;
`sourced` = dims sourced but not yet verified; `unknown` = no approval-date source.

---

## 1. Broadbent Business Park (Petition PLNSUB2011-00619) — STRONGEST CANDIDATE

**Status: candidate** — full free staff-report PDF with preliminary plat, approval on record,
zoning with a documented M-1 discrepancy that must be preserved, not resolved.

- **plat_pdf:** `http://www.slcdocs.com/Planning/Planning Commission/2012/April/00619.pdf`
  (Salt Lake City Planning Commission staff report, hearing April 11, 2012; report p.1 identifies
  Attachment A as the preliminary plat, located at p.13). Fetched verbatim earlier on 2026-09-24.
- **Location:** 3600–3730 W / 1987–2100 S, Salt Lake City, Salt Lake County
  (staff report p.1).
- **approval_status:** Approved — Planning Commission minutes for April 11, 2012 include the
  approval motion for the preliminary plat + planned development (minutes PDF:
  `http://www.slcdocs.com/Planning/Planning Commission/2012/April/411min.pdf`; motion reviewed
  on 2026-09-24). Agenda copy:
  `http://www.slcdocs.com/Planning/Planning Commission/2012/April/0411agn.pdf`.
- **zoning.district:** `M-1` (staff report pp.4/12; Tier 3 source).
- **zoning.status:** verified district, **but with a discrepancy**: the staff report states M-1
  minimum lot area 20,000 sqft / minimum width 80 ft (pp.4/12), while the NERON verified rule
  `M-1-01` states 10,000 sqft / 80 ft. Per policy, record both and do NOT silently resolve; PlatRunner
  should decide whether the 2012 report reflects an older code version.
- **zoning.sourced_from:** "Staff Report, Petition PLNSUB2011-00619, 2012-04-11 (Tier 3);
  district itself is Tier 1 via `M-1-01`."
- **lot_count:** 8 — "request to divide one parcel into eight parcels/lots" (report p.1); 8.5-acre site.
- **parent parcel ID(s):** `15-17-300-029` (report p.1).
- **lot_areas:** GAP — individual lot areas were not recovered. A table in the report listing
  11,136–16,252 sqft is **building area**, not lot area; do not use it as lot data.
- **lot_dims (frontage per lot):** GAP — not extracted from the plat figure text.
- **metes_and_bounds:** unknown (not observed in extracted text).
- **entry/book/page/date:** GAP — no recorder entry info recovered; not demonstrably recorded.
- **Scoring readiness:** lot geometry will come from the plat figure (Attachment A, p.13); lot areas
  and frontage must be measured from the PDF or left as gaps. Roads/road width: GAP.

---

## 2. Swaner Subdivision (PLNSUB2021-00740) — approval + zoning sourced; full plat PDF still missing

**Status: candidate (partial)** — strong approval/zone paper trail; qualifying plat-containing PDF
not yet found. Do not mark complete until one is.

- **plat_pdf:** GAP — no staff-report/preliminary-plat PDF found. Motion sheet and minutes (below)
  are evidence docs, not the plat.
- **Location:** approximately 2691 N 2200 W, Salt Lake City, Salt Lake County
  (public notice; minutes).
- **approval_status:** Approved — unanimous Planning Commission vote March 23, 2022
  (minutes PDF: `http://www.slcdocs.com/Planning/Planning%20Commission/2022/03.%20March/PC03.23.2022minutes.pdf`;
  motion sheet: `http://www.slcdocs.com/Planning/Planning%20Commission/2022/03.%20March/00740M.pdf`).
- **zoning.district:** `BP` Business Park (minutes; Tier 3).
- **zoning.status:** sourced.
- **zoning.sourced_from:** Official SLC Code, Section 21A.32.030 (Tier 2),
  `https://codelibrary.amlegal.com/codes/saltlakecityut/latest/saltlakecity_ut/0-0-0-65751`
  — BP minimum lot area 20,000 sqft, minimum lot width 100 ft (values from current-day code page
  reviewed 2026-09-24; approval-date code version should be checked before scoring).
- **lot_count:** 20 (official public notice
  `https://www.utah.gov/pmn/sitemap/notice/743374.html` and minutes; "20-lot preliminary
  subdivision", approximately 430 acres, primarily vacant).
- **parent parcel ID(s):** GAP.
- **lot_areas / lot_dims:** GAP.
- **metes_and_bounds:** unknown.
- **entry/book/page/date:** GAP.

---

## 3. TAG Row House P.U.D. / Row House P.U.D. (PLNSUB2017-00964) — staff-report bundle, decision unconfirmed

**Status: candidate (partial)** — free staff-report PDF contains plat text with a boundary
description; approval decision not yet sourced.

- **plat_pdf:** `http://www.slcdocs.com/Planning/Planning%20Commission/2018/00723.pdf`
  (Salt Lake City Planning Commission staff report; fetched/identified 2026-09-24).
- **Location:** 613 E 100 S, Salt Lake City, Salt Lake County (staff report).
- **approval_status:** staff recommends approval of preliminary subdivision (report §H Motions);
  actual Planning Commission decision: GAP.
- **zoning.district:** `RMF-45` with historic overlay (staff report; Tier 3).
- **zoning.status:** sourced (district per report; Tier 3 only).
- **lot_count:** 3 — "3-unit row house" proposal (staff report).
- **parent parcel ID(s):** `16-06-227-015` (staff report).
- **lot_areas:** GAP individually; the plat text included in the staff report states a total of
  **10,320 sqft / 0.237 acres / 3 lots**.
- **lot_dims (frontage per lot):** GAP.
- **metes_and_bounds:** yes — the included plat text contains a complete boundary description
  (per extracted staff-report text).
- **entry/book/page/date:** GAP.

---

## 4. Lincoln Street Subdivision (PLNSUB2022-00341 / PLNPCM2022-00378) — approval confirmed; staff-report/plat PDF missing

**Status: candidate (partial)** — real 2022 SLC residential approval; lot areas still unsourced.

- **plat_pdf:** GAP — motion sheet + minutes + agenda below are evidence docs, not the plat.
  - Motion sheet: `http://www.slcdocs.com/Planning/Planning%20Commission/2022/08.%20August/-00378_Motion%20Sheet.pdf`
    ("Motion to approve as proposed (Consistent with staff recommendation)", August 10, 2022).
  - Minutes: `http://www.slcdocs.com/Planning/Planning%20Commission/2022/08.%20August/PC08.10.2022minutes.pdf`
  - Agenda: `http://www.slcdocs.com/Planning/Planning%20Commission/2022/08.%20August/PC08.10.2022AMENDED2agenda.pdf`
- **Location:** approximately 1492 S Lincoln Street, Salt Lake City, Salt Lake County
  (minutes; parent area 13,939 sqft / 0.32 acres).
- **approval_status:** Approved — unanimous Planning Commission vote, August 10, 2022 (motion sheet + minutes).
- **zoning.district:** `R-1-5,000` (minutes; Tier 3). Staff report context: zone requires 50 ft
  minimum lot width; planned development reduced to 49 ft and 41 ft for the two lots.
- **zoning.status:** sourced (district per minutes/Tier 3).
- **lot_count:** 2.
- **parent parcel ID(s):** GAP.
- **lot_areas:** GAP individually; parent total 13,939 sqft (0.32 acres) per agenda/minutes.
- **lot_dims:** frontage widths **49 ft and 41 ft** (minutes); per-lot frontage assignment to Lot 1
  vs Lot 2: GAP.
- **metes_and_bounds:** unknown.
- **entry/book/page/date:** GAP.

---

## 5. 873 South 1500 West — Planned Development + Preliminary Subdivision (PLNSUB2019-00109/00110) — approval confirmed

**Status: candidate (partial)** — 2019 SLC residential approval with parcel ID and free staff report;
per-lot areas unsourced.

- **plat_pdf:** staff report:
  `http://www.slcdocs.com/Planning/Planning Commission/2019/00109.00110 SR.pdf`
  (verbatim search-returned URL; contains preliminary plat per report recommendation
  "The applicant shall submit a final subdivision plat").
- **Location:** 873 S 1500 West, Salt Lake City, Salt Lake County (staff report).
- **approval_status:** Approved — Record of Decision, May 22, 2019, "Decision: Approved"
  (`http://www.slcdocs.com/Planning/Planning%20Commission/2019/0522ROD.pdf`).
- **zoning.district:** `R-1-5000` Single-Family Residential District (ROD; Tier 3).
- **zoning.status:** sourced (district per ROD/staff report; Tier 3 only).
- **lot_count:** 2 — "The existing home located at 873 South 1500 West would remain and an
  additional lot would be created at the corner of 1500 West and 900 South" (ROD).
- **parent parcel ID(s):** `15-10-276-009-0000` (staff report).
- **lot_areas:** GAP — not recovered from search text. (Planned-development relief was for minimum
  public-street frontage on one lot, so both lots plausibly meet the 5,000 sqft minimum — but this
  is inference, not a fact; keep as GAP.)
- **lot_dims (frontage per lot):** GAP.
- **metes_and_bounds:** unknown.
- **entry/book/page/date:** GAP.
- **Note:** staff report PDF may have a narrower approval scope than a final plat; if the final
  recorded plat is found, prefer it.

---

## 6. 1925 West North Temple Subdivision — detailed proposed plat; approval + approval-date zoning unresolved

**Status: candidate (partial — do NOT present as approved)** — the richest free geometry in the
pool, but demonstrably proposed, not recorded.

- **plat_pdf:** `http://docs.cottonwoodtitle.com/118/118082-CAY/Proposed%20Subdivision%20Plat%202020-03-06%20(rcvd%204.1.2020).pdf`
  (plat title "1925 WEST NORTH TEMPLE SUBDIVISION"; fetched verbatim 2026-09-24).
- **Location:** 1925 West North Temple, Salt Lake City, Salt Lake County (plat).
- **approval_status:** UNKNOWN — this is a proposed subdivision plat (dated 2020-03-06, received
  4/1/2020); recorder entry/book/page/date fields on the plat are blank. No approval document found.
- **zoning.district:** UNKNOWN — 2009 SLC minutes (`http://www.slcdocs.com/Planning/Planning Commission/2009/July/78min.pdf`)
  show the property with CC and CG zoning, but that predates the 2020 plat and cannot establish the
  approval-date district; a later third-party result suggests TSA-MU. Per policy, a later rezone
  disqualifies a plat from the scored set — so the district at approval must be determined before
  this plat can be scored. Do not default to CC/CG or TSA-MU.
- **zoning.status:** unknown.
- **lot_count:** 2 (plat).
- **parent parcel ID(s):** `08-34-353-045` and `15-03-101-026` (plat).
- **lot_areas:** Lot 1 = **603,809 sqft / 13.862 acres**; Lot 2 = **267,528 sqft / 6.142 acres**;
  plat total **871,336 sqft / 20.003 acres / 2 lots**.
- **lot_dims (frontage per lot):** GAP — measure from plat.
- **metes_and_bounds:** yes — full exterior boundary description on the plat.
- **entry/book/page/date:** blank on plat (proposed, not demonstrably recorded).
- **Related note:** a LoopNet legal description references "1925 WEST NORTH TEMPLE SUB AMD",
  suggesting a recorded amended plat may exist — not verified; do not cite as fact.

---

## 7. Petition 410-07-11 (R-1/7,000 Planned Development, 2007) — lot areas sourced; approval unconfirmed

**Status: candidate (partial)** — older SLC staff report with per-lot square footage in the
publication-date range; approval outcome and final details are gaps.

- **plat_pdf:** `http://www.slcdocs.com/Planning/Planning Commission/2007/June/4100711.pdf`
  (Salt Lake City Planning Commission staff report; publication date 2007).
- **Location:** Salt Lake City, Salt Lake County (specific address not recovered from search text — GAP).
- **approval_status:** GAP — staff report only; Planning Commission decision not found.
- **zoning.district:** `R-1/7,000` (staff report; Tier 3).
- **zoning.status:** sourced (district per report; Tier 3 only).
- **lot_count:** 4, ranging **7,755–12,761 sqft** each (staff-report text); exact per-lot values: GAP.
- **parent parcel ID(s):** GAP.
- **lot_areas:** 7,755–12,761 sqft range only; individual lot areas GAP.
- **lot_dims (frontage per lot):** GAP.
- **metes_and_bounds:** unknown.
- **entry/book/page/date:** GAP.
- **Context from report:** planned-development discussion included reducing public street width
  from 50 ft to 27.5 ft — relevant to road-width proxy if/when the plat is scored.

---

## Lower-tier leads (need a qualifying plat-containing PDF and approval evidence)

### A. 759 S Post St (PLNSUB2022-00289 / PLNPCM2022-00290)
- Minutes (`http://www.slcdocs.com/Planning/Planning%20Commission/2022/09.%20September/PC09.14.2022minutes.pdf`)
  and agenda (`http://www.slcdocs.com/Planning/Planning Commission/2022/09. September/PC09.14.2022AMENDEDagenda.pdf`):
  subdivide into **2 lots**, R-1-5,000; staff review noted each lot meets the 5,000 sqft minimum,
  widths slightly over **45 ft** and slightly over **34 ft** (PD modifies the 50 ft minimum).
- Approval decision: GAP (minutes excerpt ends before the motion).
- Staff report / plat PDF: GAP.

### B. Petition 490-06-22 (SR-1A, 2006)
- Staff report: `http://www.slcdocs.com/Planning/Planning Commission/2006/August/4900622b.pdf`;
  search text: Lot 1 = **10,124 sqft**, Lot 2 = **8,284 sqft**, SR-1A, 50 ft width minimum.
- Name, address, county confirmation, parent IDs, approval outcome, M&B, recording: all GAP.

### C. Petition 00044 — Robinson-Alder / FR-3 (2010)
- Staff report: `http://www.slcdocs.com/Planning/Planning Commission/2010/June/00044.pdf`;
  search text: **2 lots**, 36,725 sqft and 34,593 sqft; FR-3, minimum 12,000 sqft / 80 ft per report.
- Project name, address, parent ID, actual approval, M&B, recording: all GAP.

### D. Petition 490-05-64 (2006)
- Staff report: `http://www.slcdocs.com/Planning/Planning Commission/2006/April/4900564.pdf`;
  search text: **3 lots**, each 6,600 sqft, each 55×120 ft.
- Name, address, zone, actual approval, parent parcel, M&B, recording: all GAP.

---

## Appendix — sourcing tiers used

- **Tier 1 (NERON verified rules):** `M-1-01` (10,000 sqft / 80 ft); MU districts have verified
  absence of lot area/width minimums. Verified store checked 2026-09-24.
- **Tier 2 (official city code):** SLC Code §21A.32.030 (BP: 20,000 sqft / 100 ft) via codelibrary
  URL above — current-day page; approval-date version should be confirmed before scoring.
- **Tier 3 (plat-specific staff reports):** all slcdocs.com staff reports, agendas, minutes, RODs
  above. All free, all exact URLs.

## Appendix — candidates deliberately excluded

- **Cove Minor Subdivision** (`http://www.slcdocs.com/Planning/Planning Commission/2010/August/00182.pdf`):
  proposed 1 commercial + 6 residential lots (CB + R-1/7,000), but staff recommended **denial**;
  excluded unless minutes show approval.
- Anything behind the SLCo Recorder $5/token portal, trials, signups, calls, or emails: excluded
  by assignment constraint.
- **No OS/PL** (Open Space / Public Lands) approved subdivision plat was found in the SLC staff-report
  corpus searched on 2026-09-24 — targeted search returned only rezones and process documents, no
  qualifying subdivision. GAP for the preferred-order OS/PL tier.

---

## GreenRush-2 swing (2026-09-24 ~10:05+ MDT) — browser-healthy turn

Worker: **GreenRush-2** (benchmark lane). Browser tools HEALTHY this turn (search + open both
returned). Priority order: (1) city engineering standard drawings, (2) Broadbent PMN PDF,
(3) Hidden Pines / nearest-miss zoning.

### H1. Herriman local-street road_width_ft — FOUND, citable (closes blocker for Herriman)

- **Source:** Herriman City Engineering Department, Standard Drawing **RD-01B / RD-01C**,
  "TYPICAL ROADWAY CROSS SECTION", fetched verbatim 2026-09-24:
  `https://herriman-website-files.s3.us-west-1.amazonaws.com/Engineering_Standards/02-RD.pdf`
  (tool-returned via web search; PDF text extraction partially garbled but section
  dimensions legible).
- **Values (asphalt/pavement width, which is the prototype's `road_width_ft` semantic —
  the road band centered on the centerline in prototype/geometry.py):**
  - **LOCAL — 60'-0" RIGHT-OF-WAY → 32'-0" ASPHALT** (RD-01B)
  - **LOCAL — 53'-0" RIGHT-OF-WAY → 28'-0" ASPHALT** (RD-01C)
- Supporting: Herriman Final Plat & Engineering Review checklist (Jan 2024) references
  "standard roadways (60')" and "narrow roadways (50')" sight-triangle standards:
  `https://www.herriman.gov/uploads/files/4764/Final-Plat-and-Engineering-Review-Requirements-Jan-2024.pdf`
- **Selection rule (explicit, not a fill):** which local section applies depends on the
  plat's dedicated ROW (60' vs 53') as shown on the plat or improvement plans. Record
  `road_width_ft` per plat with this citation + the plat's ROW. Both values are citable
  today; no plat has been assigned one yet.
- This directly supersedes the corpus-gap note "No Herriman/Riverton/South Jordan/SLC
  local-street standard found in citable form" for **Herriman only**. Riverton and South
  Jordan remain gaps (legs below).

### H2. Riverton local-street road_width_ft — FOUND, citable (closes blocker for Riverton)

- **Source:** Riverton City *Standard Specifications and Plans Manual* (Engineering/Public
  Works Dept, updated September 29, 2021), Chapter 7 "Street Design Standards" summary
  table, fetched verbatim 2026-09-24:
  `https://cms8.revize.com/revize/rivertonut/departments/public-works/engineering/documents/standard-specifications-and-plans.pdf`
- **Values (Functional Classification: Major Collector / Minor Collector / Local):**
  - ROW Width: 66 ft / 60 ft / **54 ft (Local)**
  - **Pavement Width: 42 ft / 35 ft / 29 ft (Local)**
- **road_width_ft (Riverton local) = 29 ft** — citable today with the URL + table citation.
  Adopted by Ordinance 20-23 (Nov 17, 2020) incorporating the 2020 Standard
  Specifications and Plans; manual states these standards "are required unless
  specifically approved otherwise by the Riverton City Council."

### H3. South Jordan residential road_width_ft — FOUND, citable (closes blocker for South Jordan)

- **Source:** City of South Jordan *Standard Drawings*, Drawing **S-1 "Road Widths and
  Border Areas"** (title block dated 1/8/00; current PDF at
  `https://sjc.utah.gov/DocumentCenter/View/514/Standard-Drawings-PDF`, included in the
  March-2024-updated Construction Standards and Specifications set). Page 90 of the
  drawings PDF is a scanned drawing; dims verified visually:
- **"55-FOOT R.O.W. RESIDENTIAL — 28' OF ROAD SURFACE"** (two 14' travel lanes; border
  areas 2.5' curb, 5' park strip, 6' sidewalk, 10' PUE each side).
- **road_width_ft (South Jordan residential) = 28 ft** — citable today with the
  S-1 drawing citation. Same page also shows minor collector 44', major collector 58',
  arterial 84'. Consistent with Construction Standards Ch. 7 §7.8 definition:
  "A Residential Street is defined ... as any street that has a 55 foot right of way
  or less and/or with 28 feet of pavement width or less."
- With Herriman (RD-01B: 60' ROW → 32 ft / 53' ROW → 28 ft) and Riverton (local 54' ROW
  → 29 ft pavement), all three target cities now have citable local-street
  road_width_ft values. Remaining step is matching each plat's actual ROW.

### H4. Hidden Pines final-approval + completion evidence — FOUND 2026-09-24 (zoning still gap)

- **Final subdivision approval:** Riverton City Planning Commission minutes, meeting **June 27,
  2019** (minutes approved August 8, 2019):
  `https://www.utah.gov/pmn/files/529031.pdf`. Motion text (verbatim from extractable text):
  "Commissioner Hansen moved to APPROVE Application #PLZ-19-1003 — Hidden Pines Subdivision,
  to be located at 3814 West 13800 South, subject to [4 listed conditions]" — motion passed
  unanimously. **42 lots** (agenda: "42-lot subdivision proposed near 3814 West 13800 South").
- **Completion acceptance + bond release:** Riverton City Council work session item, Sept 21, 2021:
  Warranty bond release for "Hidden Pines (7212)", 3814 W 13800 S, developer **Cazco Enterprises,
  LLC**, Western Surety Company; improvements inspected and found complete to Riverton standards;
  100% release approved ($103,673.07 release at that tranche; $1,187,851.73 total bond):
  `https://legistarweb-production.s3.amazonaws.com/uploads/attachment/pdf/1063141/_IP__2021Sep21_IssuePaper_HiddenAcres_7212_.pdf`
- **Geotechnical report (context only):** "Geotechnical Investigation, Hidden Pines Subdivision,"
  property at **3854 West 13800 South**, March 4, 2019, for Lovell Development (Project 18187):
  42 new single-family homes; site accessed from 13800 S and Deer Mountain Drive; bound by a vacant
  field to the north, a park to the east (Hamilton Sports Park), 13800 South to the south,
  existing homes to the west:
  `https://www.rivertonutah.gov/departments/public-works/engineering/geotechnical-reports/hidden-pines-subdivision-geotechnical-report.pdf`
  No zoning district in the report.
- **Zoning: still UNSOURCED after minutes, geotech, and bond-record legs.** None of the three
  sources names the approval-date zone district. The minutes say zoning "was described" but the
  district is not in extractable text. Keep as explicit gap — do NOT infer from current
  fabric or lot yield.
- **road_width_ft candidate:** Riverton local = **29 ft pavement** (H2 above), conditional on
  sourcing that Hidden Pines' internal streets are local (54' ROW). Street names/classification
  and plat-specific ROW: still gaps.

### H5. Broadbent PMN PDF 1015940.pdf — CONFIRMED DEAD 2026-09-24 (replacement source needed)

- Direct fetch of `https://www.utah.gov/pmn/files/1015940.pdf` returns a **315-byte HTML 404**,
  not a PDF. The PMN URL stored in `plats.json` is stale.
- Public search did not recover a replacement Broadbent staff report, final-plat document, or
  final-approval record. Herriman PrimeGov portal is publicly reachable at
  `https://herriman.primegov.com/Public/Portal`, but no Broadbent result was extracted this turn.
- UGRC SGID parcels queried around ~6400 W 13800 S found no obvious large unsubdivided parent
  at the stated address (envelopes too wide; address-to-coordinate uncertainty unresolved).
- **Standing gaps:** final approval, exact parent location/geometry, plat-specific ROW,
  replacement plat document. The old claim "M&B in plat PDF" is downgraded to unsourced until
  a live replacement document is fetched.

## GreenRush-3 swing (2026-09-24 ~10:15–11:30 MDT) — UGRC child-parcel reconstruction + Hidden Pines deep leg

### GR3-H1. Village at the Boulders Phase 3 — parent polygon RECONSTRUCTED (zoning/ROW/count still gaps)

- **Recording (closed, official abstract):** `VILLAGE AT THE BOULDERS PHASE 3`, Entry `12826461`,
  Plat Book/Page `2018P / 274`, recorded 2018-08-09 11:37 AM, dedication type subdivision, status completed.
  Abstract: `http://docs.cottonwoodtitle.com/MDD/28.pdf`
- **Parent:** `33083510770000` ("LOT F"). Re-verified ABSENT from 2026 UGRC fabric (subdivided, as expected).
- **Child set (20 parcels, from abstract + live fabric):**
  - Common area / private road: `33083510780000` (14850 S Trap Rock Way, 25,851.41 m²)
  - 9 surviving lots: `33083510920000` VB57, `33083510910000` VB58, `33083510900000` VB59,
    `33083510890000` VB60, `33083510850000` VB61, `33083510860000` VB62,
    `33083510840000` VB65, `33083510790000` VB68, `33083510810000` VB70 (~610.9 m² each)
  - 10 AMD units from `VILLAGE AT THE BOULDERS PHASE 3 AMD`, Entry `13678229`, `2021P` p143,
    recorded 2021-06-01, which replatted 4 original lots (VB63, VB66, VB67, VB69 — confirmed absent from
    fabric): `33083511010000`, `33083511020000`, `33083510990000`, `33083511000000`, `33083510950000`,
    `33083510960000`, `33083510970000`, `33083510980000`, `33083510930000`, `33083510940000` (~152.7 m² each)
  - Abstract says "Active Parcel Numbers Found: 11" but rows list 10; VB64 unaccounted — minor gap.
- **Union:** deterministic shapely union of the 20 native-geometry polygons
  (UGRC endpoint `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Parcels_SaltLake/FeatureServer/0`,
  anonymous) → valid single Polygon, **32,876.9 m² = 8.125 acres**, exactly equals the attribute sum.
  Saved: `samples/village_boulders_ph3_parent.geojson` (EPSG:4326). Built 2026-09-24 by GreenRush-3
  (script, not model geometry).
- **CRITICAL SERVICE GOTCHA (durability note):** the endpoint's `f=geojson` geometries are ~0.578x
  the `Shape__Area` attribute — a systematic artifact across every parcel tested (single-family and
  townhome alike), verified by geodesic cross-check and by native `f=json&outSR=102100` where the
  common-area outer ring (33,487.8 m²) minus its 8 interior rings equals the attribute exactly
  (25,851.4 m²). **Always use native f=json for union geometry; never f=geojson.**
- **Still gaps:** approval-date zoning district (2023 amendment records show a label rendered `R-20-43`
  at 14853 Trap Rock Way — 2023, not 2018; label may be extraction-garbled; NOT approval-date);
  plat-specific/private road ROW (abstract confirms a PRIVATE road, so Herriman public local-street
  standards cannot be assigned); exact 2018 approved lot count (labels VB57–VB70 suggest ~13–14 original:
  9 surviving + 4 replatted; VB64 unaccounted).
- **Verdict:** parent geometry now the strongest-reconstructed in the corpus, but the plat remains
  scored:false — townhome phase, not a greenfield single-family yield test; harness honesty contract
  requires all four zoning dims.

### GR3-H2. Hidden Pines — amended plat found; zoning still unsourced; child union not provable

- **Amended plat (NEW, official):** City Council minutes 2021-07-13 — the "Hidden Pines Amended Plat"
  "combined 42 residential lots into 38 lots" (refund request by Hidden Pines Land, LLC):
  `https://rivertoncity.granicus.com/DocumentViewer.php?file=rivertoncity_e0ed695287c2ca40ab718399f5451e2b.pdf&view=1`
  - 100% warranty bond release for **Hidden Pines Amended (9395)** approved 2022-02-15,
    developer JCraft Homes, 13800 South 3870 West:
    `https://legistarweb-production.s3.amazonaws.com/uploads/attachment/pdf/1229556/2022Feb15_IP_Release_HiddenPines_9395_.pdf`
  - (Original Hidden Pines (7212) bond release approved 2021-09-21, already in plats.json.)
  - NOTE for UGRC work: the 2026 fabric reflects the 38-lot amended plat, not the original 42.
- **UGRC child-fabric findings:** small-lot cluster sits NORTH of 13800 S on Deer Mountain Dr /
  3825 W / 3870 W / 13715 S (recorder blocks `33051510`, `33051530`, `33051540`), all Private,
  ParcelYear 2026, ~2,250–2,850 m². 59-parcel cluster clearly includes adjacent development(s);
  a separate big-lot regime (Red Tail Dr / Yearling Dr / Deer Horn Dr, 0.86–1.23 ac) is older/other.
  Cleanest 42-parcel hypothesis: `3305151017–1022` (6) + `3305153001–3030` (30) + `3305154001–4010` (10)
  = 46, minus 4 tiny non-lot fragments (3025/3026/3028/3030) = exactly 42 parcels; union = 100,059 m²
  = **24.72 acres**. The "~11–12 acre parent" premise in earlier notes is inconsistent with the fabric
  (42 lots × ~2,250 m² need ≥23.4 ac before roads; 11.75 ac matches the Cove at Silver Sky candidate,
  not Hidden Pines — possible premise mix-up, flagged not filled).
- **Verdict:** membership cannot be proven from the open service (no SUBDIV_NAME field; no recorded-plat
  entry/book/page found in the searchable corpus), so **no union file was created** and the candidate
  is not reconstructable to benchmark standard. Needs the recorded plat (SLCo Recorder, entry ~2019–2020;
  the open SLCo abstract portal did not surface it this turn).
- **Zoning:** still UNSOURCED after a full new leg (June 18, 2019 sewer-easement issue paper
  `https://rivertoncity.granicus.com/MetaViewer.php?view_id=1&clip_id=283&meta_id=18153` — says only
  "under existing zoning", no district; PC staff-report packet not found via PMN/Granicus search).
  Unconfirmed hypotheses ONLY: `R-3-SD` (third-party countyoffice snippet ties a nearby Riverton property
  to "R-3-SD, single-family residential, 1/3 minimum lot sizes" — Hidden Pines lots ~0.33 ac fit) or `R-3`
  (a 2022 PC agenda names "R-3 (Single Family Residential, 14,000-sf lots)"). **NOT citable — do not
  promote to zoning.status=known.**
- **ROW:** still unsourced plat-specifically. Internal streets include Deer Mountain Dr. Riverton local
  standard (54' ROW / 29 ft pavement) stays conditional.

### GR3 carry-forward lesson

The UGRC anonymous parcel endpoint is a working, citable parent-polygon source for RECORDED plats
(via child-union), but child-membership pinning needs a recorder abstract or the recorded plat itself;
the open service has no subdivision-name attribute. And `f=geojson` geometries are systematically
~0.578x the attribute area — native `f=json&outSR=102100` is the only trustworthy geometry path.

## GreenRush-4 final hunt (2026-09-24 ~10:20–10:50 MDT) — Hidden Pines approval-date zoning: STILL UNSOURCED, legs exhausted

Objective: name Hidden Pines' (PLZ-19-1003, 42 lots, approved 2019-06-27, 3814/3854 W 13800 S) zoning
district at approval date from an official citable source. Result: NOT FOUND. Zoning stays explicitly
UNKNOWN / null in plats.json. No speculative geometry was created; harness not run.

### Official legs worked
1. **June 27, 2019 PC minutes re-opened** (`https://www.utah.gov/pmn/files/529031.pdf`): motion text
   confirms final subdivision approval of "Application #PLZ-19-1003 — Hidden Pines Subdivision",
   "42 residential lots", with the Deer Mountain Drive public-road connection discussed and city
   engineering review complete except minor redlines. The staff summary describes "zoning in the area"
   but names NO district in the extracted Hidden Pines section. Minutes were approved at the
   2019-08-08 PC meeting (per that meeting's published agenda packet).
2. **PLZ-19-1003 staff-report packet:** searched PMN/Granicus/Legistar and web — no staff report or
   agenda packet with the application number surfaced. Riverton's pre-2019 Granicus archive is not
   indexed by application number in the searchable surface.
3. **Recorded plat / recorder abstract:** searched for a Hidden Pines recorded plat entry/book/page
   (SLCo abstract, title-document surfaces, web). No free searchable hit. The amended plat (42→38,
   2021) and the original (2019) both remain unsourced as plat documents.
4. **Rezone history:** no pre-June-2019 rezone ordinance tying the parcel to a district was found in
   the searchable ordinance corpus.
5. **Official zoning map PDF** (`https://www.rivertonutah.gov/departments/planning/documents/rivertonzoningmap.pdf`,
   linked from the city maps page `http://www.rivertonutah.gov/planning/maps.php`): page fetch failed
   terminally this turn (browser-service fetch error, not retried). Even when readable, this is a
   current-era map and cannot prove the 2019 approval-date district without dated or paired
   no-change ordinance history. Left as a recoverable lead, NOT evidence.
6. **2022-03-01 PC final subdivision mention** (hemofilia mirror of Granicus): item "final subdivision,
   Hidden Pines, 42-lot, Brett Lovell" — refers back to the 2019 approval; names no district.
   (The mirror domain is low-quality; the original sits behind rivertoncity.granicus.com.)

### Context facts established this turn (none name the district)
- Stormwater reimbursement Resolution 20-13 (City Council 2020-02-18): Hidden Pines at ~3870 W 13800 S,
  developer Cazco Enterprises, $27,759.30 over-built storm drainage reimbursed.
  `https://legistarweb-production.s3.amazonaws.com/uploads/attachment/pdf/532081/IP_Resolution_20-13_Stormwater_Agreement.pdf`
- Original bond-release issue paper is filed under a misnamed filename
  (`..._IP__2021Sep21_IssuePaper_HiddenAcres_7212_.pdf`) but the CONTENT is Hidden Pines (7212),
  3814 W 13800 S, Cazco Enterprises, $103,673.07 — filename quirk, no content impact.
- Geotechnical report on the city site is project #18187, CLIENT "Lovell Development" (Brett Lovell's
  entity) — "PROJECT NAME Hidden Pines Subdivision". Context only.
- The `R-3-SD` hypothesis seen in a 2022 council item ("R-3-SD, single-family residential, 1/3 minimum
  lot sizes") belongs to a DIFFERENT property (13040 S Redwood Rd, Riverton Ranch development
  agreement) — it is NOT Hidden Pines evidence. Hypotheses remain R-3-SD or R-3, both unconfirmed,
  neither promoted.

### Verdict
- `zoning.district` for Hidden Pines: **explicit UNKNOWN**. All bounded official legs are exhausted;
  the next credible step would need the recorded plat (recorder's office, in-person/fee) or the
  Granicus video/packet archive for the 2019-06-27 meeting — beyond the free bounded-hunt scope.
- UGRC union: not built (membership still unpinned; GR3 verdict stands — no recorded-plat entry, no
  subdivision name in the open service).
- Internal-street ROW: still plat-unspecific (Riverton local 54'/29' stays conditional).
- Plat stays in `research_candidates_not_scored` with zoning null. Scored set unchanged at 0/16.

### GR4 carry-forward lesson
Approval-date zoning for pre-2020 Riverton plats is the binding constraint and the searchable
corpus (PMN minutes + Legistar papers + open abstracts) does not carry it. Future Hidden-Pines-class
leads should be triaged EARLY on "does a staff report or recorded plat exist in the free corpus?"
before spending reconstruction effort — a 10-minute staff-report check gates the whole lane.

---

## GreenRush-5 triage (2026-09-24 ~10:25-11:05 MDT) — pivot off Hidden Pines; Swaner gated, not scoreable

**Verdict: no candidate scoreable this turn. Scored set remains 0/16. Harness re-run: 0 scored, honest.**

Swaner Subdivision (PLNSUB2021-00740) was the only greenfield candidate with approval + zone
sourced, so it received the full gate. Three independent gaps found:

1. **Staff-report PDF not found** after 4 targeted searches. Official record stands on: motion
   sheet `http://www.slcdocs.com/Planning/Planning%20Commission/2022/03.%20March/00740M.pdf`,
   PC minutes `http://www.slcdocs.com/Planning/Planning%20Commission/2022/03.%20March/PC03.23.2022minutes.pdf`
   (read verbatim this turn), and the Utah PMN public notice.
2. **Parent-parcel membership unprovable.** UGRC spatial query around geocoded 2691 N 2200 W
   (40.82738, -111.9606; Parcels_SaltLake FeatureServer, anonymous) returned large private
   parcels in the 2200W-3200W band. Closest size match: `08091000080000` (1,770,695 m2 =
   437.6 ac, address "2940 N 3200 W") vs minutes' "~430 ac". But the notice address matches no
   parcel address, the applicant's slide places the site "between 2200 West and 3200 West", and
   the site may span multiple parcels. Recorded as hypothesis ONLY; no union built.
3. **road_width_ft has no clean citable SLC number.** SLC Code 20.26.060
   (`https://codelibrary.amlegal.com/codes/saltlakecityut/latest/saltlakecity_ut/0-0-0-99954`,
   fetched verbatim) defers street cross-sections to the Transportation Division's Street and
   Intersection Typologies Design Guide (neighborhood street: 53-66 ft ROW, 10 ft lanes; no
   single pavement-width figure). Minutes road mentions are project-specific (resident: road
   "25-30 feet"; staff: 36 ft additional asphalt on 2200 W), not standards.

**New minutes facts banked** (PC03.23.2022minutes.pdf): unanimous preliminary-subdivision approval
2022-03-23 (motion Bachman, second Scheer); zone BP confirmed in minutes; 20 lots; ~430 ac
primarily vacant; developer Scannell Properties (Colby Anderson); new ROW: N-S roadway ~2900 W,
E-W ROW at 2950 N, additional ROW dedicated along 2200 W + 3200 W; staff contact Daniel Echeverria.

**Broadbent Business Park re-examined:** M-1 district / 8 lots / parent 15-17-300-029 / 2012-04-11
PC approval all previously sourced, but the same SLC road-width gap applies, and it is a re-plat
around existing buildings (not greenfield) — stays not_scored.

**Side finding:** Murray City Code 16.16.180 codifies "minimum width 49 ft with asphalted width
25 ft" (`https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/0-0-0-9269`) — citable
road_width_ft for any future Murray candidate (none in the set today).

**Next highest-value document:** the staff report (or final plat) for PLNSUB2021-00740 — it would
name parent parcel IDs, plat ROW widths, and lot layout in one shot.

---

## GreenRush-7 — Meadows of Murray (Project #20-009) — BLOCKED, frontage gap

**Status: not_scored** — frontage is a genuine evidence gap, not a research failure.

**Research completed 2026-09-24 by GreenRush-7:**

- **Official packet:** Murray City Planning Commission, May 7, 2020 (https://murray.utah.gov/DocumentCenter/View/11088/050720-Planning-Commission-Packet?bidId=)
- **Project:** Meadows of Murray, Project #20-009, 533/551/565/583/593/631 E Winchester St + 6363 S 525 E
- **Approved:** 26-lot twinhome subdivision, 4.41 acres, 10 vacant parcels. Preliminary 2020-04-16, Final review 2020-05-07 (staff recommended approval).
- **Zone:** R-N-B, Residential Neighborhood Business (approval-date).
- **Min lot area:** 5,000 sqft per twinhome side, cited to §17.140.040 (staff report).
- **Setbacks:** Front 25', Rear 25', Interior Common Side 0', Interior Side 8', Corner Side 20'.
- **Street:** Fashion Creek Court, 571' public cul-de-sac. 25' pavement + 2.5' curb/gutter + 5.5' park strips + 4' sidewalks (both sides) = 49' corridor, matching Murray §16.16.180.
- **Parent parcels:** 22-19-279-015, -016, -018, -024, -025, -027, -028, -021, -009, -010 (retired). 26 child parcels on Fashion Creek Ct identified in current UGRC fabric.

**Blocking gap:** The approval-date R-N-B twinhome standards (Sec. 17.140.040 as amended March 17, 2020) state "specific setback and area requirements" — NO minimum lot width. The staff report section header reads "Lot Area, Width, Setbacks, and Height Standards" but lists no width value. Per ZONING_POLICY, min lot width may proxy for min_frontage_ft ONLY when the district's code states a width minimum. None exists. Frontage is UNKNOWN. The harness requires min_frontage_ft for scored plats (raises ValueError if missing). **Meadows cannot be scored.**

**Pivot attempted:** Matthew Avenue 3-Lot Subdivision (Project #20-090, 6450 & 6468 S 1300 E, R-1-6, 3 lots, approved 2020-08-20). Parent parcels not locatable in current UGRC data — addresses 6450/6468 S 1300 E do not appear; subdivision may not have been recorded. Pivot failed.

**Lesson:** Murray's remaining greenfield/detached subdivisions are scarce. Most recent approvals are infill, flag lots, or attached product (twinhome/townhome/PUD). The benchmark may need to look beyond Murray for the second scored plat, or accept attached-product plats with complete standards.
