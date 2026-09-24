# BENCHMARK PACKET — Fields Subdivision
**File #4S22/SUB-000226-2022** | Assembled by Evidence/Reconstruction lane, 2026-09-24
**Claim status: machine-draft** (facts sourced from official documents + UGRC; not human-verified)

## 1. Official project identity / file number
- Project name: **Fields Subdivision**
- File: **4S22/SUB-000226-2022**
- Applicant: Nancy Fields (applicant = agent)
- Planner: Karyn Kerdolff (Taylorsville Community Development)
- Source: Planning Commission Staff Report, File #4S22/SUB-000226-2022, dated June 7, 2022 (staff_report.pdf)

## 2. Approval evidence
- **Final plat RECORDED** — the strongest approval evidence available:
  - Parent parcel 21111020270000 is RETIRED from UGRC Parcels_SaltLake (ParcelYear 2026).
  - Two child parcels exist with the EXACT approved lot dimensions (see §5). A plat cannot be recorded in Salt Lake County without city approval signatures.
- Preliminary: staff recommended approval June 7, 2022 ("Staff recommends that the Planning Commission approves the Fields Preliminary Plat for a two (2) lot subdivision"); PC meeting June 14, 2022, Agenda Item 3.
- **Gap (honest):** the June 14, 2022 PC vote minutes were not recovered after two search attempts. The recorded final plat supersedes this as approval evidence.
- History: applicant received final plat approval in 2017 for the same subdivision but did not record within the approval timeframe — this 2022 application is the re-approval.

## 3. Final / recorded plat
- **RECORDED** (genealogy-confirmed; see §2, §5).
- Recorder confirmation layer: SLCo Recorder free-search UI not attempted (form-based; no subagent browser path). Parcel genealogy from the county's own parcel fabric is recorder-derived ground truth. Plat book/page not retrieved — noted as a minor gap, not a blocker.

## 4. Approved lot / unit count
- **2 lots** on **0.72 acres** (staff report):
  - Lot 1: 21,139 sqft (existing single-family home, remains intact)
  - Lot 2: 10,263 sqft (proposed, south of Lot 1)
  - Total: 31,402 sqft = 0.721 ac

## 5. Historical parent parcel geometry (pre-development) — CHILD-UNION RECONSTRUCTION
- Original parent: **21111020270000** (4768 S 1175 W) — RETIRED, not in current UGRC.
- Reconstructed via child union (both children still current, ParcelYear 2026):
  - **21111020370000** — 4768 S 1175 W — geodesic **21,139.2 sqft** vs approved 21,139 (0.00%)
  - **21111020380000** — 4776 S 1175 W — geodesic **10,263.0 sqft** vs approved 10,263 (0.00%)
  - Children are adjacent (touch = True); union = **31,402.3 sqft = 0.721 ac** vs staff report 0.72 ac (0.1%)
- This is the cleanest parent reconstruction in the benchmark to date: exact dimensional match on both children.
- Geometry: `children.geojson` (WGS84, UGRC Parcels_SaltLake FeatureServer, retrieved 2026-09-24). The union polygon = the historical parent.
- Parent-first doctrine: parent confirmed via genealogy (retired parent + exact-match children), not assumed.

## 6. Zoning / rule context at approval date
- District: **Taylorsville R-1-10** (rezoned R-1-15 → R-1-10 by PC 6/13/17, CC 7/5/17). General Plan: Low Density Residential. Surrounding: OS / R-1-15 / R-1-10.
- Applicable: LDC §§13.20, 13.21, 13.30 (staff report cover).
- Dimensional standards (staff report, quoting code — official-secondary):
  - Min lot area: **10,000 sqft**
  - Min lot width: **80 ft**
  - Front yard: 25 ft; side yard 5 ft (16 ft combined); rear yard 15 ft
  - Min home size: 1,200 sqft (1-story) / 1,875 sqft (2-story)
- Cross-check for GreenRush: verify against rulegraph/taylorsville_params_draft.json (Pack waves) + input-consistency script before scoring.

## 7. Product type(s)
- Residential: **1 existing single-family home (retained) + 1 new single-family lot**.

## 8. Raw source files (this directory)
- `staff_report.pdf` — June 7, 2022 PC staff report (File #4S22/SUB-000226-2022) with exhibits
- `staff_report.txt` — pdftotext extraction
- `children.geojson` — UGRC child parcel geometries (WGS84)
- `SHA256SUMS.txt` — hashes

## 9. Source URLs + retrieval dates
- https://www.utah.gov/pmn/files/859213.pdf (retrieved 2026-09-24)
- UGRC: https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Parcels_SaltLake/FeatureServer/0 (queried 2026-09-24)

## 10. Hash / version metadata
See `SHA256SUMS.txt` (sha256, computed 2026-09-24):
- staff_report.pdf: 1157c957...
- children.geojson: 8b25a6de...

## 11. Untouched NERON run
- **NOT RUN** — handoff to GreenRush. Packet assembled; awaiting GreenRush triage (TRIAGED gate) then blind score.

## Lane notes for GreenRush triage
1. Infill 2-lot split, not greenfield — run the harness honestly; record whether Rank-1 taxonomy findings replicate at small scale.
2. Parent = union of the two children (reconstructed; exact match). Use the union polygon as harness input.
3. Harness inputs from staff report: min_lot_area 10,000 sqft, min_frontage 80 ft (both quoted); road_width_ft: Taylorsville local standard needed (check draft pack / GR-2 banked standards).
4. Final plat recorded → this is a CLOSED case (preliminary + final), stronger than preliminary-only.
5. Evidence level on scoring: L2 (official public historical project; blind holdout if NERON run is untouched).
6. June 14, 2022 vote minutes unrecovered — if the vote-gate requires the minutes explicitly, one more targeted hunt (Taylorsville city site document center) could close it; the recorded plat is the stronger evidence.
