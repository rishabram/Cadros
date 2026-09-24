# Approved-plat benchmark — sample plats (Phase A)

No plat data is invented. Anything not sourced below is a gap, not a fill.

## Sample 1 — THE MILL SUBDIVISION PLAT (full plat text obtained)

- Source: http://docs.cottonwoodtitle.com/122/122419-ETB/MillSubdivisionPlat.pdf
  (recorded plat PDF, free, public)
- Location: NE Quarter of Section 24, T1S R1W, South Salt Lake City, Salt Lake County
- Parent: three tracts (deeds Entry 12902877 Bk10738 p3374; Entry 12978893 Bk10775 p8331;
  Entry 12942030 Bk10756 p7974). Parent parcel IDs on plat: 15-24-236-002, 15-24-236-003
- Stated area: 231,617 sqft / 5.317 acres. ROW dedication 0.452 ac (19,703 sqft)
- Approved lots: 4 — Lot 1: 36,159 sqft (0.830 ac); Lot 2: 93,506 (2.147);
  Lot 3: 40,264 (0.924); Lot 4: 41,984 (0.964). Sum lots + ROW = 231,616 ≈ stated. Commercial.
- Boundary: full 6-leg metes-and-bounds on plat. Reconstructed via benchmark/traverse.py:
  closure error 0.003 ft; computed area 231,614.4 sqft (delta 2.6, rounding). VERIFIED.
- Engine smoke test (prototype run.py, synthetic R-1-8 zoning — geometry path only):
  8 schemes in ~8 s, lot counts 7–15. Geometry flows end to end. (Zoning was a placeholder;
  real benchmark uses per-plat researched zoning.)
- Drawn 12/11/20 by Ensign Engineering. Surveyor cert on plat.

## Sample 2 — VILLAGE AT THE BOULDERS PHASE 3 (abstract; full PDF to pull in Phase B)

- Source: http://docs.cottonwoodtitle.com/MDD/28.pdf (subdivision abstract, free, public)
- Location: Herriman, Salt Lake County. Recorded 8/9/2018, Entry 12826461, Plat Book 2018P p274
- Parent: abstract parcel 33083510770000, LOT F
- Lots visible in abstract: VB57–VB62, VB65, VB68, VB70 + more (14 lot rows shown;
  exact approved count to confirm from full plat PDF in Phase B)
- Parent geometry path: UGRC SGID parcel polygon for 33083510770000, or plat metes-and-bounds.

## Source notes

- docs.cottonwoodtitle.com: browsable Apache index, many recorded plats/abstracts, free.
  Corpus is mixed-county (SLCo, Tooele, Washington) — Phase B filters to Salt Lake County.
- UGRC SGID parcels (opendata.gis.utah.gov / ArcGIS services): free parent-parcel polygons
  by parcel number. To verify access in Phase B.
- City planning commission packets (e.g. cms3.revize.com sites): free PDFs pairing plats
  with staff reports that state zoning — best source for the zoning-research path.
- SLCo Recorder's own recorded-docs portal is $5/token — NOT used (ALL FREE constraint).
