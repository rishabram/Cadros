# AUDIT2.md — adversarial audit round 2 (2026-09-24)

Targets: useallow engine (silent-default hunt, aggregation, pack integrity),
POC builder (embedded-data fidelity, label honesty), caddy_drop
reconstruction (determinism, STORE_VIEW determination).
Mandate: minimal fixes only; goldens frozen; economics untouched.

## A. useallow engine — PASS, no silent defaults

**Method:** read `useallow/engine.py`, `adapter.py`, `pack.py`, `mu_pack.py`
in full, then ran a live adversarial battery (every aggregate below was
recomputed from source, not quoted from prose).

**Findings:**
1. No silent-default-to-allowed path exists. Exhaustive edge cases all yield
   UNKNOWN: unknown district (`R-1-7000`), empty/None `proposed_uses`,
   nonexistent use name, empty-string use name. A use absent from the pack
   yields UNKNOWN ("no verified row for this use") — never FAIL, never PASS.
2. Aggregation order verified live against the ratified order
   FAIL > UNKNOWN > MANUAL_REVIEW > CONDITIONAL_PASS > PASS:
   single-row statuses (M1-U-01 MR, M1-U-02 PASS, M1-U-13 CONDITIONAL_PASS,
   M1-U-28 UNKNOWN, M1-U-29 FAIL) and pairs (UN+MR→UNKNOWN, MR+CD→MR,
   CD+PP→CONDITIONAL_PASS, NP+UN→FAIL) all correct.
3. Footnote-before-status ordering is deliberate and correct: a
   permitted/conditional row carrying qualifying footnotes routes to
   MANUAL_REVIEW. (One latent note, not a live issue: `not_permitted` is
   checked before footnotes, so a blank cell WITH a footnote would yield
   FAIL; zero such rows exist in the pack — verified: `not_permitted rows
   with footnotes: none`.)
4. Pack integrity: 191 rows (122 M-1 / 27 OS / 42 PL, pin `5a3a06db…`
   reproduces), 322 MU rows (106 MU-5 / 105 MU-6 / 111 MU-11, pin
   `bf741fd2…` reproduces), combined 513 rows, zero duplicate rule_ids.
   `combine_packs` raises ValueError loudly on duplicates (tested).
5. All 513 rows pass the human-verification gate (named verifier + date +
   result in {VERIFIED, CORRECTED}).
6. MU blank-cell policy is the honest one: blank cells have no rows, so an
   absent MU use evaluates UNKNOWN, never FAIL — explicitly because the
   extraction may be incomplete. Documented in `mu_pack.py` + FILE_FLAGS.
7. `mu_pack.py` docstring claims footnote markers were "verified
   programmatically at load" — no such check exists in the loader. I ran
   the check myself: 322/322 names clean. Claim true, enforcement absent.
   **Recommendation:** add the assertion to `load_mu_pack` (one-line,
   fail-loud). Left as recommendation, not changed — minimal-fix mandate.

**No code changes made to useallow/.**

## B. POC builder — data matched sources; labels were stale; FIXED

**Verification:** embedded 10 rules == archived `verified_rules.v1_10rule.json`
(rule_id order identical); embedded 191 uses == live M-1/OS/PL pack
(zero diff both directions).

**Findings (fixed):**
1. The MU label ("awaiting Caddy's verified_uses_mu.json — not yet
   delivered") was factually false — the file landed, was reconstructed,
   and its 322 rows are merged. Removed.
2. The banner ("local verified rule store (10 rules)") was stale — the
   canonical store has 59.
3. The builder's `renderRules` was written for the pre-canonical schema
   (`r.district`/`section`/`title`/`claim`/`source_quote`); re-running it
   against the canonical store would have rendered an empty rules section.
   (Canonical rules carry `citation`, `quote`, `canonical_params`,
   `_caddy_rule_name`, and `district` string or `districts` list.)

**Fix applied:** rewrote `poc/build_poc.py` to embed the canonical store
(59 rules) + combined pack (513 rows: 191 M-1/OS/PL + 322 MU), with a
canonical-schema-aware renderer (handles the `districts` list on
MU-OPENSPACE-01), dynamic banner counts, honest MU provenance labels, and
a corrected Jefferson walkthrough cell (8/8 UNKNOWN now attributed to
stored-but-not-executable rules, not "no program facts"). Regenerated
`poc/neron_poc.html` (68KB → 189KB): embedded 59 rules == canonical store,
embedded 513 uses == combined pack, all stale labels gone.

## C. caddy_drop reconstruction — deterministic, STORE_VIEW holds

- sha256 `9ec5e8dc06104b001e4ed0274c7998e13e78eaab37bdb599c66816919e43c803`
  reproduces exactly for both the concatenated 7 store chunks and
  `store_view_lebron_schema.json`. Uses chunks sha `05ea9a11…` likewise.
- Chunks are byte-identical to the reconstructed files — the
  reconstruction is pure concatenation, deterministic by construction.
  (No committed reconstruction script exists; the chunks ARE the source.)
- STORE_VIEW determination re-confirmed: top-level `"rules"` (not
  `"candidate_rules"`); LeBron-schema keys
  (`citation`, `quote`, `params`, `human_verification`); adapter metadata
  (`_caddy_rule_name`, `_caddy_source_url`) on all 59 rules; zero native
  `code_section` keys. 59 rules, no duplicate ids.
- The honest limitation stands: Caddy's native fingerprint `7284b028…`
  cannot be verified from the pasted projection.

## D. Rename verification (folded in per LeBron 01:15 steering)

- `rulegraph/engine.py` `RULE_ALIASES`: `MU-OPEN-01` primary →
  `MU-OPENSPACE-01`; `MU-OS-01` kept as deprecated fallback resolving
  identically (interop with Caddy's store view, which still exposes
  MU-OS-01 until he locks MU-OPEN-01 in adapt_store.py per the 01:14 doc
  post). Canonical rule_id and Rohan's VERIFIED provenance byte-untouched.
- Live check: both aliases resolve to MU-OPENSPACE-01; store fingerprint
  unchanged (`9cc91ac7…`).
- Validations re-run: gate 92/44/43 (known composition), unit suite
  275/275 green, regression harness full mode PASS (0 real failures,
  0 findings, all 4 pins).

## E. Cosmetic fix

- `screen/outputs/real_slco_v3/summary.json`: `screen_name`
  `"real-slco-v2"` → `"real-slco-v3"` (metadata only).
