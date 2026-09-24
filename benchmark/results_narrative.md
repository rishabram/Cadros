## GreenRush swing (2026-09-24, greenfield-only follow-up)

10 new candidates researched (Herriman ×2, Riverton ×1, Saratoga Springs ×4, South Jordan ×3; plus revisits of Swaner/Mill/Village at the Boulders). **0 newly scoreable.** Scored set remains 0/16 researched; pass rate undefined.

**Firm corpus-gap finding.** No free source co-locates all five required inputs (parent polygon, approved lot count, approval confirmed, approval-date zoning, road_width_ft) for any greenfield plat. Two structural blockers, both policy-hardened as gaps (never fills):
1. **Parent polygon** — needs either UGRC SGID parcel-union REST (not attempted: browser fetch terminal this turn, exec web access prohibited by standing rules) or a fetchable plat PDF with full metes-and-bounds text (only Mill has one, and it is non-greenfield commercial).
2. **road_width_ft** — needs a citable city engineering standard drawing. Searchable text yields only other cities' codes (e.g., River Heights Title 11 Ch 7: 66' collector / 50' local; SLC staff reports referencing a 50' public-street baseline). No Herriman/Riverton/South Jordan/SLC local-street standard found in citable form.

Nearest misses: Cove at Silver Sky (Herriman R-1-10, Tier-2 params sourced, but preliminary-only with no lot count/geometry); Broadbent Subdivision (Herriman, 22 lots, M&B in plat PDF but PDF not fetchable); Hidden Pines (Riverton, 42 lots final-approved, zoning + geometry unsourced). Recommended next unlock: UGRC SGID parcel polygons for parent reconstruction + official engineering standard drawings for road width. Full candidate records in `plats.json` (`research_candidates_not_scored`).

## UGRC swing (2026-09-24 ~02:21 MDT, ParcelScout) — unexecuted: tool outage

The swing targeted the two named unlocks for the three nearest misses (Cove at Silver
Sky, Broadbent Subdivision, Hidden Pines): (1) UGRC SGID parcel-union REST for parent
polygons, (2) citable Herriman/Riverton/South Jordan engineering standard drawings for
road_width_ft, plus a retry of the Broadbent PMN PDF fetch (1015940.pdf).

**Not attempted on merits.** Both browser tools were terminally unavailable this turn:
`browser_search` upstream unavailable after 3 attempts (retry exhausted; instructed not
to call again), and `browser_open` upstream unavailable after 3 attempts (retry
exhausted; no exec/curl/invented-endpoint reproduction permitted). `browser_open` is
additionally restricted to exact conversation URLs, and no UGRC SGID endpoint URL was
ever tool-returned, so the REST query URL could not be constructed (URL construction
prohibited). The Broadbent PDF retry and the Cove agenda fetch failed on the same
outage. Zero scoring inputs changed; scored set remains 0/16.

**Recommendation:** retry the UGRC SGID parcel-polygon leg (query parent parcel IDs /
point-in-polygon at the three nearest-miss locations; confirm final recording via the
current parcel fabric) and the city standard-drawings leg in a future swing when browser
tools are healthy. The two unlocks stand as named in the corpus-gap finding.

## UGRC swing RETRY (2026-09-24 ~02:30–02:45 MDT, UGRCScout) — endpoint confirmed, scored set 0/16

Browser tools were healthy this turn. The UGRC SGID parcel-polygon leg was executed
against live data.

**Endpoint confirmed (tool-returned).** Via the GitHub commit diff
nache327/stack-land-acquisition@1680170 (opened verbatim from search results):
county-specific FeatureServers —
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Parcels_SaltLake/FeatureServer/0`.
Anonymous querying works (`allowAnonymousToQuery: true`, `maxRecordCount: 2000`).

**Key refinement — BASIC parcels only.** The open service is the HB113 basic-parcel
layer. Verified field list: OBJECTID, FIPS, PARCEL_ID, PARCEL_ADD, PARCEL_CITY,
PARCEL_ZIP, OWN_TYPE, RECORDER, ParcelsCur/Rec/Pub, ParcelYear, ParcelNotes,
CoParcel_URL, ACCOUNT_NUM, Shape__Area, Shape__Length. There is NO SUBDIV_NAME and
no LIR/tax-roll attributes (the service description states those require county
recorder contact). Consequence: open-SGID parcels **cannot** filter by subdivision
name; parent retrieval needs a known PARCEL_ID (direct polygon) or a
spatial/address-pattern query.

**Proven on live data.**
- Village at the Boulders Phase 3 parent `33083510770000`: ABSENT from the 2026
  fabric (query `PARCEL_ID LIKE '3308351%'` returned the subdivided neighborhood
  fabric instead). Consistent with its 2018 recording — recorded plats need
  child-parcel union reconstruction, not parent lookup.
- Broadbent (Herriman) recording check: inconclusive. No large unsubdivided
  parcel at ~6400 W 13800 S; the only large parcel on 13800 S in Herriman is
  `33064080010000` at 4257 W 13800 S (68,021 sqm / ~16.8 ac — not the Broadbent
  site). Address-format uncertainty remains; not resolved.

**Not executed.** Broadbent PMN PDF retry (`1015940.pdf`) failed — `browser_open`
went terminal for the turn (developer instruction: no further calls). The city
engineering standard-drawings leg (road_width_ft) is unexecuted.

**Outcome.** Scored set remains 0/16; no plat scored — all three nearest misses
lack non-geometry inputs UGRC cannot supply (Cove: preliminary-only, no lot
count; Broadbent: final approval unconfirmed; Hidden Pines: zoning district
unsourced). **Corpus-gap finding refined:** the parent-polygon blocker is SOLVABLE
via the UGRC method (known parcel ID → direct polygon; recorded plat → child
union by ID prefix/address pattern). The binding constraints are now
approval-date zoning district + `road_width_ft` for every candidate.

## GreenRush-2 RETRY (2026-09-24 ~10:05–16:30 MDT, browser leg) — road standards closed, scored set 0/16

Browser tools healthy this turn (search + open both returned). Priorities executed:
(1) official road-width standards for Herriman, Riverton, South Jordan; (2) Broadbent PMN
PDF `1015940.pdf`; (3) approval-date zoning for Hidden Pines and nearest misses.

**Road-width blocker CLOSED for all three target cities** (citable local/residential
pavement widths; see `research_notes.md` H1–H3):
- Herriman RD-01B/RD-01C: 60' ROW → **32 ft asphalt**; 53' ROW → **28 ft asphalt**
  (`https://herriman-website-files.s3.us-west-1.amazonaws.com/Engineering_Standards/02-RD.pdf`).
- Riverton Standard Specifications and Plans Manual (2021-09-29): local street = 54' ROW /
  **29 ft pavement** (`https://cms8.revize.com/revize/rivertonut/departments/public-works/engineering/documents/standard-specifications-and-plans.pdf`).
- South Jordan Standard Drawings S-1 "Road Widths and Border Areas" (p.90, scanned drawing
  visually verified): 55' ROW residential → **28 ft of road surface**
  (`https://sjc.utah.gov/DocumentCenter/View/514/Standard-Drawings-PDF`).
- Remaining step is per-plat: match each plat's actual ROW/classification before assigning
  `road_width_ft`. No plat has been assigned a value yet.

**Hidden Pines:** final approval now strongly sourced (Riverton PC minutes 2019-06-27,
PMN `529031.pdf`: PLZ-19-1003, 42 lots, 3814 W 13800 S, unanimous approval; 100%
warranty-bond release approved 2021-09-21, developer Cazco Enterprises, LLC, project
7212). **Approval-date zoning district still unsourced** after minutes, geotech report,
and bond-record legs (see `research_notes.md` H4). Riverton 29-ft local candidate
conditional on street classification. Parent parcel/polygon still unknown.

**Broadbent:** PMN `1015940.pdf` is **CONFIRMED DEAD** (315-byte HTML 404, not a PDF).
No replacement document or final-approval record found (see `research_notes.md` H5).
Previous claim of M&B in the plat PDF downgraded to unsourced.

**Cove at Silver Sky:** R-1-10 params sourced; Herriman road standard now sourced but
plat ROW unknown; final approval + lot count still gaps.

**Outcome.** Scored set remains **0/16** — accuracy rate undefined (not 0%). The
road-width unlock is banked as official, citable standards; the binding constraints are
now: (a) approval-date zoning district for every candidate, (b) parent polygons/geometry,
(c) final-approval records (Broadbent, Cove). Recommended next unlock: plat-specific
documents (recorded plats name the zone) via Herriman PrimeGov / Riverton Granicus /
SLCo recorder research, and UGRC child-parcel union reconstruction at confirmed site
coordinates.

## GreenRush-6 (2026-09-24) — FIRST SCORED PLAT: Tripp Lane Subdivision, Murray

**Scored set: 1/1. NERON estimated 9 lots vs 12 approved — relative error 25%, outside the ±15% tolerance. Pass rate 0%.** This is the benchmark's first scored comparison and it is an honest miss, not a pipeline defect to tune away.

**Candidate.** Tripp Lane Subdivision, 871 W Tripp Lane, Murray UT. Preliminary approval 2022-11-17 (5–1; murray.utah.gov/Archive/ViewFile/Item/7396): 12 lots + public cul-de-sac street on a vacant 2.78-ac parcel, R-1-6. Final approval 2023-04-06, project 22-088 (6–0; utah.gov/pmn/files/991087.pdf): frontage deficiency on Lot 7 corrected, ROW widened to Murray's 49-ft standard, all R-1-6 requirements met.

**Inputs (all four dims known, all cited):**
- Approval-date district R-1-6 (final minutes: "the property was in R-1-6"; "R-1-6 zone requires 6,000 sq ft per lot").
- min_lot_area_sqft = 6,000 (final minutes, source-precedence-3 approving-body record; direct Ch. 17.96 code text unretrieved — API Cloudflare-blocked).
- min_frontage_ft = 60 (preliminary minutes: Lot 7 "required 60' lot width at the 20' setback line"; final minutes call it "lot frontage"; width-as-proxy documented).
- road_width_ft = 49 (Murray Code §16.16.180: all streets minimum 49-ft width / 25-ft asphalt; approval conditioned the public ROW to 49 ft; the pipeline's road band = the dedicated corridor, not the pavement).
- Parent geometry: concave-hull (ratio 0.5) reconstruction from the 13 child parcels (12 lots + Parcel A, 5762–5846 S Tripp Lane), 2.787 ac vs official 2.78 ac (0.3% diff). The raw child union (2.155 ac) excludes the dedicated street; the hull fills it deterministically.

**Result.** 24 candidates evaluated, 8 schemes kept; top scheme: N–S spine road (the real orientation), 75-ft module, 9 conforming lots. The real plat fit 12 — human design used the cul-de-sac bulb and adapted widths, which the pipeline's rigid grid cannot replicate. Sensitivity check: road_width 25 ft → 11 lots (inside tolerance), but 25 ft is the pavement, not the dedicated corridor, so 49 ft stands; the input was chosen on principle, not tuned to the score.

**Reading.** The benchmark now has a real, scored, failing comparison. The product under-yields on narrow cul-de-sac sites with human-optimized lot arrangements — a genuine product gap to close, not a data problem. Next: add more scored plats (target ~10) before drawing conclusions about the tolerance target.

## GreenRush-8 (2026-09-24) — Cove at Silver Sky: confirmed built, document-blocked

**Scored set remains 1/16 (Tripp Lane only).** GreenRush-8 expanded beyond Murray per the GR7 carry-forward. Best lead was Cove at Silver Sky (Herriman S2023-113, R-1-10, 11.75 ac @ ~12754 S 6200 W):

- **Confirmed built:** 2025–2026 MLS new-construction listings name "COVE AT SILVER SKY" (Silver Sky Dr / Harlow Ann Way, lots 0.21–0.25 ac). The final plat was administratively approved by Herriman Engineering (no PC/Council action — per Herriman process) and recorded ~2024.
- **Geometry leg executed:** 34 current child parcels union to ~11.65 ac vs the official 11.75 ac (0.9% diff) — but parcel-ID blocks differ across clusters (multiple phases/recordings likely) and the open UGRC service carries no subdivision names, so membership is NOT provable to benchmark standard. No parent GeoJSON built (GR5 Swaner lesson).
- **Binding gaps (document, not research):** approved lot count has no official source (the 3-20-24 staff report PDF was unreachable — browser outage this turn); plat ROW unassigned between Herriman RD-01B (32 ft) and RD-01C (28 ft); R-1-10 Tier-2 params await context confirmation.
- Broadbent (Herriman) re-check: still no final approval. Riverton's recent docket is infill-scale.

**Next unlock (concrete):** fetch the 3-20-24 Item 4.2 staff report (Herriman S3 bucket, URL in the 2024-03-20 PC agenda) or the 2024 recorded plat from the SLCo Recorder. Either names lot count + ROW + zone and unlocks the second scored plat. Cove at Silver Sky is the prime target for the next lane with working browser access.

## GreenRush-9 (2026-09-24) — Cove document gate: failed, firmly blocked

**Scored set remains 1/16 (Tripp Lane only).** The exact staff-report URL was recovered from the PMN agenda PDF (`.../3-20-24/Item+4.2++Staff+Report.pdf`) but the S3 bucket returns 403 AccessDenied on all objects — a policy lock, not a bad URL. No Wayback snapshot; the 2024-03-20 PC meeting predates Herriman's PrimeGov usage; no web mirror; no recorded-plat result in search. Pivot attempt (Hollys Pond Ph 2, S2024-102) also document-blocked — the official agenda's S3 links point to a nonexistent bucket. The March 2024 Herriman PC staff reports are unrecoverable through public channels; the remaining paths (recorder visit, GRAMA) need a human. Next lanes: stop retrying Cove recovery; gate on a *reachable* staff report or recorded plat (PrimeGov item attachments, 2024–2026 meetings) before any geometry work.

## GreenRush-11 (2026-09-24) — SECOND SCORED PLAT: Daybreak Village 12B Plat 1, South Jordan

**Scored set now 2/17 (Tripp Lane + Daybreak V12B Plat 1). Pass rate 0/2 within ±15%.**

**Candidate.** Daybreak Village 12B Plat 1, South Jordan (PLPP202400077), "Generally 7050 West 11350 South." Preliminary approval 2024-08-13, 4–0 (South Jordan PC minutes item H.1; https://www.utah.gov/pmn/files/1160983.pdf): 61 single-family lots + 5 park lots on 14.306 ac, P-C zone. Lot sizes 2,671–10,867 sqft, avg 6,094 (staff report). This is the first P-C (planned community) scored plat — dimensional control comes from the village-specific adopted Design Guidelines attached to the staff-report packet, not the base city code.

**Inputs (all document-backed).**
- Parent geometry: DIRECT parent parcel 26221030210000 from UGRC/SLCo Parcels_SaltLake FeatureServer — still current (preliminary approval only; final plat not yet parcelized as of 2026-09-24). Geodesic 14.253 ac vs official 14.306 ac = 0.37% difference — PASSES the 5% gate. No child-union reconstruction needed.
- min_frontage_ft = 30: Design Guidelines SMALL LOT product, "Min. 30', Max. 70' lot frontage" (quoted). Small Lot is the binding most-permissive detached product present in the plat (approved lots down to 2,671 sqft; plat-figure lots 101–125 read 2,100–7,325 sqft).
- min_lot_area_sqft = 1,500: DERIVED and documented as such — Small Lot states "Min. 30' lot frontage" and "Min. 50' lot depth" (guidelines state frontage/depth, not area); 30×50 = 1,500 sqft theoretical minimum compliant Small Lot. The designer built above the minimum (smallest approved 2,671 sqft); the pipeline estimates max yield under stated minimums.
- road_width_ft = 28: South Jordan Standard Drawings S-1, "55-FOOT R.O.W. RESIDENTIAL — 28' OF ROAD SURFACE."

**Result.** 8 schemes; top-ranked: **76 lots vs 61 approved = 24.6% over, outside ±15%.** Scheme envelope: 76/73/64/62/60/59/57/49. The envelope BRACKETS the approved 61 — schemes at 59, 60, 62 lots sit inside tolerance — but the max-yield ranker selects scheme_00 (76).

**Reading.** The mirror image of Tripp Lane. There NERON under-yielded on a tight cul-de-sac site (9 vs 12); here it over-yields on a mixed-product P-C plat (76 vs 61) because the pipeline optimizes lot count under the most permissive product's minimums while the human designer mixed Small/Standard/Large products (avg 6,094 sqft vs the 1,500 sqft minimum) for market and urbanism reasons. Critically, the generator CAN produce realistic schemes (59–62 lots exist in the envelope) — the gap is in RANKING, not generation. The product question this raises: should the ranker prefer max yield, or model designer-like product-mix behavior? For P-C zones with multi-product guidelines, a single-product minimum input structurally overestimates. Next: score V12B Plat 3 (30 lots, same guidelines) to test whether the over-yield pattern replicates on a smaller sibling plat.

## GR-14B2 (2026-09-24) — THIRD SCORED PLAT: Taylorsville Fields Subdivision (final plat RECORDED)

**Scored set now 3/17 (Tripp Lane + Daybreak V12B Plat 1 + Fields). Pass rate 0/3 within ±15%.**

**Candidate.** Fields Subdivision, Taylorsville (File #4S22/SUB-000226-2022), 4768 S 1175 W. FINAL PLAT RECORDED (genealogy-confirmed: parent 21111020270000 retired; children 21111020370000/21111020380000 match approved dims at 0.00%). Approved: 2 lots — Lot 1: 21,139 sqft (existing SF home, retained); Lot 2: 10,263 sqft (proposed). R-1-10 (rezoned from R-1-15 in 2017). Applicant Nancy Fields; preliminary staff-recommended 2022-06-07, PC 2022-06-14.

**Inputs (all document-backed, unchanged from the GR-14 triage — blind re-run).**
- Parent geometry: deterministic shapely child-union, 31,434.3 sqft = 0.7216 ac vs official 0.72 ac (0.22%) — cleanest parent in the benchmark.
- min_lot_area_sqft = 10,000: staff report quoting code (approval-date); cross-checks rulegraph Taylorsville R-1-10 = 10,000 (LDC Sec. 13.04.020) — pack and benchmark agree.
- min_frontage_ft = 80: staff report "Min lot width: 80 ft" used as frontage proxy per benchmark policy (Tripp Lane precedent). Note: the rule pack has an evidenced absence of a numeric R-1 lot-width standard — benchmark used approval-record sourcing.
- road_width_ft = 50: Taylorsville LDC Sec. 13.21.100 local ROW (rule pack). Fields has no new dedicated street; kept at the code value per the cross-lane consistency directive — the pipeline's lot-split path does not consume it.

**Result.** 3 schemes, all from the new lot-split family (DW-GEOM2, commits 27dcff4/bde99e9); street-based strategies yielded nothing as in triage. Top-ranked: **3 lots vs 2 approved = +50.0%, outside ±15%.** Envelope: 3 / 2 / 2 (split-short-3, split-short-2, split-long-2). The envelope CONTAINS the approved 2-lot form — the margin-based ranker selected the 3-lot max-yield scheme (margin 0.5368 vs 0.3053).

**Reading.** A RANKING miss, the small-infill twin of Daybreak 12B Plat 1: generation now covers the no-new-street form (the GR-14 generator-gate failure is resolved), but the ranker still optimizes lot count/margin while the human designer split around a retained home (21,139 sqft kept as-is; 10,263 sqft carved as the new lot). The pipeline's equal-strip splits cannot express "keep the existing house lot whole" — that condition is recorded as an inputs note, not the driver: the count miss is ranking, not geometry. This is the second independent replication of the accuracy-directive #5 finding (product-mix prior over max-yield ranking), now at 2-lot infill scale. Family-maturity note for D-Wade: the R-5 street-connectivity validation misfires on no-new-street schemes (checks_fail=1 on all three split schemes) — harmless to ranking today, but the check should be split-aware. Funnel KPI: DISCOVERED→SCOREABLE = 5.77 h.
