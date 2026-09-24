"""Input-freshness gate for the POC builder.

The POC embeds the canonical rule store and both use packs. BUILD_DATE is the
date the embedded data was last verified current. If any input changes after
that date, the built HTML is silently stale — so the builder refuses to build
until BUILD_DATE and the expected fingerprints are updated together.

RECOVERY (when StalePocInputsError names a stale input):
1. Verify the input change is legitimate (diff the store/pack; check provenance).
2. Get the new live fingerprints from the error message (it prints live vs expected).
3. Update BUILD_DATE (today) and EXPECTED_INPUTS (new pins) together — never one alone.
4. Rebuild: venv/bin/python poc/build_poc.py
5. Run poc tests + full suite + regression harness; all pins must stay green.

Produces and implies no human verdicts. All values here are machine-checked.
"""
from __future__ import annotations

BUILD_DATE = "2026-09-24"

# Pinned fingerprints of the inputs the POC embeds. These are the same pins
# the test suite and the regression harness pin (evals/regression.py), so any
# store/pack edit fails the whole suite — and this gate fails the POC build
# with a message that names the stale input instead of building quietly.
EXPECTED_INPUTS = {
    "rule_store": "9cc91ac71f5f1de221b9609291ce264ca33d6c6ba9b98f7e7f898778fd0cfd1c",
    "pack_m1_os_pl": "5a3a06db51f04b7cefafe57ae9339b44ebdec6e4a3f7404d67687faec4fbc90e",
    "pack_mu": "bf741fd283b46ee39b937e5a5ff8c04fb5d9b3a3fb7a4a577bb4e3f8eb58bd6c",
}


class StalePocInputsError(RuntimeError):
    """Raised when the POC's embedded inputs changed since BUILD_DATE."""


def store_fingerprint(rules):
    """Fingerprint the rule store exactly the way the engine does."""
    from rulegraph.fingerprint import canonical_hash

    return canonical_hash({"rules": rules})


def assert_inputs_fresh(rule_store_fp, pack_191_fp, pack_322_fp):
    """Raise StalePocInputsError if any embedded input changed since BUILD_DATE.

    Returns the live fingerprints on success (the builder embeds them so the
    NERON lane can validate them on receipt).
    """
    live = {
        "rule_store": rule_store_fp,
        "pack_m1_os_pl": pack_191_fp,
        "pack_mu": pack_322_fp,
    }
    stale = [k for k in live if EXPECTED_INPUTS.get(k) != live[k]]
    if stale:
        detail = ", ".join(
            "%s (live %s…, expected %s…)"
            % (k, live[k][:12], (EXPECTED_INPUTS.get(k) or "")[:12])
            for k in stale
        )
        raise StalePocInputsError(
            "POC inputs changed since BUILD_DATE %s: %s. The built HTML would be "
            "stale. After verifying the change, update BUILD_DATE and "
            "EXPECTED_INPUTS in poc/input_freshness.py together." % (BUILD_DATE, detail)
        )
    return live
