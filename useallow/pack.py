"""Use-allow pack parser for the 21A.33 M-1/OS/PL candidate rows.

Parses ONLY sections 1-3 of
~/workspace/neron-zoning/21A33_candidates_M1_OS_PL.md:
  §1 — M-1 candidates as a markdown TABLE (122 rows)
  §2 — OS candidates as BULLET lines (27 rows)
  §3 — PL candidates as BULLET lines (42 rows)
Parsing STOPS before section 4 (§4+ holds footnote fragments, retrieval
gaps, reconciliation notes — never candidate rows).

Human verdicts are never invented here: the human_verification field is
parsed verbatim from the row's Human-verdict column/segment ("VERIFIED —
verified_by Rohan, 2026-09-23"); absent verdict text yields None.

Fingerprinting reuses rulegraph.fingerprint.canonical_hash (imported, not
reimplemented) so any edit to the pack is caught by the pinned constant.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRATCH = os.path.dirname(_HERE)
if _SCRATCH not in sys.path:
    sys.path.insert(0, _SCRATCH)

from rulegraph.fingerprint import canonical_hash  # noqa: E402

# Pinned after the first verified parse; tests assert load_pack() reproduces it.
PINNED_PACK_FINGERPRINT = "5a3a06db51f04b7cefafe57ae9339b44ebdec6e4a3f7404d67687faec4fbc90e"

DEFAULT_PACK_PATH = os.path.normpath(
    os.path.join(_SCRATCH, "..", "neron-zoning", "21A33_candidates_M1_OS_PL.md")
)

_SECTION_RE = re.compile(r"^## (\d+)\.")
_FOOTNOTE_RE = re.compile(r"\(([PC])\s*([\d\s,]*)\)")
_HV_RE = re.compile(r"VERIFIED\s*—\s*verified_by\s+([^,]+),\s*(\d{4}-\d{2}-\d{2})")
# Deviates slightly from the plain spec regex: allows an optional
# parenthetical annotation after the quoted use name, e.g.
#   - OS-U-16 — "Parking: Off site" (off-site parking supporting OS/NOS uses) — Permitted — ...
# (4 rows carry such annotations: OS-U-16, PL-U-15, PL-U-28, PL-U-39.)
# The annotation is folded into use_name to keep it verbatim.
_BULLET_RE = re.compile(r'^- (OS|PL)-U-(\d+) — "([^"]+)"( \([^()]*\))? — (.+)$')

_DISTRICT_BY_PREFIX = {"M1": "M-1", "OS": "OS", "PL": "PL"}
_PROVENANCES = ("live-text", "reconciled", "prior-extraction")


@dataclass
class UseRow:
    rule_id: str            # e.g. "M1-U-01"
    district: str           # "M-1" | "OS" | "PL"
    use_name: str           # verbatim
    marking: str            # verbatim marking(s); "" when none/ambiguous
    status: str             # "permitted" | "conditional" | "not_permitted" | "unresolved"
    footnotes: list[int]    # qualifying-provision numbers; [] if none
    flags: str              # "⚠ ..." substring of the status segment, else ""
    provenance: str         # "live-text" | "reconciled" | "prior-extraction"
    human_verification: dict | None  # {"result","verified_by","verified_on"}


@dataclass
class UsePack:
    rows: list[UseRow]
    fingerprint: str


def _parse_status_segment(seg):
    """-> (status, footnotes, flags). Unresolved rows keep the full status
    text in flags and claim no footnotes (the marking is not trustworthy)."""
    seg = seg.strip()
    if seg.startswith("⚠"):
        return "unresolved", [], seg
    if seg.startswith("Permitted"):
        status = "permitted"
    elif seg.startswith("Conditional"):
        status = "conditional"
    elif seg.startswith("Not permitted"):
        status = "not_permitted"
    else:
        raise ValueError(f"unrecognized status segment: {seg!r}")
    m = _FOOTNOTE_RE.search(seg)
    footnotes = [int(x) for x in m.group(2).split(",") if x.strip()] if m else []
    warn = seg.find("⚠")
    flags = seg[warn:].strip() if warn != -1 else ""
    return status, footnotes, flags


def _parse_human_verification(text, line_no):
    m = _HV_RE.search(text)
    if not m:
        raise ValueError(f"row at line {line_no} lacks a parseable human verdict: {text!r}")
    return {"result": "VERIFIED", "verified_by": m.group(1), "verified_on": m.group(2)}


def _parse_table_row(cells, line_no, expected_district):
    if len(cells) != 6:
        raise ValueError(f"line {line_no}: expected 6 cells, got {len(cells)}: {cells!r}")
    rid, name, marking, status_seg, prov, hv_text = cells
    assert "|" not in name, f"pipe inside use name at line {line_no}: {name!r}"
    prefix = rid.split("-")[0]
    if prefix not in _DISTRICT_BY_PREFIX:
        raise ValueError(f"line {line_no}: bad rule id {rid!r}")
    district = _DISTRICT_BY_PREFIX[prefix]
    if district != expected_district:
        raise ValueError(f"line {line_no}: id {rid!r} in wrong section (expected {expected_district})")
    if prov not in _PROVENANCES:
        raise ValueError(f"line {line_no}: bad provenance {prov!r}")
    status, footnotes, flags = _parse_status_segment(status_seg)
    return UseRow(
        rule_id=rid,
        district=district,
        use_name=name,
        marking=marking,
        status=status,
        footnotes=footnotes,
        flags=flags,
        provenance=prov,
        human_verification=_parse_human_verification(hv_text, line_no),
    )


def _parse_bullet(line, line_no):
    m = _BULLET_RE.match(line)
    if not m:
        raise ValueError(f"line {line_no}: unparseable bullet: {line!r}")
    prefix, num, quoted, paren, remainder = m.groups()
    district = _DISTRICT_BY_PREFIX[prefix]
    name = quoted + (paren or "")
    segs = remainder.split(" — ")
    status_seg = segs[0].strip()
    prov = segs[1].strip() if len(segs) > 1 else ""
    if prov not in _PROVENANCES:
        raise ValueError(f"line {line_no}: bad provenance {prov!r}")
    verdict_text = " — ".join(segs[2:]).strip()
    hv = _parse_human_verification(verdict_text, line_no) if verdict_text else None
    status, footnotes, flags = _parse_status_segment(status_seg)
    if status == "unresolved":
        # Ambiguous extraction (e.g. OS-U-27): no single trustworthy marking,
        # no footnote claim — the full story stays in flags.
        marking, footnotes = "", []
    else:
        fm = _FOOTNOTE_RE.search(status_seg)
        marking = status_seg[fm.start() + 1:fm.end() - 1].strip() if fm else ""
    return UseRow(
        rule_id=f"{prefix}-U-{num.zfill(2)}" if len(num) == 2 else f"{prefix}-U-{num}",
        district=district,
        use_name=name,
        marking=marking,
        status=status,
        footnotes=footnotes,
        flags=flags,
        provenance=prov,
        human_verification=hv,
    )


def load_pack(path: str | None = None) -> UsePack:
    """Load the use-allow pack from the markdown source. Missing file -> loud
    FileNotFoundError. Sections 4+ are never parsed."""
    if path is None:
        path = DEFAULT_PACK_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"use pack source not found: {path}")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    rows: list[UseRow] = []
    section = None
    for i, line in enumerate(lines, 1):
        sm = _SECTION_RE.match(line)
        if sm:
            section = int(sm.group(1))
            if section >= 4:
                break
            continue
        if section == 1 and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells[0] == "ID" or all(re.fullmatch(r"-+", c) for c in cells):
                continue  # header / separator row
            rows.append(_parse_table_row(cells, i, expected_district="M-1"))
        elif section in (2, 3) and line.startswith("- "):
            if line.startswith("- OS-U-") or line.startswith("- PL-U-"):
                rows.append(_parse_bullet(line, i))
            # other dash lines in §2/§3 (e.g. prose) are not candidate rows

    fingerprint = canonical_hash({"rows": [r.__dict__ for r in rows]})
    return UsePack(rows=rows, fingerprint=fingerprint)


def combine_packs(*packs: UsePack) -> UsePack:
    """Concatenate pack rows (in argument order) into one UsePack with a fresh
    canonical fingerprint. Row identity is preserved; duplicate rule_ids
    across packs raise ValueError (loud) — two packs must never silently
    shadow each other's rows."""
    rows: list[UseRow] = []
    seen = set()
    for pack in packs:
        for r in pack.rows:
            if r.rule_id in seen:
                raise ValueError(
                    f"duplicate rule_id {r.rule_id!r} across combined packs"
                )
            seen.add(r.rule_id)
            rows.append(r)
    fingerprint = canonical_hash({"rows": [r.__dict__ for r in rows]})
    return UsePack(rows=rows, fingerprint=fingerprint)
