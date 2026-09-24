"""Use-allowance evaluation: proposed uses vs the verified use pack.

adapter.py maps the pipeline-known district + the building program's
proposed uses onto the two-attribute use-allowance context contract.
engine.py evaluates each proposed use against human-verified UseRows
(M-1/OS/PL rows from SLC 21A.33.040/.070) with the canonical verdict set:
PASS / CONDITIONAL_PASS / FAIL / UNKNOWN / MANUAL_REVIEW.
"""

# Program key contract for the use-allowance evaluator (building program dict):
#
# - "proposed_uses": list of use-name strings proposed for the site, e.g.
#   ["Agricultural use", "Bar establishment"]. Each name is matched
#   verbatim (case- and whitespace-insensitive) against the "Use name
#   (verbatim)" column of the parcel district's human-verified rows.
#   A proposed use with no matching verified row is UNKNOWN, never allowed.
# - "district": optional; overrides zoning_cfg's "district" when present
#   (program facts win, mirroring rulegraph.adapter.build_context).
# - "schemes": optional top-level map of scheme id -> program override dict;
#   popped by rulegraph.adapter.split_program before build_use_context sees
#   it, exactly as in the RuleGraph wiring.
#
# The building program is shared with the RuleGraph evaluator: RuleGraph
# facts (height_ft, stories, ...) are known keys here and are ignored, and
# "proposed_uses" is a known key to the RuleGraph adapter and is ignored
# there. Truly unknown (non-underscore) keys still raise ValueError loudly.
from __future__ import annotations
