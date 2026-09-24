# mu_pack marker-stripping audit

Date: 2026-09-24. Auditor: D-Wade wave worker. Scope: `useallow/mu_pack.py::_extract_footnote_markers`
(superscript digits, parenthesized/bracketed digit groups, glued trailing digits) —
confirm no REAL MU use name legitimately carries a digit group the stripper would remove.

## 1. §21A.33.030 — CORPUS GAP (unverifiable-by-us, NOT a pass)

The §21A.33.030 section ("Table of Permitted and Conditional Uses — Mixed Use
Districts", the source of the 322 MU use names) is **absent from the local corpus**:
`~/workspace/neron-zoning/` holds §21A.25.010 (MU general provisions + use tables),
§21A.33.040 (M-1), §21A.33.070 (OS/PL), and district sections — but no §21A.33.030
file. A prior worker (`mu11_4cell_check.md`, 2026-09-24) attempted a live fetch and
could not retrieve it (browser route unhealthy; node IDs not guessable).

**Owner:** Caddy's lane — he performed the original §21A.33.030 extraction that
produced `verified_uses_mu.json`; a re-read for marker notation is folded into his
browser work. Fallback owner: Rishab (browser-credential refresh is a human step).

## 2. What was checked (all against the real 322-name source)

`caddy_drop/verified_uses_mu.json` (Caddy's extraction, 322 names: MU-5 106,
MU-6 105, MU-11 111) was run through the actual `_extract_footnote_markers`:

- **0 of 322 names altered** — every name returns `(name, [])` unchanged;
  the pack fingerprint pin `bf741fd2…` reproduces on disk.
  Command: `venv/bin/python -c` loop over all names asserting
  `_extract_footnote_markers(name.strip()) == (name.strip(), [])` (0 failures).
- **Digit-bearing name class:** exactly 4 rows carry digits — `K-12 Private`
  (×2) and `K-12 Public` (×2), mid-name hyphenated digits. Verified pass-through
  unchanged: no trailing glued digit run, no parenthesized/bracketed group,
  no unicode superscripts. Digits that are part of a real name are safe.
- **Real corpus footnote notation:** our own corpus files render use-table
  footnotes as letter-prefixed groups (`Brewpub (P6,10)`, `Accessory use (P21)` —
  12+ examples in `slc_code_21A25010_use_tables.md`). **0 of 322 MU names carry
  this pattern**, so nothing real is damaged.
- **No-damage verdict:** no real MU use name in the source is damaged by any of
  the four stripper patterns. The false-positive class (stripper removes digits
  that are part of a name) is empty on the current source.

## 3. Follow-up DONE — letter-prefixed markers (2026-09-24, mu_pack lane wave)

The recommended PROPOSED item above was executed in a single wave with the
required name-safety review FIRST. `_extract_footnote_markers` now also
strips the corpus's own letter-prefixed notation:
`_LETTER_PREFIXED_RE = r"\(\s*([PC])\s*(\d[\d\s,]*)\s*\)"` —
"Brewpub (P6,10)" → ("Brewpub", [6, 10]); "Accessory use (P21)" → [21];
"Shop (C2)" → [2]. The P/C column letter is dropped; only digits become
footnotes; matched markers route to MANUAL_REVIEW via `row.footnotes`
(never silently dropped). Pattern runs BEFORE the plain digit-group
pattern so "(P6,10)" can't partially match mid-name.

Name-safety review (executed against the real 322-name source before
shipping, in a throwaway script — all counts from
`caddy_drop/verified_uses_mu.json`):

- Digit-bearing names in the source: **exactly 4** — `K-12 Private` (×2),
  `K-12 Public` (×2), all mid-name hyphenated digits. None are
  parenthesized letter+digit groups → untouched by the new pattern.
- Parenthesized names: 59, all parenthetical WORDS ("(large)", "(ADU)",
  "(indoor, outdoor)"). The new pattern requires a P/C letter followed
  by digits, so `(ADU)` and `(large)` do not match.
- New-pattern matches on the 322-name source: **0 (both the narrow P/C
  pattern and a broader any-letter pattern)** — zero real-name damage.
- Narrow-choice recorded: the pattern is P/C-only and case-sensitive.
  A broader letter set risks over-stripping real future names (e.g.
  "Building (Grade A2)"); lowercase "(p6)" is left as a false negative,
  which is the safe direction (passes through clean, never mis-stripped).

Regression tests added (`useallow/test_mu_pack.py`):
`test_letter_prefixed_markers` (strip + P/C-letter drop + coexistence
with parenthetical words + lowercase/ADU non-matches),
`test_real_digit_bearing_names_untouched` (K-12 names),
`test_all_322_source_names_marker_free` (every source name through the
EXTENDED extractor → unchanged, no footnotes),
`test_letter_prefixed_marked_row_routes_to_manual_review` (synthetic
"Brewpub (P6,10)" source → row.footnotes [6, 10] → engine MANUAL_REVIEW
end-to-end). All useallow tests green (57 tests).

**Zero real-name damage proven → the extension shipped** (not
BLOCKED-on-design). The §21A.33.030 corpus gap in §1 still stands:
no re-read of the actual section text was performed in this wave.

## 4. Safety properties (unchanged, re-verified)

- Marked rows are parsed into `row.footnotes` and routed to MANUAL_REVIEW by the
  engine — never silently dropped.
- A name that is *only* a footnote marker raises `ValueError` loudly at load
  (no empty-name rows).
- Parenthetical words (`(large)`, `(indoor, outdoor)`) are NOT treated as
  markers — verified against the live function.
