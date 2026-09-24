"""Quote-fidelity pass over Caddy's 51 rules (the 59-rule canonical store minus
Rishab's 8, identified by human_verification.verified_by).

Read-only evidence: this module CLASSIFIES stored quotes against the local
corpus; it never rewrites quotes. Categories:

  VERBATIM    - stored quote matches the code text exactly (modulo the
                section-header prefix, which quotes omit by convention).
  VALUE_MATCH - values and meaning preserved; wording condensed or rephrased.
                The diff note records exactly what differs.
  CORPUS_GAP  - the cited section is absent from the local corpus
                (~/workspace/neron-zoning/slc_code_*.md). Unverifiable-by-us,
                NOT a failure.
  MISMATCH    - value or meaning differs from the code text. Findings only;
                never silently "fixed".

Corpus coverage (2026-09-24):
  slc_code_M1_OS_PL_MU11.md      -> 21A.28.020 (M-1), 21A.32.100 (OS),
                                    21A.32.070 (PL), 21A.25.070 (MU-11)
  slc_code_21A25010_use_tables.md -> 21A.25.010 (MU general provisions),
                                    21A.33.040 / 21A.33.070 (use tables)
  ABSENT: 21A.25.040 (MU-5), 21A.25.050 (MU-6) -> 32 CORPUS_GAP rules.
  The browser credential is expired (terminal 401); live re-fetch is
  unavailable, so corpus gaps stay gaps until Caddy's extraction lands.

The MANUAL table pins each verifiable rule's classification AND the sha256
of the quote it was judged against. If any quote changes, the test fails
loudly and the pass must be re-run by a human-eyed wave -- never auto-
reclassified.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

STORE_PATH = Path(__file__).with_name("verified_rules.json")

# section -> corpus file that carries its text
CORPUS_SECTIONS = {
    "21A.25.010": "slc_code_21A25010_use_tables.md",
    "21A.25.070": "slc_code_M1_OS_PL_MU11.md",
    "21A.28.020": "slc_code_M1_OS_PL_MU11.md",
    "21A.32.070": "slc_code_M1_OS_PL_MU11.md",
    "21A.32.100": "slc_code_M1_OS_PL_MU11.md",
}

# rule_id -> (category, quote_sha256[:16], diff note)
# Diff notes quote the material difference for every VALUE_MATCH row.
MANUAL = {
    "MU-11-01": ("VALUE_MATCH", "1a10904cdcbd353b",
        "Code: 'Height: 45' max.' (Table C.1 Row House). Quote rephrases as "
        "'Height Maximum: 45 feet.' Value identical (45 ft max)."),
    "MU-11-02": ("VALUE_MATCH", "b90f8d3f0d51fbb8",
        "Code: 'Front/Corner Side Yard: 5' min (10' on 300 West, 400 South, "
        "1700 South West Temple-I-15, 2100 South West Temple-I-15); 20' max.' "
        "Quote expands the same three values (5 min; 10 on listed streets; "
        "20 max) into enumerated sentences. Values identical."),
    "MU-11-03": ("VALUE_MATCH", "8953eb1af9e77f7a",
        "Code: 'Interior Side Yard: 4' min.' Quote: 'Interior Side Yard "
        "Minimum: 4 feet.' Value identical (4 ft min)."),
    "MU-11-04": ("VALUE_MATCH", "422ce58c4f01f405",
        "Code: 'Rear Yard: 10' min; 20' min where rear abuts R-1, R-2, FR, SR, "
        "FB-UN1, RMF-30, MU-2, or MU-3.' Quote expands to sentences with the "
        "same two values and the same abutter list. Values identical."),
    "MU-OPENSPACE-01": ("VALUE_MATCH", "c63fe580bd46f81c",
        "Code 21A.25.010.D.1: 'Minimum 10% of lot area as open space (unless "
        "chapter says otherwise).' Quote: 'A minimum of ten percent (10%) of "
        "the lot area shall be provided as open space area, unless otherwise "
        "specified in this chapter.' Value identical (10% of lot area)."),
    "M-1-01": ("VERBATIM", "11dc9178ed55ada9",
        "Matches 21A.28.020.C.1-3 exactly (quote omits the 'C. Minimum Lot "
        "Size:' header by convention)."),
    "M-1-02": ("VERBATIM", "0e1461101a8cde19",
        "Matches 21A.28.020.D.1-4 exactly."),
    "M-1-03": ("VERBATIM", "d814a800213c2031",
        "Matches 21A.28.020.D.6 exactly, header included."),
    "M-1-04": ("VALUE_MATCH", "d8d0eacac856c0c3",
        "Code F.1: 65' max; distillation-column exception up to FAA minimal "
        "approach surface or 120' max, whichever less. Quote states the same "
        "values in fuller code-style sentences ('emission free' vs "
        "code-rendered 'emission-free' is a hyphenation artifact). Quote "
        "DROPS the AFPP Overlay / FAA-approval sentence of F.1 -- out of "
        "scope for the max-height rule, but a reader should know it exists."),
    "M-1-05": ("VALUE_MATCH", "bcefcd8729d8cfa5",
        "Code F.2(a): west of SLC Intl Airport and north of I-80, up to 85' "
        "via design review (21A.59). Quote states the same value and "
        "geography but DROPS the '(a)' sub-item lettering, so a reader "
        "cannot tell it is sub-item (a) of three location exceptions (b)/(c) "
        "are not quoted; citation is F.2). Matching value, weakened "
        "provenance precision -- human eyeball still owed at check-in (flag "
        "carried forward from the 00:48 gate deep-dive)."),
    "M-1-06": ("VALUE_MATCH", "e21c3cba7f3bb480",
        "Code E.1-2: front/corner-side yards as landscape yards per Ch. "
        "21A.48; buffer yards where abutting residential. Quote matches with "
        "minor padding ('in conformance with the requirements of chapter "
        "21A.48 of this title' vs 'in conformance with chapter 21A.48'). "
        "Quote DROPS E.3 (Northwest Quadrant Overlay special landscape "
        "requirements)."),
    "OS-01": ("VERBATIM", "e5c2f311c4fb0956",
        "Matches 21A.32.100.C exactly ('C. Minimum Lot Area And Lot Width: "
        "None required.')."),
    "OS-02": ("VALUE_MATCH", "ad3d55a7501a4b17",
        "Code D.1-2,4: <=4ac lots 35' max with 1' yard increase per foot over "
        "20'; >4ac lots 35-45' with 1:1 yard increase over 35', 45-60' via "
        "design review with 1:1 over 35'; SLC Public Utilities critical "
        "infrastructure exempt. Quote states the same values in fuller "
        "code-style sentences. All numeric values identical. (The corpus "
        "file's own rendering is the condensed one here; the quote is closer "
        "to full code text.)"),
    "OS-03": ("VALUE_MATCH", "4942ca395913b444",
        "Code D.3: recreation equipment up to 80' where needed for safe "
        "operation (e.g. golf driving-range fences). Quote expands to a full "
        "sentence with the same value, condition, and example."),
    "OS-04": ("VALUE_MATCH", "34dd581843bcc24a",
        "Code E.1-2: <=4ac lots 10' all yards; >4ac lots front/corner 10', "
        "interior/rear 15'. Quote states the same values in enumerated "
        "code-style form. Values identical."),
    "OS-05": ("VALUE_MATCH", "bc6bfaa7a0161973",
        "Code F: all required yards as landscaped yards per Ch. 21A.48 "
        "(excluding authorized accessory buildings/structures). Quote "
        "matches with minor padding plus the chapter's full title "
        "('Landscaping And Buffers'). Value identical."),
    "PL-01": ("VALUE_MATCH", "5c31de28b3ce2ffb",
        "Code Table 21A.32.070.C: public schools 5ac / 150' width; other "
        "permitted uses 20,000 sqft / 75' width. Quote is a pipe-transcription "
        "of the same table with identical values."),
    "PL-02": ("VALUE_MATCH", "4b9ff92e980775b4",
        "Code D.1-3: listed civic/entertainment uses 75' (or abutting "
        "district's greater standard); K-12 public schools 125'; other uses "
        "35'. Quote matches ('prison or jail' vs 'prison/jail', '75 feet' vs "
        "'75''). Values identical."),
    "PL-03": ("VALUE_MATCH", "bbf2fd4c26ac36cb",
        "Code E.1-2: K-12 public schools front/corner 30', interior/rear 50' "
        "next to residential/manufacturing else 30' (setbacks on site "
        "perimeter + shared lines); other uses 30/30/20/30. Quote states the "
        "same values in sentences. Quote DROPS E.3 (accessory "
        "buildings/structures in yards per 21A.36.020)."),
}

CADDY_RULE_COUNT = 51  # 59-rule store minus Rishab's 8 (by verified_by)
EXPECTED_COUNTS = {
    "VERBATIM": 4,
    "VALUE_MATCH": 15,
    "CORPUS_GAP": 32,
    "MISMATCH": 0,
}

_SECTION_RE = re.compile(r"21A\.\d+\.\d+")


def _section_of(citation: str) -> str | None:
    m = _SECTION_RE.search(citation or "")
    return m.group(0) if m else None


def classify(store_path: Path = STORE_PATH) -> list[dict]:
    """Classify each of Caddy's 51 rules. Returns one dict per rule:
    {rule_id, citation, category, detail}."""
    store = json.loads(store_path.read_text())
    out = []
    for rule in store["rules"]:
        hv = rule.get("human_verification", {})
        if hv.get("verified_by") == "Rishab":
            continue  # Rishab's 8 are out of scope for this pass
        rid = rule["rule_id"]
        section = _section_of(rule.get("citation", ""))
        if section not in CORPUS_SECTIONS:
            out.append({
                "rule_id": rid,
                "citation": rule.get("citation", ""),
                "category": "CORPUS_GAP",
                "detail": (
                    f"Cited section {section} is absent from the local corpus "
                    f"(no slc_code_*.md carries it). Unverifiable-by-us, not "
                    f"a failure. Live re-fetch unavailable (browser credential "
                    f"expired); covered by Caddy's extraction Packages A/B."
                ),
            })
            continue
        if rid not in MANUAL:
            out.append({
                "rule_id": rid,
                "citation": rule.get("citation", ""),
                "category": "MISMATCH",
                "detail": (
                    "UNCLASSIFIED: verifiable section but no manual judgment "
                    "recorded -- the pass must be extended by a human-eyed "
                    "wave before this rule can be trusted."
                ),
            })
            continue
        category, pinned_sha, note = MANUAL[rid]
        actual_sha = hashlib.sha256(rule["quote"].encode()).hexdigest()[:16]
        if actual_sha != pinned_sha:
            out.append({
                "rule_id": rid,
                "citation": rule.get("citation", ""),
                "category": "MISMATCH",
                "detail": (
                    f"QUOTE CHANGED since the manual pass (pinned "
                    f"{pinned_sha}, now {actual_sha}). Re-run the "
                    f"quote-fidelity wave; do not auto-reclassify."
                ),
            })
            continue
        out.append({
            "rule_id": rid,
            "citation": rule.get("citation", ""),
            "category": category,
            "detail": note,
        })
    return out


def counts(results: list[dict]) -> dict:
    tally: dict[str, int] = {
        "VERBATIM": 0, "VALUE_MATCH": 0, "CORPUS_GAP": 0, "MISMATCH": 0}
    for r in results:
        tally[r["category"]] = tally.get(r["category"], 0) + 1
    return tally
