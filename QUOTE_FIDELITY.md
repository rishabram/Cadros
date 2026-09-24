# QUOTE_FIDELITY.md — quote-fidelity pass over Caddy's 51 rules

**Date:** 2026-09-24. **Store:** `rulegraph/verified_rules.json` (canonical 59-rule store, fp `9cc91ac7…`).
**Scope:** the 51 rules with `human_verification.verified_by == "Rohan"` (Caddy's 00:43 drop, via the STORE_VIEW reconstruction `caddy_drop/`, sha `9ec5e8dc…43c803`). Rishab's 8 are out of scope for this pass.
**Corpus:** `~/workspace/neron-zoning/slc_code_M1_OS_PL_MU11.md` (21A.28.020 M-1, 21A.32.100 OS, 21A.32.070 PL, 21A.25.070 MU-11) and `~/workspace/neron-zoning/slc_code_21A25010_use_tables.md` (21A.25.010 general provisions, 21A.33 use tables). Retrieved 2026-09-23 from codelibrary.amlegal.com, 2026 S-21.
**Method:** read-only. Each stored `quote` was compared against the corresponding code passage by a human-eyed wave. No quotes were rewritten. Machine enforcement lives in `rulegraph/quote_fidelity.py` + `rulegraph/test_quote_fidelity.py`: the classification counts and the sha256 of every judged quote are pinned — any quote change fails the suite loudly and forces a re-run of this pass.

## Counts

| Category | Count | Meaning |
|---|---|---|
| VERBATIM | 4 | Stored quote matches the code text exactly |
| VALUE_MATCH | 15 | Values/meaning preserved; wording condensed or rephrased (diffs below) |
| CORPUS_GAP | 32 | Cited section absent from the local corpus — unverifiable-by-us, NOT a failure |
| MISMATCH | 0 | No value-or-meaning differences found |

**Headline: zero MISMATCHes. Every verifiable quote preserves its rule's values and meaning.**

## Relation to the 00:48 gate deep-dive

That run used PASS/REVIEW/FAIL categories over all 59 rules (4 verbatim PASS, 44 REVIEW, 11 FAIL). Mapping to this pass's schema: its 44 REVIEWs split into this pass's 15 VALUE_MATCH + 22 MU-5/MU-6 rules whose quote-vs-params were internally consistent but unverifiable against code text + Rishab's 7 condensed quotes (out of scope here); its 11 FAILs were 10 MU-5/MU-6 corpus-gap cases + M-1-05's dropped-"(a)"-lettering paraphrase. This pass re-homes those: all 32 MU-5/MU-6 rules are CORPUS_GAP (one honest category instead of split across REVIEW/FAIL), and M-1-05 is VALUE_MATCH with the human-eyeball flag carried forward (its value matches; only the sub-item lettering is dropped).

## Per-rule classifications

| rule_id | citation | category |
|---|---|---|
| MU-5-01 | 21A.25.040 (Table 21A.25.040.C.1) | CORPUS_GAP |
| MU-5-02 | 21A.25.040 (Table 21A.25.040.C.1) | CORPUS_GAP |
| MU-5-03 | 21A.25.040 (Table 21A.25.040.C.1) | CORPUS_GAP |
| MU-5-04 | 21A.25.040 (Table 21A.25.040.C.1) | CORPUS_GAP |
| MU-5-05 | 21A.25.040 (Table 21A.25.040.C.2) | CORPUS_GAP |
| MU-5-06 | 21A.25.040 (Table 21A.25.040.C.2) | CORPUS_GAP |
| MU-5-07 | 21A.25.040 (Table 21A.25.040.C.2) | CORPUS_GAP |
| MU-5-08 | 21A.25.040 (Table 21A.25.040.C.2) | CORPUS_GAP |
| MU-5-09 | 21A.25.040 (Table 21A.25.040.C.2) | CORPUS_GAP |
| MU-5-10 | 21A.25.040 (Table 21A.25.040.C.3) | CORPUS_GAP |
| MU-5-11 | 21A.25.040 (Table 21A.25.040.C.3) | CORPUS_GAP |
| MU-5-12 | 21A.25.040 (Table 21A.25.040.C.3) | CORPUS_GAP |
| MU-5-13 | 21A.25.040 (Table 21A.25.040.C.3) | CORPUS_GAP |
| MU-5-14 | 21A.25.040 (Table 21A.25.040.C.3) | CORPUS_GAP |
| MU-5-15 | 21A.25.040 (Table 21A.25.040.C.1) | CORPUS_GAP |
| MU-5-16 | 21A.25.040 | CORPUS_GAP |
| MU-6-01 | 21A.25.050 (Table 21A.25.050.C.1) | CORPUS_GAP |
| MU-6-02 | 21A.25.050 (Table 21A.25.050.C.1) | CORPUS_GAP |
| MU-6-03 | 21A.25.050 (Table 21A.25.050.C.1) | CORPUS_GAP |
| MU-6-04 | 21A.25.050 (Table 21A.25.050.C.1) | CORPUS_GAP |
| MU-6-05 | 21A.25.050 (Table 21A.25.050.C.2) | CORPUS_GAP |
| MU-6-06 | 21A.25.050 (Table 21A.25.050.C.2) | CORPUS_GAP |
| MU-6-07 | 21A.25.050 (Table 21A.25.050.C.2) | CORPUS_GAP |
| MU-6-08 | 21A.25.050 (Table 21A.25.050.C.2) | CORPUS_GAP |
| MU-6-09 | 21A.25.050 (Table 21A.25.050.C.2) | CORPUS_GAP |
| MU-6-10 | 21A.25.050 (Table 21A.25.050.C.3) | CORPUS_GAP |
| MU-6-11 | 21A.25.050 (Table 21A.25.050.C.3) | CORPUS_GAP |
| MU-6-12 | 21A.25.050 (Table 21A.25.050.C.3) | CORPUS_GAP |
| MU-6-13 | 21A.25.050 (Table 21A.25.050.C.3) | CORPUS_GAP |
| MU-6-14 | 21A.25.050 (Table 21A.25.050.C.3) | CORPUS_GAP |
| MU-6-15 | 21A.25.050 (Table 21A.25.050.C.1) | CORPUS_GAP |
| MU-6-16 | 21A.25.050 | CORPUS_GAP |
| MU-11-01 | 21A.25.070 (Table 21A.25.070.C.1) | VALUE_MATCH |
| MU-11-02 | 21A.25.070 (Table 21A.25.070.C.1) | VALUE_MATCH |
| MU-11-03 | 21A.25.070 (Table 21A.25.070.C.1) | VALUE_MATCH |
| MU-11-04 | 21A.25.070 (Table 21A.25.070.C.1) | VALUE_MATCH |
| MU-OPENSPACE-01 | 21A.25.010.D (referenced by every MU district table) | VALUE_MATCH |
| M-1-01 | 21A.28.020.C | VERBATIM |
| M-1-02 | 21A.28.020.D | VERBATIM |
| M-1-03 | 21A.28.020.D.6 | VERBATIM |
| M-1-04 | 21A.28.020.F | VALUE_MATCH |
| M-1-05 | 21A.28.020.F.2 | VALUE_MATCH |
| M-1-06 | 21A.28.020.E | VALUE_MATCH |
| OS-01 | 21A.32.100.C | VERBATIM |
| OS-02 | 21A.32.100.D | VALUE_MATCH |
| OS-03 | 21A.32.100.D.3 | VALUE_MATCH |
| OS-04 | 21A.32.100.E | VALUE_MATCH |
| OS-05 | 21A.32.100.F | VALUE_MATCH |
| PL-01 | 21A.32.070.C | VALUE_MATCH |
| PL-02 | 21A.32.070.D | VALUE_MATCH |
| PL-03 | 21A.32.070.E | VALUE_MATCH |

## CORPUS_GAP detail (32 rules)

All 16 MU-5 rules cite §21A.25.040 and all 16 MU-6 rules cite §21A.25.050. Neither section is present in any `slc_code_*.md` file (verified by grep: zero hits for "21A.25.040" or "21A.25.050" across `~/workspace/neron-zoning/*.md`). These 32 quotes are therefore unverifiable from our side — this is a limitation of our corpus, not evidence of bad quotes. The browser credential is expired (terminal 401), so live re-fetch is unavailable; Caddy's extraction contract Packages A/B cover these sections on his side. When that text lands, this pass must be re-run for these 32 (the pinned counts will force it: any reclassification changes the tally).

## VALUE_MATCH diffs (15 rules)

### MU-11-01 — 21A.25.070 Table C.1
- Code: "Height: 45' max."
- Quote: "Height Maximum: 45 feet."
- Diff: rephrased; value identical (45 ft max).

### MU-11-02 — 21A.25.070 Table C.1
- Code: "Front/Corner Side Yard: 5' min (10' on 300 West, 400 South, 1700 South West Temple–I-15, 2100 South West Temple–I-15); 20' max."
- Quote: "Front and Corner Side Yard Minimum: 5 feet, except as listed below. 1. 10 feet, on the following streets: a. 300 West b. 400 South c. 1700 South, from West Temple to I-15 d. 2100 South, from West Temple to I-15 Maximum: 20 feet."
- Diff: same three values (5 min; 10 on listed streets; 20 max) expanded into enumerated sentences; street list identical.

### MU-11-03 — 21A.25.070 Table C.1
- Code: "Interior Side Yard: 4' min."
- Quote: "Interior Side Yard Minimum: 4 feet."
- Diff: rephrased; value identical (4 ft min).

### MU-11-04 — 21A.25.070 Table C.1
- Code: "Rear Yard: 10' min; 20' min where rear abuts R-1, R-2, FR, SR, FB-UN1, RMF-30, MU-2, or MU-3."
- Quote: "Rear Yard Minimum: 10 feet. When the rear yard abuts an R-1, R-2, FR, SR, FB-UN1, RMF-30, MU-2, or MU-3 zone along the rear lot line, the minimum is 20 feet."
- Diff: expanded to sentences; both values and the full abutter list identical.

### MU-OPENSPACE-01 — 21A.25.010.D
- Code (D.1): "Minimum 10% of lot area as open space (unless chapter says otherwise)."
- Quote: "Open Space Area: A minimum of ten percent (10%) of the lot area shall be provided as open space area, unless otherwise specified in this chapter."
- Diff: rephrased; value identical (10% of lot area).

### M-1-04 — 21A.28.020.F
- Code (F.1): "No building shall exceed sixty five feet (65') except emission-free distillation column structures (up to FAA minimal approach surface elevation or 120' max, whichever is less). AFPP Overlay District development needs Department of Airports approval; over 50' may need FAA site-specific approval."
- Quote: "No building shall exceed sixty five feet (65') except that emission free distillation column structures, necessary for manufacture processing purposes, shall be permitted up to the most restrictive Federal Aviation Administration imposed minimal approach surface elevations, or one hundred twenty feet (120') maximum, whichever is less."
- Diff: same height values (65' general max; distillation-column exception to FAA surface or 120' max, whichever less). "emission free" vs "emission-free" is a hyphenation artifact. **Dropped:** the AFPP Overlay / FAA-approval sentence — out of scope for the max-height rule, but a reader should know it exists.

### M-1-05 — 21A.28.020.F.2
- Code (F.2(a)): "west of SLC International Airport and north of I-80: up to 85' via design review (21A.59)."
- Quote: "West of the Salt Lake City International Airport and north of Interstate 80 (I-80): Buildings may exceed sixty-five feet (65') in height subject to the design review standards and procedures of chapter 21A.59 of this title. In no case shall any building exceed eighty-five feet (85')."
- Diff: same value (85' max via design review) and geography. **Dropped: the "(a)" sub-item lettering** — a reader cannot tell this is sub-item (a) of three location exceptions ((b)/(c) not quoted; citation is F.2). Matching value, weakened provenance precision. **Human eyeball still owed at check-in** (flag carried forward from the 00:48 gate deep-dive).

### M-1-06 — 21A.28.020.E
- Code (E.1–2): "Front And Corner Side Yards: All required front and corner side yards shall be maintained as landscape yards in conformance with chapter 21A.48. Landscape Buffer Yards: All lots abutting a lot in a residential district shall conform to the landscape buffer yard requirements of chapter 21A.48."
- Quote: same, with padding ("in conformance with the requirements of chapter 21A.48 of this title").
- Diff: minor wording padding only. **Dropped:** E.3 (Northwest Quadrant Overlay special landscape requirements per 21A.34.140 B2).

### OS-02 — 21A.32.100.D
- Code (D.1–2,4): ≤4-acre lots 35' max with 1' yard increase per foot over 20'; >4-acre lots 35–45' with 1:1 yard increase per foot over 35'; 45–60' via design review with 1:1 increase over 35'; SLC Public Utilities critical infrastructure exempt.
- Quote: the same values stated in fuller code-style sentences ("Lots four (4) acres or less: Building height shall be limited to thirty five (35) feet; provided that for each foot of height in excess of twenty (20) feet, each required yard and landscaped yard shall be increased one foot…").
- Diff: all numeric values identical. (Here the corpus file's own rendering is the condensed one; the stored quote is closer to full code text.)

### OS-03 — 21A.32.100.D.3
- Code: "Recreation equipment: up to 80' where needed for safe operation (e.g., golf driving-range fences)."
- Quote: "Recreation equipment heights are permitted to a height not to exceed eighty (80) feet when needed due to the nature of the equipment or for the use to operate safely, such as fences surrounding golf course driving ranges."
- Diff: expanded to a full sentence; value (80'), condition, and example identical.

### OS-04 — 21A.32.100.E
- Code (E.1–2): ≤4-acre lots: Front/Corner/Interior/Rear 10'; >4-acre lots: Front/Corner 10', Interior/Rear 15'.
- Quote: same values in enumerated code-style form ("1. Lots Four Acres Or Less: a. Front Yard: Ten feet (10')…").
- Diff: values identical; wording is the fuller code form vs. the corpus file's condensed rendering.

### OS-05 — 21A.32.100.F
- Code: "All required yards maintained as landscaped yards per chapter 21A.48 (excluding authorized accessory buildings/structures)."
- Quote: "All required yards shall be maintained as landscaped yards excluding authorized accessory buildings and structures in conformance with the requirements of chapter 21A.48, 'Landscaping And Buffers', of this title."
- Diff: minor padding plus the chapter's full title; value identical.

### PL-01 — 21A.32.070.C
- Code (Table C): "Public schools: 5 acres min area, 150 feet min width. Other permitted uses: 20,000 square feet min area, 75 feet min width."
- Quote: "Land Use Minimum Lot Area Minimum Lot Width | Public schools | 5 acres | 150 feet | | Other permitted uses | 20,000 square feet | 75 feet |"
- Diff: pipe-transcription of the same table; values identical.

### PL-02 — 21A.32.070.D
- Code (D.1–3): listed civic/entertainment uses 75' (or abutting district's greater standard); K-12 public schools 125'; other uses 35'.
- Quote: same ("prison or jail" vs "prison/jail", "75 feet" vs "75'").
- Diff: trivial wording; values identical.

### PL-03 — 21A.32.070.E
- Code (E.1–2): K-12 public schools: front/corner 30', interior/rear 50' next to residential/manufacturing else 30' (setbacks on site perimeter + shared lines); other uses 30/30/20/30.
- Quote: same values in sentences, including the multi-parcel site-perimeter rule.
- Diff: values identical. **Dropped:** E.3 (accessory buildings/structures in yards per 21A.36.020).

## MISMATCH rows

None. (The MISMATCH category also fires if any judged quote changes or any verifiable rule lacks a manual judgment — see `rulegraph/quote_fidelity.py`. Both force a human-eyed re-pass, never silent auto-reclassification.)

## Reproducibility

```bash
cd ~/workspace/neron-scratch
venv/bin/python -m unittest rulegraph.test_quote_fidelity -v
venv/bin/python -c "from rulegraph.quote_fidelity import classify, counts; print(counts(classify()))"
# expected: {'VERBATIM': 4, 'VALUE_MATCH': 15, 'CORPUS_GAP': 32, 'MISMATCH': 0}
```
