"""Adapter: building program -> use-allowance context contract.

The use-allowance engine needs two facts: the parcel's zoning district
(from the pipeline's zoning config) and the list of uses proposed for the
site (from the building program). Anything the program does not supply stays
None (-> UNKNOWN downstream), with provenance recording which upstream
source would fill the gap.

Per-scheme program overrides are NOT handled here. Callers split the
program with rulegraph.adapter.split_program() and merge per-scheme
overrides with rulegraph.adapter.program_for_scheme() BEFORE calling
build_use_context() — those helpers are program-shape-generic and are
reused here on purpose, not reimplemented. (Note: a raw "schemes" key
passed straight to build_use_context() is an unknown attribute and is
rejected loudly, exactly like any other typo'd program key.)
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# Reused, not reimplemented: program-shape-generic split/merge helpers, plus
# the RuleGraph contract attributes, which are KNOWN keys to this adapter's
# typo guard. One shared building program feeds both evaluators: RuleGraph
# facts (height_ft, stories, ...) are legitimate program keys that this
# adapter simply ignores — only truly unknown keys raise ValueError.
from rulegraph.adapter import (
    CONTRACT_ATTRS as _RG_CONTRACT_ATTRS,
    program_for_scheme,
    split_program,
)

__all__ = [
    "USE_ATTRS",
    "GAP_NOTES",
    "build_use_context",
    "split_program",
    "program_for_scheme",
]

# The full use-allowance context contract, in stable order.
USE_ATTRS: List[str] = [
    "district",
    "proposed_uses",
]

# Keys the typo guard accepts: our own contract attributes plus the
# RuleGraph contract attributes (foreign keys, ignored here).
_KNOWN_PROGRAM_KEYS = frozenset(USE_ATTRS) | frozenset(_RG_CONTRACT_ATTRS)

# Where each attribute would come from when it is not supplied.
GAP_NOTES: Dict[str, str] = {
    "district": "zoning config 'district' or parcel jurisdiction lookup",
    "proposed_uses": "building program 'proposed_uses': list of use names proposed for the site",
}


def build_use_context(
    zoning_cfg: Dict | None = None,
    program: Dict | None = None,
    program_source: str = "building program",
) -> Tuple[Dict, Dict]:
    """Build a use-allowance context from zoning config + optional program.

    Returns (context, provenance). context = {"district": str|None,
    "proposed_uses": list[str]|None}. Provenance maps each attribute to
    ("known", source) or ("unknown", gap_note). Unknown program keys raise
    ValueError — a typo'd program file must be loud, not silently ignored.
    "proposed_uses", when supplied, must be a list of strings, else
    ValueError (loud).
    """
    context: Dict = {"district": None, "proposed_uses": None}
    provenance: Dict = {a: ("unknown", GAP_NOTES[a]) for a in USE_ATTRS}

    if zoning_cfg:
        district = zoning_cfg.get("district")
        if district is not None:
            context["district"] = district
            provenance["district"] = ("known", "zoning config 'district'")

    if program:
        unknown_keys = [
            k for k in program if not k.startswith("_") and k not in _KNOWN_PROGRAM_KEYS
        ]
        if unknown_keys:
            raise ValueError(
                f"building program has unknown attributes: {', '.join(sorted(unknown_keys))} "
                "— fix the program file; nothing was evaluated"
            )
        if "district" in program and program["district"] is not None:
            context["district"] = program["district"]
            provenance["district"] = ("known", program_source)
        if "proposed_uses" in program and program["proposed_uses"] is not None:
            uses = program["proposed_uses"]
            if not isinstance(uses, list) or any(
                not isinstance(u, str) for u in uses
            ):
                raise ValueError(
                    "building program 'proposed_uses' must be a list of "
                    "use-name strings; nothing was evaluated"
                )
            context["proposed_uses"] = list(uses)
            provenance["proposed_uses"] = ("known", program_source)

    return context, provenance
