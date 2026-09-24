"""MU use-allow pack loader: Caddy's verified_uses_mu.json -> UseRows.

Parses ONLY the name lists under "districts" (MU-5 / MU-6 / MU-11, each with
"permitted" and "conditional" lists). 322 rows total (95+11 / 100+5 / 102+9).

Row identity: the JSON carries no per-row rule ids, so ids are synthesized
deterministically as MU5-U-001 ... in file order (permitted block first,
then conditional, per district). The ids are pack-local provenance keys,
NOT code citations — the human verification behind them is the file-level
batch record below, attached to every row.

Human verification: the source file asserts batch verification
(human_verified_by Rohan, 2026-09-23, "Batch-of-30 review against the live
table; silence per batch = verified; zero corrections"). That batch record
is attached verbatim to every row and surfaced in provenance
("caddy-batch-verified") — the machine never invents per-row verdicts.

Statuses: "permitted"/"conditional" only. The file's legend says blank =
not allowed, but blank cells have no rows here — a use absent from both
lists evaluates UNKNOWN ("no verified row for this use"), never FAIL,
because the extraction may be incomplete. The file's one flags entry
(MU-11 absent rows, live-re-read confirmed blank, still needing human
eyeball) is surfaced as FILE_FLAGS, not per-row verdicts.

Footnotes: none of the 322 names carry superscript/footnote markers
(verified programmatically at load by _extract_footnote_markers); rows
therefore never route to MANUAL_REVIEW from this pack. If a future source
file DOES carry markers, they are parsed into row.footnotes and the engine
routes those rows to MANUAL_REVIEW — the check never silently drops them.

Fingerprinting reuses rulegraph.fingerprint.canonical_hash so any edit to
the MU file is caught by the pinned constant.
"""

from __future__ import annotations

import json
import os
import re

from .pack import PINNED_PACK_FINGERPRINT  # noqa: F401  (re-exported for tests)
from .pack import UsePack, UseRow
from rulegraph.fingerprint import canonical_hash

# Pinned after the first verified parse; tests assert load_mu_pack() reproduces it.
PINNED_MU_PACK_FINGERPRINT = "bf741fd283b46ee39b937e5a5ff8c04fb5d9b3a3fb7a4a577bb4e3f8eb58bd6c"

DEFAULT_MU_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "caddy_drop",
        "verified_uses_mu.json",
    )
)

_DISTRICTS = ("MU-5", "MU-6", "MU-11")
_ID_PREFIX = {"MU-5": "MU5", "MU-6": "MU6", "MU-11": "MU11"}
_BLOCKS = (("permitted", "P", "permitted"), ("conditional", "C", "conditional"))

# File-level extraction caveat, surfaced verbatim (not a per-row verdict).
FILE_FLAGS = (
    "MU-11 absent rows (Single-family (detached), Twin home, Two-family, "
    "Store, Pawnshop, Check cashing/payday loan business, Automobile repair "
    "(major)): absent from MU-11 permitted column per extraction; live "
    "re-read 2026-09-23 confirmed blank with no P, C, or superscript — "
    "still needs a human eyeball at check-in per contract. These uses have "
    "no rows in this pack and evaluate UNKNOWN, never FAIL."
)


# Footnote-marker patterns a use-table name may carry: unicode superscript
# digits (¹²), parenthesized digit groups ("(1)", "(1, 2)"), bracketed digit
# groups ("[1]"), a bare digit run glued to a trailing letter ("Retail1"),
# or the corpus's own LETTER-PREFIXED form: P/C glued to digits inside
# parens ("Brewpub (P6,10)", "Accessory use (P21)", "Shop (C2)").
# The P/C prefix is the table's permitted/conditional column marker — it is
# dropped and only the digits become footnotes.
# Parenthetical words ("(large)", "(indoor, outdoor)") are NOT markers.
_SUPERSCRIPT_RE = re.compile(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+")
_DIGIT_GROUP_RE = re.compile(r"\(\s*(\d[\d\s,]*)\s*\)")
_BRACKET_DIGIT_RE = re.compile(r"\[\s*(\d[\d\s,]*)\s*\]")
_TRAILING_DIGIT_RE = re.compile(r"(?<=[A-Za-z])(\d+)$")
# P/C-only and case-sensitive BY DESIGN: a broader letter set risks
# over-stripping real names (e.g. "Building (Grade A2)"), and the corpus
# notation is uppercase P/C. Lowercase "(p6)" is left as a false negative —
# safe direction (passes through clean, never mis-stripped).
_LETTER_PREFIXED_RE = re.compile(r"\(\s*([PC])\s*(\d[\d\s,]*)\s*\)")
_SUPERSCRIPT_VALUE = {
    "⁰": 0, "¹": 1, "²": 2, "³": 3, "⁴": 4,
    "⁵": 5, "⁶": 6, "⁷": 7, "⁸": 8, "⁹": 9,
}


def _extract_footnote_markers(name: str):
    """-> (clean_name, footnotes). The programmatic footnote-marker check
    the module docstring promises: every use name is scanned at load and any
    marker is parsed into footnotes (the engine routes such rows to
    MANUAL_REVIEW). Returns the name with markers stripped.

    A name with no markers returns (name, []) — the honest common case for
    the current source file, so its fingerprint is unaffected.
    """
    footnotes = []

    def _take_sup(m):
        run = m.group(0)
        footnotes.append(int("".join(str(_SUPERSCRIPT_VALUE[c]) for c in run)))
        return ""

    clean = _SUPERSCRIPT_RE.sub(_take_sup, name)

    def _take_group(m):
        footnotes.extend(int(x) for x in m.group(1).split(",") if x.strip())
        return ""

    def _take_letter_prefixed(m):
        # group(1) is the P/C column letter (dropped); group(2) the digits.
        footnotes.extend(int(x) for x in m.group(2).split(",") if x.strip())
        return ""

    # Letter-prefixed FIRST so "(P6,10)" never partially matches another
    # pattern's digit group mid-name.
    clean = _LETTER_PREFIXED_RE.sub(_take_letter_prefixed, clean)
    clean = _DIGIT_GROUP_RE.sub(_take_group, clean)
    clean = _BRACKET_DIGIT_RE.sub(_take_group, clean)
    m = _TRAILING_DIGIT_RE.search(clean)
    if m:
        footnotes.append(int(m.group(1)))
        clean = clean[: m.start(1)]
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean, footnotes


def load_mu_pack(path: str | None = None) -> UsePack:
    """Load the MU use-allow pack from Caddy's verified_uses_mu.json.

    Missing file -> loud FileNotFoundError. Every row carries the file's
    batch human-verification record; the pack fingerprint pins the content.
    """
    if path is None:
        path = DEFAULT_MU_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"MU use pack source not found: {path}")
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)

    src = doc.get("source", {})
    hv = {
        "result": "VERIFIED",
        "verified_by": src.get("human_verified_by"),
        "verified_on": src.get("human_verified_on"),
    }
    if not hv["verified_by"] or not hv["verified_on"]:
        raise ValueError(f"{path}: source lacks batch human-verification record")

    districts = doc.get("districts", {})
    rows: list[UseRow] = []
    for district in _DISTRICTS:
        d = districts.get(district)
        if not isinstance(d, dict):
            raise ValueError(f"{path}: missing district block {district!r}")
        seq = 0
        for block, marking, status in _BLOCKS:
            names = d.get(block)
            if not isinstance(names, list):
                raise ValueError(
                    f"{path}: district {district!r} block {block!r} is not a list"
                )
            for name in names:
                if not isinstance(name, str) or not name.strip():
                    raise ValueError(
                        f"{path}: district {district!r} block {block!r} "
                        "has an empty/non-string use name"
                    )
                seq += 1
                clean_name, footnotes = _extract_footnote_markers(name.strip())
                if not clean_name:
                    raise ValueError(
                        f"{path}: district {district!r} block {block!r} "
                        f"use name {name!r} is only a footnote marker"
                    )
                rows.append(
                    UseRow(
                        rule_id=f"{_ID_PREFIX[district]}-U-{seq:03d}",
                        district=district,
                        use_name=clean_name,
                        marking=marking,
                        status=status,
                        footnotes=footnotes,
                        flags="",
                        provenance="caddy-batch-verified",
                        human_verification=dict(hv),
                    )
                )

    fingerprint = canonical_hash({"rows": [r.__dict__ for r in rows]})
    return UsePack(rows=rows, fingerprint=fingerprint)
