"""RuleGraph v1 engine.

Gate: a rule may execute ONLY when its human_verification record authorizes
it — result in {VERIFIED, CORRECTED} AND a nonempty verified_by AND a
nonempty verified_on. The top-level "status" field is a legacy label and can
NEVER authorize execution on its own: stale/missing human_verification
yields UNKNOWN.

Three-valued results flow upward: a scheme is "clean" only when every
applicable rule returns PASS. Any FAIL fails the scheme; any UNKNOWN makes the
scheme's compliance UNKNOWN.
"""
import json

from .predicates import EVALUATORS, Outcome
from .fingerprint import canonical_hash

EXECUTABLE_RESULTS = {"VERIFIED", "CORRECTED"}


def human_authorization(rule):
    """Return (ok, reason). Only a human verifier can authorize execution.

    Requires ALL of:
      - human_verification.result in {VERIFIED, CORRECTED}
      - human_verification.verified_by nonempty
      - human_verification.verified_on nonempty
    A top-level "status" field (e.g. status: "verified") is ignored by the
    gate — it is stale metadata, not a human verdict.
    """
    hv = rule.get("human_verification")
    if not isinstance(hv, dict):
        return False, "no human_verification record; not human-verified, cannot execute"
    result = hv.get("result")
    if result not in EXECUTABLE_RESULTS:
        return False, (
            f"human_verification.result is {result!r}; not human-verified, cannot execute"
        )
    if not str(hv.get("verified_by") or "").strip():
        return False, "human_verification.verified_by is empty; not human-verified, cannot execute"
    if not str(hv.get("verified_on") or "").strip():
        return False, "human_verification.verified_on is empty; not human-verified, cannot execute"
    return True, f"human-verified ({result})"


# Engine-scoped aliases for canonical rule ids. The cross-team decision,
# posted to the shared doc (LeBron 2026-09-24 01:13), is that the agent-agreed
# short alias is "MU-OPEN-01" (NOT "MU-OS-01", which reads as the OS district).
# Canonical id MU-OPENSPACE-01 and its Rohan-verified provenance are untouched;
# "MU-OS-01" is kept as a deprecated fallback resolving identically, to cover
# the 01:11/01:13 wording slip — both aliases never change what the store says.
RULE_ALIASES = {
    "MU-OPEN-01": "MU-OPENSPACE-01",
    "MU-OS-01": "MU-OPENSPACE-01",  # deprecated fallback; do not use in new code
}


class RuleGraph:
    # Machine-extracted param overlays (Caddy extraction v1/v2). An overlay
    # supplies (evaluator, params) for stored-but-not-executable rules whose
    # quotes are human-verified but whose numeric params were never
    # transcribed. Overlays are applied IN MEMORY ONLY: self.rules (and
    # therefore self.fingerprint) is always the canonical store,
    # byte-identical to verified_rules.json. Results computed from overlay
    # params carry params_source in their reason so machine extraction is
    # never mistaken for human verification.
    #
    # Label stamped on every overlay-derived reason. Kept as the fallback tag
    # for overlays whose doc carries no ``params_source_tag`` (the v1 overlay
    # has none; its reasons must stay byte-identical).
    OVERLAY_PARAMS_SOURCE = "caddy_extraction_v1"

    def __init__(self, rules, overlays=None, overlay_sources=None):
        self.rules = {r["rule_id"]: r for r in rules}
        self.overlays = dict(overlays or {})
        self.overlay_sources = dict(overlay_sources or {})
        self.fingerprint = canonical_hash({"rules": rules})

    @classmethod
    def load(cls, path, overlay_path=None):
        """Load the store; optionally apply param overlays in-memory.

        ``overlay_path`` may be a single path or a list of paths. Overlays
        apply in list order — a later overlay wins if two name the same
        rule_id. Each overlay doc may carry ``params_source_tag``; the tag of
        the overlay that supplied a rule's params is stamped on that rule's
        reasons. A missing overlay path raises FileNotFoundError loudly (never
        silently unapplied); an overlay naming an unknown rule raises
        KeyError loudly.
        """
        with open(path) as f:
            store = json.load(f)
        overlays = {}
        overlay_sources = {}
        if overlay_path is not None:
            paths = [overlay_path] if isinstance(overlay_path, str) else list(overlay_path)
            for opath in paths:
                with open(opath) as f:
                    overlay_doc = json.load(f)
                tag = overlay_doc.get("params_source_tag") or cls.OVERLAY_PARAMS_SOURCE
                for rid, entry in overlay_doc.get("rules", {}).items():
                    if rid not in {r["rule_id"] for r in store["rules"]}:
                        raise KeyError(f"overlay references unknown rule {rid!r}")
                    overlays[rid] = entry
                    overlay_sources[rid] = tag
        return cls(store["rules"], overlays=overlays, overlay_sources=overlay_sources)

    def evaluate(self, rule_id, context):
        """Evaluate one rule. Unknown rule ids raise KeyError (a code bug, loud).

        Engine-scoped aliases (RULE_ALIASES) resolve to their canonical ids;
        the returned rule_id is always the canonical one.
        """
        rule_id = RULE_ALIASES.get(rule_id, rule_id)
        rule = self.rules[rule_id]  # KeyError on purpose: fail loud, not UNKNOWN
        context = context or {}
        authorized, gate_reason = human_authorization(rule)
        hv_result = (rule.get("human_verification") or {}).get("result")
        if not authorized:
            return {
                "rule_id": rule_id,
                "outcome": Outcome.UNKNOWN.value,
                "applicable": True,
                "reason": gate_reason,
                "status": hv_result,
            }
        rule_district = rule.get("district")
        # Canonical stores may scope one rule to several districts via a
        # "districts" list (e.g. MU-OPENSPACE-01: MU-5, MU-6, MU-11). A list
        # never partially matches: the context district must be a member.
        rule_districts = rule.get("districts")
        if rule_districts is None:
            rule_districts = [rule_district] if rule_district else []
        ctx_district = context.get("district")
        if rule_districts and ctx_district and ctx_district not in rule_districts:
            scope = (
                f"rule districts {rule_districts} do not include parcel "
                f"district {ctx_district}"
                if len(rule_districts) > 1
                else f"rule district {rule_districts[0]} != parcel district {ctx_district}"
            )
            return {
                "rule_id": rule_id,
                "outcome": Outcome.PASS.value,
                "applicable": False,
                "reason": f"not applicable: {scope}",
                "status": hv_result,
            }
        evaluator = EVALUATORS.get(rule.get("evaluator"))
        params = rule.get("params", {}) or {}
        params_source = None
        overlay = self.overlays.get(rule_id)
        if overlay:
            # The canonical store keeps evaluator=None / params=null for
            # these rules; the overlay supplies both without editing the
            # human-verified store. Canonical ids and human_verification
            # records are never touched.
            if overlay.get("evaluator"):
                evaluator = EVALUATORS.get(overlay["evaluator"])
            if overlay.get("params") is not None:
                params = overlay["params"]
            params_source = self.overlay_sources.get(rule_id, self.OVERLAY_PARAMS_SOURCE)
        if evaluator is None:
            wanted = (overlay or {}).get("evaluator") or rule.get("evaluator")
            return {
                "rule_id": rule_id,
                "outcome": Outcome.UNKNOWN.value,
                "applicable": True,
                "reason": f"no evaluator registered for {wanted!r}",
                "status": hv_result,
            }
        outcome, reason = evaluator(params, context)
        if params_source:
            reason = f"{reason} [params: {params_source} — machine-extracted, not a human verdict]"
        return {
            "rule_id": rule_id,
            "outcome": outcome.value,
            "applicable": True,
            "reason": reason,
            "status": hv_result,
        }

    def evaluate_all(self, context):
        return [self.evaluate(rid, context) for rid in self.rules]

    def scheme_verdict(self, context):
        """Roll per-rule outcomes into one scheme verdict.

        The verdict vocabulary stays three-valued (PASS/FAIL/UNKNOWN): any
        FAIL fails the scheme, any UNKNOWN makes it UNKNOWN, otherwise PASS.
        "applicable_count" names how many rules actually evaluated against
        this scheme's district — a PASS with applicable_count == 0 is
        vacuous (no verified rule covered the district) and must be
        rendered as "no applicable verified rules", never as a compliance
        finding. The authorization gate above is unchanged.
        """
        results = self.evaluate_all(context)
        outcomes = [r["outcome"] for r in results]
        applicable_count = sum(1 for r in results if r.get("applicable") is True)
        if Outcome.FAIL.value in outcomes:
            verdict = Outcome.FAIL.value
        elif Outcome.UNKNOWN.value in outcomes:
            verdict = Outcome.UNKNOWN.value
        else:
            verdict = Outcome.PASS.value
        return {
            "verdict": verdict,
            "results": results,
            "applicable_count": applicable_count,
        }
