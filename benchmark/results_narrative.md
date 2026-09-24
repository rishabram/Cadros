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
