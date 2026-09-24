# BENCHMARK PACKET — Taylorsville Garden Flag Lot Development
**File #1S25/SUB-000494-2024** | Assembled by Evidence/Reconstruction lane, 2026-09-24
**Claim status: machine-draft** (facts sourced from official documents; not human-verified)

## 1. Official project identity / file number
- Project name: **Taylorsville Garden Flag Lot Development**
- File: **1S25/SUB-000494-2024**
- Applicant: Jake Larsen, Desert Peak Builders
- Planner: Jim Spung, AICP, Senior Planner (Taylorsville Community Development)
- Source: Planning Commission Staff Report, File #1S25/SUB-000494-2024, dated May 8, 2025 (Exhibit C of 1430381.pdf)

## 2. Approval evidence
- **Preliminary subdivision approval, UNANIMOUS vote**, Taylorsville Planning Commission, **May 13, 2025**
  - Minutes (may13_minutes.pdf = PMN 1294055.pdf): "MOTION: Commissioner Wright moved to approve File 1S25-SUB-000494-2024... The motion was seconded by Commissioner Willardson and passed unanimously."
  - Corroborated: May 6, 2026 extension memo (Terryne Bergeson, Planner II) states "The planning commission granted preliminary approval for the proposed plat with a 5-0 vote."
- Extension of preliminary approval requested May 6, 2026 per LDC §13.43.080(C) (no final plat application filed within 12 months).
- **No final/recorded plat** — preliminary approval only (same posture as Daybreak 12B Plat 1).

## 3. Final / recorded plat
- **NONE RECORDED** (two independent signals):
  1. May 6, 2026 extension memo: approval extension requested because no final plat application was filed.
  2. Both parent parcels still current in UGRC Parcels_SaltLake (ParcelYear 2026) — a recorded plat would retire them into child parcels.
- SLCo Recorder free-search UI not attempted (form-based; no subagent browser path). The two signals above are conclusive per the two-negative-signals rule.

## 4. Approved lot / unit count
- **4 residential lots** on **0.979 acres** (staff report + agenda + minutes agree).
- Configuration: 2 existing duplex lots retained + **2 NEW flag lots** created in the rear yards (staff report: "create two new flag lots behind the existing duplex structures," Exhibit F subdivision plat).

## 5. Historical parent parcel geometry (pre-development)
- Two unplatted parent parcels, **both still current** in UGRC (ParcelYear 2026) — current geometry IS the pre-development parent state (no recorded plat ever altered them).
  - **21033800140000** — 1881 & 1883 W. 4655 S. — staff report 22,215 sqft; UGRC geodesic **22,515.6 sqft** (1.35%)
  - **21033800130000** — 1901 & 1903 W. 4655 S. — staff report 20,037 sqft; UGRC geodesic **20,133.0 sqft** (0.48%)
- Combined: 42,648.6 sqft = **0.979 ac** — matches the official 0.979 ac exactly.
- Geometry: `parent_parcels.geojson` (WGS84, from UGRC Parcels_SaltLake FeatureServer, retrieved 2026-09-24).
- Parent-first doctrine: PASSED — parents confirmed still-current before any geometry talk; area reconciliation <1.5%.

## 6. Zoning / rule context at approval date
- District: **Taylorsville Mixed-Use (MU)** (staff report, Exhibit A zoning map). Surrounding: R-1-8 (north), MU (S/E/W).
- Applicable: LDC §§13.08, 13.12, 13.21, 13.27, 13.28, 13.30 (staff report cover).
- SF residential standards: **§13.23.260(G)(2)** — front setbacks 12–20 ft (from inside edge of sidewalk to porch); front-loaded garages ≥18 ft; side/rear setbacks determined by PC (staff recommends 8 ft min N/S side, front measured from common line bisecting shared driveway); TND design standards (subservient garages, ≥4/12 roof pitch, street-facing gables, ≥50% front porch, entry sidewalks). CUP required to construct the single-family homes.
- Flag lots: **§13.21.220** (staff report includes the standards table; shared 20-ft driveway; Unified Fire approved; no parking on private lane, plat-noted).
- **SCOREABILITY FLAG for GreenRush:** no minimum lot area or minimum frontage quoted in the staff-report excerpts — MU SF standards here are setback/design-driven. The harness needs min_lot_area_sqft + min_frontage_ft from citable sources; check Taylorsville draft pack (§13.23.260 primary text) before scoring. Also: parent is TWO parcels, harness input is one — union the two parent polygons if triage passes.

## 7. Product type(s)
- Residential infill: **2 existing duplex dwellings (retained) + 2 new single-family flag lots**.
- Density: 4 → 6 dwelling units/acre (General Plan: High-Density Mixed-Use, up to 12 du/ac).

## 8. Raw source files (this directory)
- `1430381.pdf` — full May 2026 PC packet incl. extension memo + May 13, 2025 staff report (Exhibit C) with plat/civil exhibits
- `1267987.pdf` — May 13, 2025 PC agenda (Item 3)
- `1281533.pdf` — April 8, 2025 PC minutes (first presentation)
- `may13_minutes.pdf` — May 13, 2025 PC minutes (approval vote)
- `parent_parcels.geojson` — UGRC parent geometries (WGS84)
- `SHA256SUMS.txt` — hashes

## 9. Source URLs + retrieval dates
- https://www.utah.gov/pmn/files/1430381.pdf (retrieved 2026-09-24)
- https://www.utah.gov/pmn/files/1267987.pdf (retrieved 2026-09-24)
- https://www.utah.gov/pmn/files/1281533.pdf (retrieved 2026-09-24)
- https://www.utah.gov/pmn/files/1294055.pdf (retrieved 2026-09-24)
- UGRC: https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Parcels_SaltLake/FeatureServer/0 (queried 2026-09-24)

## 10. Hash / version metadata
See `SHA256SUMS.txt` (sha256, computed 2026-09-24):
- 1430381.pdf: 115bdd1f...
- 1267987.pdf: 781513b1...
- 1281533.pdf: 02420b96...
- may13_minutes.pdf: (in SHA256SUMS.txt)
- parent_parcels.geojson: 7d32a6a3...

## 11. Untouched NERON run
- **NOT RUN** — handoff to GreenRush. Packet assembled; awaiting GreenRush triage (TRIAGED gate) then blind score.

## Lane notes for GreenRush triage
1. Infill flag-lot case, not greenfield — run the harness honestly; record whether Rank-1 taxonomy findings replicate at small scale (per GR-14's mission).
2. Two-parcel parent: union before harness input.
3. Zoning dims: MU §13.23.260(G)(2) setback/design-based; verify min lot area + frontage citable in the Taylorsville draft pack or record the gap.
4. Approval is preliminary (5-0, 2026-05-13), final plat unrecorded — admissible per the Daybreak 12B Plat 1 precedent.
5. Evidence level on scoring: L2 (official public historical project, blind holdout if NERON run is untouched).
