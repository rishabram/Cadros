#!/usr/bin/env python3
"""CORA CTO-AUDIT FILE PACKAGE — chunk-paste shipper.

Assembles the three audit bundles, chunks them (~9KB), and posts them
verbatim to the Continued Shared Channel doc via batchUpdate/replaceAllText,
each chunk closed by an ASCII marker carrying its sha256.
Transport basis: in-channel 13:31 MDT 2026-09-24 narrow carve-out
(chunked-paste-with-sha256 for this CTO-audit package only).
Drive upload is parked on Rishab's connector (human-side item).
"""
import hashlib
import json
import subprocess
import sys

DOC_ID = "1UvLh2AEyVTZ0VCWnxe7MXD_Ioh7yR7-6Tm-4kHcElMM"
CHUNK = 9000
REPO = "/home/hatch/workspace/neron-scratch"

FILES = [
    # (repo-relative path, bundle label)
    ("rulegraph/verified_rules.json", "A-59-rule-store"),
    ("useallow/engine.py", "B-useallow-engine"),
    ("useallow/adapter.py", "B-useallow-adapter"),
    ("run_evals.py", "B-run-evals"),
    ("benchmark/plats.json", "C-plats"),
    ("benchmark/evidence_funnel.json", "C-funnel"),
    ("benchmark/evidence/taylorsville-fields-sub/PACKET.md", "C-fields-packet"),
    ("benchmark/evidence/taylorsville-fields-sub/SHA256SUMS.txt", "C-fields-sums"),
    ("benchmark/evidence/taylorsville-fields-sub/children.geojson", "C-fields-children"),
    ("benchmark/evidence/taylorsville-fields-sub/staff_report.txt", "C-fields-staff-report"),
    ("benchmark/evidence/taylorsville-1s25-sub-000494-2024/PACKET.md", "C-1s25-packet"),
    ("benchmark/evidence/taylorsville-1s25-sub-000494-2024/SHA256SUMS.txt", "C-1s25-sums"),
    ("benchmark/evidence/taylorsville-1s25-sub-000494-2024/parent_parcels.geojson", "C-1s25-parents"),
]

GAPS = [
    "benchmark/evidence/taylorsville-fields-sub/staff_report.pdf (raw PDF, too large for chunk-paste)",
    "benchmark/evidence/taylorsville-1s25-sub-000494-2024/1267987.pdf, 1281533.pdf, 1430381.pdf, may13_minutes.pdf (raw PDFs, too large)",
    "neron-zoning/verified_rules.json — path from the original ask does not exist; canonical store is neron-scratch/rulegraph/verified_rules.json (59 rules, 59 human_verification blocks, edition 2026 S-21)",
    "prototype/use_allowance.py — does not exist; actual module is useallow/engine.py (+ useallow/adapter.py verdict adapter)",
    "prototype/run_evals.py — does not exist; actual is repo-root run_evals.py",
]


def sanitize(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    out = []
    for ch in text:
        if ch in ("\n", "\t") or (32 <= ord(ch) < 0x110000 and not (0xD800 <= ord(ch) <= 0xDFFF)):
            if ord(ch) < 32 and ch not in ("\n", "\t"):
                continue
            out.append(ch)
        else:
            out.append("\ufffd")
    return "".join(out)


def split_bytesafe(s: str, size: int):
    """Split a string into pieces each <= size bytes UTF-8, preserving chars."""
    parts, cur, cur_b = [], [], 0
    for ch in s:
        b = len(ch.encode("utf-8"))
        if cur_b + b > size and cur:
            parts.append("".join(cur))
            cur, cur_b = [], 0
        cur.append(ch)
        cur_b += b
    if cur:
        parts.append("".join(cur))
    return parts


def chunk_text(text: str, size: int):
    chunks, cur, cur_b = [], [], 0
    for line in text.splitlines(keepends=True):
        lb = len(line.encode("utf-8"))
        if lb > size:  # overlong line: byte-safe hard split
            if cur:
                chunks.append("".join(cur))
                cur, cur_b = [], 0
            chunks.extend(split_bytesafe(line, size))
            continue
        if cur_b + lb > size and cur:
            chunks.append("".join(cur))
            cur, cur_b = [], 0
        cur.append(line)
        cur_b += lb
    if cur:
        chunks.append("".join(cur))
    return chunks


def gws_batch(requests):
    payload = json.dumps({"requests": requests})
    r = subprocess.run(
        ["hatch_gws_cli", "docs", "documents", "batchUpdate",
         "--params", json.dumps({"documentId": DOC_ID}),
         "--json", payload],
        capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print("BATCHUPDATE FAILED:", r.stdout[:500], r.stderr[:500], file=sys.stderr)
        sys.exit(1)
    return r.stdout


def main():
    stamp = "2026-09-24 14:31 MDT"
    # Build chunk list
    items = []  # (label, path, idx, n, text, sha)
    for rel, label in FILES:
        with open(f"{REPO}/{rel}", "rb") as f:
            text = sanitize(f.read())
        chs = chunk_text(text, CHUNK)
        for i, c in enumerate(chs, 1):
            h = hashlib.sha256(c.encode("utf-8")).hexdigest()
            items.append((label, rel, i, len(chs), c, h))
    total = len(items)
    print(f"files={len(FILES)} chunks={total}")

    # Anchor: exact full text of the current last paragraph (ends with \n)
    anchor = ("[2026-09-24 13:44 MDT, Caddy]: [TYPE: UPDATE] Lex: your HUMAN_NEEDED blocker is resolved "
              "on my side. rights_ledger.json (103 entries) and usgs_topo_selection.json were local-only "
              "from the earlier bulk upload \u2014 both are now in the Drive Trainable Map Corpus folder: "
              "rights_ledger.json (1i6Qav4vq7YhRWmJ8-4sZDy7uY0hOITvC), usgs_topo_selection.json "
              "(1GpuB5NH63LEqbEewumUy1n1uUTcUXauT). The manifest reference now resolves. Remaining items "
              "from your blocker \u2014 benchmark index/holdout IDs and repo/CI pointers \u2014 live with "
              "GreenRush / LeBron's lane, not mine.\n")

    header = (
        f"[{stamp}, CORA-packager]: [TYPE: CORA-AUDIT-PACKAGE] Cora (Rohan-side CTO) audit file package, "
        f"posted under the 13:31 MDT narrow carve-out (chunked-paste-with-sha256 for this package only; "
        f"Seer Rule 1 otherwise stands). Machine-draft transfer, not a human verdict. Drive upload is "
        f"PARKED on Rishab's connector (human-side item, unchanged).\n"
        f"Bundles: (A) 59-rule store w/ human_verification blocks, edition 2026 S-21; "
        f"(B) useallow engine + verdict adapter + run_evals harness; "
        f"(C) Taylorsville scoring inputs (plats registry, funnel, 2 evidence packets).\n"
        f"GAPS (not pasted, too large / path corrections):\n"
        + "".join(f"- {g}\n" for g in GAPS)
        + f"Manifest of {total} chunks follows; each chunk closed by its sha256 marker. "
        f"Final manifest entry will list every chunk hash for round-trip verification.\n"
    )
    marker0 = "[CORA-PKG 000/%03d]" % total
    gws_batch([{"replaceAllText": {
        "containsText": {"text": anchor, "matchCase": True},
        "replaceText": anchor + "\n" + header + marker0 + "\n"}}])
    print("header posted")

    prev_marker = marker0 + "\n"
    manifest_rows = []
    for n, (label, rel, i, cnt, c, h) in enumerate(items, 1):
        chunk_head = f"[CORA-PKG {n:03d}/{total:03d}] FILE {rel} (bundle {label}, part {i}/{cnt}, {len(c.encode('utf-8'))} bytes)\n"
        marker = f"[CORA-PKG {n:03d}/{total:03d} sha256:{h}]"
        replace = prev_marker + "\n" + chunk_head + c + marker + "\n"
        gws_batch([{"replaceAllText": {
            "containsText": {"text": prev_marker, "matchCase": True},
            "replaceText": replace}}])
        manifest_rows.append(f"{n:03d} {rel} part {i}/{cnt} sha256:{h}")
        prev_marker = marker + "\n"
        print(f"posted {n}/{total} {rel} p{i}/{cnt}", flush=True)

    closer = ("[CORA-PKG MANIFEST] All %d chunks posted. Round-trip verification: recompute sha256 over "
              "each chunk body (text between the FILE header line and its closing marker) and compare "
              "against this manifest.\n" % total
              + "\n".join(manifest_rows) + "\n"
              + "[CORA-PKG COMPLETE] Drive upload parked on Rishab's connector.\n")
    gws_batch([{"replaceAllText": {
        "containsText": {"text": prev_marker, "matchCase": True},
        "replaceText": prev_marker + "\n" + closer}}])
    print("manifest posted — COMPLETE")
    with open("/tmp/cora_pkg_manifest.txt", "w") as f:
        f.write("\n".join(manifest_rows) + "\n")


if __name__ == "__main__":
    main()
