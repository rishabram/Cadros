# Benchmark zoning policy — what may feed the harness

The harness refuses to score a plat unless all three dimensional inputs are
sourced. An unsourceable input is a gap, never a fill. This policy is the
contract Phase C plat research follows.

## Required per scored plat

- `min_lot_area_sqft`, `min_frontage_ft`, `road_width_ft` — each with a `source`
  string naming exactly where the number came from (rule_id, code section + URL,
  or staff-report document + page).
- The zoning district must be the district the plat was **approved under**.
  Verify against the staff report or the zoning map effective at the approval
  date. A later rezone disqualifies the plat from the scored set.

## Source precedence

1. **NERON verified rule store** (`rulegraph/verified_rules.json`) — cite `rule_id`;
   only `human_verification.result == VERIFIED` rules. Known-good examples:
   M-1-01 (min lot area 10,000 sqft; min lot width 80 ft), OS-01 (no minimums),
   PL-01 (use-specific minimums). MU districts have VERIFIED *absence* of
   minimum lot area/width (MU-5-16, MU-6-16, MU-11-11) — an MU plat therefore
   cannot be scored on lot-count minimums; record as not_scored with reason.
2. **Official city code text** (city website, ULCT, or qcode/amlegal) — cite
   section + URL + access date.
3. **Planning commission staff report** for the plat — cite document + page.

## Allowed mappings (recorded explicitly in `source`, never silently)

- Min **lot width** may stand in for `min_frontage_ft` only when the district's
  code states a width minimum and no separate frontage minimum exists.
  Example source string: "M-1-01: 80 ft min lot width used as frontage proxy;
  no separate frontage minimum in 21A.28 (verified absence unconfirmed — see gap)".
- `road_width_ft` has no verified-store source today; it must come from the
  city engineering design standards with citation. If unsourceable, the plat
  is not scored.

## Known gaps (2026-09-24)

- No verified frontage or road-width rules in the store for any district.
- Non-SLC cities (South Salt Lake, Herriman, etc.) have no verified rules at
  all — their plats need source-precedence-2/3 research per plat, or they stay
  unscored. Mill Subdivision is the current example: commercial, zone unstated
  on plat, stays unscored until its approving zone + params are sourced.
