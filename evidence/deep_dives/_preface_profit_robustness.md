## Deep-dive narrative — archetype: profit vs. robustness

> **Machine-generated narrative (machine-draft — not human-verified).** Every
> figure below is copied from this parcel's `report.json` and from
> `screening_results.csv`; no new facts, no verdicts, no recommendations.

**Why this parcel — selection documented:** the brief asked for a high-profit
parcel with elevated UNKNOWNs (`rg_unknown > 0` among scheme rows, excluding
the MU-11 parcel reserved for the unknown-review archetype). **That query
returned zero rows.** In this screen, every non-MU-11 scheme is RuleGraph
PASS with **23 unknown context attributes** each — the robustness gap takes
the form of unknown attributes and vacuous PASSes, not UNKNOWN verdicts.
This parcel was therefore chosen as the **3rd-highest projected profit in
the screen** ($3,582,080.25) *and* because its economics fell back to the
DEFAULT build — the weakest economics confidence in the top cohort.

- Parcel `08251510020000` — **M-2**, **95.03 acres** (largest parcel with
  schemes in the screen). Top scheme `scheme_00`: **37 lots**, profit
  **$3,582,080.25**, margin **71.71%**. All 8 schemes geometry-clean.

**What the $3.58M assumes vs. what is unverified:**

| The profit assumes… | Status |
|---|---|
| M-2 dimensional minimums for lot sizing | **PROVISIONAL** — no M-2 rule is human-verified; illustrative only |
| $450,000/lot sale price | **DEFAULT fallback, assumption-grade**: "Valley-average Wasatch Front finished SFR lot; **judgment, no comp pulled**" — an SFR-lot judgment applied to an M-2 industrial parcel |
| Compliance with M-2 rules | **Unchecked** — all 8 RuleGraph PASSes are `applicable: false` (the store's 8 verified rules cover MU-11 and PL only) |
| 23 RuleGraph context attributes (height, setbacks, buffers, abutments, building program) | **UNKNOWN** — the pipeline never had these facts |
| The proposed use is allowed in M-2 | **Use-allowance pending** — the 21A.33 checker is not yet integrated |

**Tradeoff, plainly:** this is the screen's most *geometrically* productive
large parcel and its least *evidentially* supported top profit. Nearly every
input the $3.58M depends on — the price per lot, the lot-size rules, the
compliance check, the use allowance — is provisional, defaulted, or missing.
Robustness here would come from, in order: (1) human-verified M-2 rules,
(2) a real industrial-lot comp set, (3) a use-allowance check, (4) a building
program. Until then, treat the figure as a screening flag for "worth
researching," not as diligence.
