"""Evidence-layer round-trip test: the NERON-lane doc transfer, parsed back.

Proves that what NERON receives in the shared Google Doc is machine-readable.
Parses our own 10 evidence-transfer chunk-posts back from the shared doc (via
hatch_gws_cli documents.get -- never the browser), reassembles manifest.json +
index.md + the two sample reports, and validates them against frozen
transfer-time receipts plus the pinned fingerprints.

RECEIPT RULE: every chunk validates byte-for-byte against a frozen
transfer-time receipt in evidence/test_fixtures/ — NEVER against live disk.
The receipt is what the doc carried when the transfer was posted; the test
proves the transfer was faithful AT TRANSFER TIME, even as the live
artifacts evolve afterwards.

Three distinct failure modes, all loud, never a skip:
- DocUnreachableError ("doc unreachable ...") — the doc could not be fetched
  (CLI missing, auth down, timeout, unparsable response).
- AssertionError ("payload corrupt ...") — the doc was reached but a payload
  does not match its transfer-time receipt (posted bytes damaged in transit
  or edited afterwards).
- DocTransferStaleError ("doc transfer stale ...") — the doc payload matches
  its receipt (the transfer was faithful) but the live artifact has moved
  since the transfer; the transfer is STALE, not corrupt. Staleness is only
  tolerated when the artifact is named in KNOWN_STALE_ARTIFACTS — i.e. NERON
  was already notified and a re-transfer is owed. Any unannounced staleness
  escapes as a loud error, never masquerading as corruption.

Freshness scope: chunks 1 (manifest) and 2-8 (index.md) are machine-stable
artifacts and carry a receipt-vs-live-disk freshness check. Chunks 9-10 are
point-in-time report samples and carry no freshness expectation — report
presentation evolves by design; their fixtures prove only that the posted
sample was faithful when posted.

Read-only against the doc. No verdicts, no store/economics/golden writes.
"""

import json
import os
import re
import shutil
import subprocess
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO, "screen", "outputs", "real_slco_v3", "evidence_reports")
MANIFEST_PATH = os.path.join(EVIDENCE_DIR, "manifest.json")
INDEX_PATH = os.path.join(EVIDENCE_DIR, "index.md")
NOSCHEME_SAMPLE = "08223510140000.md"
SCHEME_SAMPLE = "08214000240000.md"
FIXTURES_DIR = os.path.join(REPO, "evidence", "test_fixtures")
FIXTURE_CHUNK1 = os.path.join(FIXTURES_DIR, "transfer_chunk1_manifest.json")
FIXTURE_INDEX = os.path.join(FIXTURES_DIR, "transfer_chunks2_8_index.md")
FIXTURE_CHUNK9 = os.path.join(FIXTURES_DIR, "transfer_chunk9_no_scheme_sample.md")
FIXTURE_CHUNK10 = os.path.join(FIXTURES_DIR, "transfer_chunk10_scheme_head.md")

DOCUMENT_ID = "1-hMIc8yISkD-XkUf3vZWqc8GFDoedJWpz67OQW-63xc"
FETCH_TIMEOUT_S = 120

CHUNK_HEADER = re.compile(
    r"\[D-Wade → NERON, evidence transfer, chunk (\d+)/10\]:"
)
CLOSING_NOTE_HEADER = re.compile(
    r"\[D-Wade → NERON, evidence transfer — closing note\]"
)
TRUNC_MARKER = "> [TRUNCATED BY D-WADE"
FP_LABELS = {
    "rule_store": r"rule store:\s*([0-9a-f]{64})",
    "use_combined": r"combined use pack:\s*([0-9a-f]{64})",
    "use_mu": r"MU use pack:\s*([0-9a-f]{64})",
    "use_m1_os_pl": r"M-1/OS/PL use pack:\s*([0-9a-f]{64})",
}

# Pinned fingerprints (source of truth: the modules that stamp them).
PIN_RULE_STORE = "9cc91ac71f5f1de221b9609291ce264ca33d6c6ba9b98f7e7f898778fd0cfd1c"  # rulegraph/test_rulegraph.py::PINNED_FINGERPRINT
PIN_USE_COMBINED = "02a78aa4a9adeb5b243b3393a76494ecb636aa29f48cc2e9db9fc807214425b3"  # evals/regression.py::PIN_USE_COMBINED
PIN_USE_MU = "bf741fd283b46ee39b937e5a5ff8c04fb5d9b3a3fb7a4a577bb4e3f8eb58bd6c"  # useallow/mu_pack.py::PINNED_MU_PACK_FINGERPRINT
PIN_USE_M1_OS_PL = "5a3a06db51f04b7cefafe57ae9339b44ebdec6e4a3f7404d67687faec4fbc90e"  # useallow/pack.py::PINNED_PACK_FINGERPRINT


class DocUnreachableError(Exception):
    """The shared doc could not be fetched. Distinct from payload corruption."""


class DocTransferStaleError(Exception):
    """The doc payload matches its transfer-time receipt, but the live artifact
    has moved since the transfer. The transfer is STALE, not corrupt —
    distinct from DocUnreachableError and the payload-corrupt AssertionError."""


# Artifacts whose doc transfer is KNOWN-STALE: the doc faithfully carries what
# was posted, but the live file has moved since, and NERON was already
# notified via the doc log (re-transfer offered on request; BACKLOG item
# "doc index chunk re-transfer for NERON"). A re-transfer updates the receipt
# fixture in evidence/test_fixtures/ AND removes the name here.
KNOWN_STALE_ARTIFACTS = frozenset({
    # index.md gained the `rg basis` column after the transfer was posted.
    "index.md",
})


def assert_transfer_fresh(artifact, receipt_text, disk_text):
    """Raise DocTransferStaleError unless the receipt equals live disk.

    Message starts "doc transfer stale" — the third distinct failure mode,
    never "doc unreachable" and never "payload corrupt".
    """
    if receipt_text != disk_text:
        raise DocTransferStaleError(
            "doc transfer stale — re-transfer owed: %s "
            "(the doc faithfully carries what was posted, but the live file "
            "has moved since the transfer)" % artifact
        )


def fetch_doc_text():
    """Fetch the shared doc body as plain text via hatch_gws_cli.

    Raises DocUnreachableError (message starts "doc unreachable") on any
    fetch failure. Never returns partial text, never skips.
    """
    cli = shutil.which("hatch_gws_cli")
    if not cli:
        raise DocUnreachableError("doc unreachable: hatch_gws_cli not on PATH")
    cmd = [
        cli, "docs", "documents", "get",
        "--params", json.dumps({"documentId": DOCUMENT_ID}),
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=FETCH_TIMEOUT_S
        )
    except subprocess.TimeoutExpired as e:
        raise DocUnreachableError(
            "doc unreachable: documents.get timed out after %ss" % FETCH_TIMEOUT_S
        ) from e
    except OSError as e:
        raise DocUnreachableError("doc unreachable: exec failed: %s" % e) from e
    if proc.returncode != 0:
        raise DocUnreachableError(
            "doc unreachable: documents.get exit=%s stderr=%s"
            % (proc.returncode, proc.stderr[:500])
        )
    try:
        doc = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise DocUnreachableError(
            "doc unreachable: documents.get returned unparsable JSON: %s" % e
        ) from e
    parts = []

    def walk(node):
        if isinstance(node, dict):
            tr = node.get("textRun")
            if isinstance(tr, dict) and "content" in tr:
                parts.append(tr["content"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(doc.get("body", {}))
    text = "".join(parts)
    if not text.strip():
        raise DocUnreachableError("doc unreachable: empty body text returned")
    return text


def extract_chunk_payload(segment):
    """Extract the fenced payload from one chunk's doc segment.

    Segment layout: header, blank line, ``` fence line, payload lines,
    closing ``` fence line (which shares its line with the next header).
    Payloads may themselves contain ``` lines, so the payload is everything
    between the FIRST and LAST fence lines of the segment.
    """
    lines = segment.split("\n")
    fence_idx = [i for i, l in enumerate(lines) if l.startswith("```")]
    if len(fence_idx) < 2:
        raise ValueError(
            "payload corrupt: fewer than 2 fence lines in chunk segment "
            "(head: %r)" % segment[:120]
        )
    body = lines[fence_idx[0]:fence_idx[-1]]
    body[0] = body[0][3:]  # strip the opening fence token itself
    return "\n".join(body)


def parse_transfer(text):
    """Locate the 10 chunk-posts + closing note; return (chunks, closing).

    chunks: dict "1".."10" -> raw payload string (still fence-wrapped with
    the wrapper newlines; callers normalize per artifact).
    """
    headers = list(CHUNK_HEADER.finditer(text))
    if len(headers) != 10:
        raise ValueError(
            "payload corrupt: expected 10 evidence-transfer chunk headers, "
            "found %d" % len(headers)
        )
    nums = [m.group(1) for m in headers]
    if nums != [str(n) for n in range(1, 11)]:
        raise ValueError(
            "payload corrupt: chunk headers out of order/duplicated: %r" % nums
        )
    closes = list(CLOSING_NOTE_HEADER.finditer(text))
    if not closes:
        raise ValueError("payload corrupt: closing-note header not found")
    # The header text echoes once on chunk 10's closing-fence line; the real
    # post is the LAST occurrence (it carries ": 10/10 chunks posted." etc.).
    close = closes[-1]
    chunks = {}
    for i, m in enumerate(headers):
        seg_end = headers[i + 1].start() if i + 1 < len(headers) else close.start()
        chunks[m.group(1)] = extract_chunk_payload(text[m.end():seg_end])
    # Closing-note segment runs to the next doc entry (a "[...]:" line).
    tail = text[close.end():]
    nxt = re.search(r"\n\[[^\]\n]{1,80}\]:", tail)
    closing = tail[:nxt.start()] if nxt else tail
    return chunks, closing


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class DocRoundTripTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Fetch once; DocUnreachableError propagates as a loud ERROR (never skip).
        cls.text = fetch_doc_text()
        cls.chunks, cls.closing = parse_transfer(cls.text)

    def test_all_ten_chunks_present_in_order(self):
        self.assertEqual(
            sorted(self.chunks.keys(), key=int),
            [str(n) for n in range(1, 11)],
            "payload corrupt: chunk set != 1..10",
        )

    def test_manifest_matches_transfer_receipt(self):
        # Chunk 1 validates against its frozen transfer-time receipt — never
        # live disk. Post wrapper: header, blank line, ``` fence, newline,
        # then the receipt bytes verbatim. So payload == "\n" + receipt.
        receipt = _read(FIXTURE_CHUNK1)
        payload = self.chunks["1"]
        self.assertEqual(
            payload, "\n" + receipt,
            "payload corrupt: chunk 1 payload != transfer-time manifest receipt "
            "(evidence/test_fixtures/transfer_chunk1_manifest.json)",
        )
        parsed = json.loads(receipt)
        self.assertEqual(parsed["reports"], 500)
        self.assertEqual(
            parsed["counts"], {"error": 0, "no_schemes": 445, "scheme": 55}
        )

    def test_index_matches_transfer_receipt(self):
        # Parts were split at line boundaries with no trailing newline; the
        # reassembly is "\n".join(parts) + the file's trailing newline.
        # Validates against the frozen transfer-time receipt (what the doc
        # carried when posted) — never live disk; staleness is a separate
        # check (test_transfer_freshness_is_labeled_distinctly).
        parts = [self.chunks[str(n)].strip("\n") for n in range(2, 9)]
        reassembled = "\n".join(parts) + "\n"
        receipt = _read(FIXTURE_INDEX)
        self.assertEqual(
            reassembled, receipt,
            "payload corrupt: chunks 2-8 do not reassemble to the transfer-time "
            "index.md receipt (evidence/test_fixtures/transfer_chunks2_8_index.md)",
        )
        rows = re.findall(r"^\| \[`", receipt, re.M)
        self.assertEqual(len(rows), 500,
                         "payload corrupt: receipt index has %d per-parcel rows, "
                         "want 500" % len(rows))
        ok = len(re.findall(r"^\| \[`[^`]+`\]\(./[^)]+\) \| `ok`", receipt, re.M))
        nos = len(re.findall(r"no_schemes_generated", receipt))
        self.assertEqual((ok, nos), (55, 445),
                         "payload corrupt: receipt index row split %d ok / %d "
                         "no-scheme != manifest 55/445" % (ok, nos))

    def test_transfer_freshness_is_labeled_distinctly(self):
        # THIRD failure mode: receipt-vs-live-disk freshness. The doc payload
        # matches its receipt (the transfer was faithful), but the live
        # artifact may have moved since. That is staleness —
        # DocTransferStaleError — never "payload corrupt". An artifact is only
        # tolerated stale when named in KNOWN_STALE_ARTIFACTS (NERON notified,
        # re-transfer owed); unannounced staleness escapes as a loud error.
        artifacts = {
            "manifest.json": (_read(FIXTURE_CHUNK1), _read(MANIFEST_PATH)),
            "index.md": (_read(FIXTURE_INDEX), _read(INDEX_PATH)),
        }
        for name, (receipt, disk) in artifacts.items():
            try:
                assert_transfer_fresh(name, receipt, disk)
            except DocTransferStaleError:
                self.assertIn(
                    name, KNOWN_STALE_ARTIFACTS,
                    "UNANNOUNCED staleness: the %s transfer is stale but %s is "
                    "not in KNOWN_STALE_ARTIFACTS — notify NERON or re-transfer"
                    % (name, name),
                )
            else:
                self.assertNotIn(
                    name, KNOWN_STALE_ARTIFACTS,
                    "%s is fresh again but still listed in KNOWN_STALE_ARTIFACTS "
                    "— remove it now that the re-transfer has landed" % name,
                )

    def test_no_scheme_sample_matches_transfer_receipt(self):
        # Chunk 9's sample is frozen as a transfer-time receipt: the doc must
        # still carry exactly the bytes that were posted, even as the live
        # report generator evolves. Internal consistency: it is a complete
        # report (banner + provenance footer present).
        payload = self.chunks["9"]
        receipt = _read(FIXTURE_CHUNK9)
        self.assertEqual(
            payload, receipt,
            "payload corrupt: chunk 9 payload != transfer-time receipt "
            "(evidence/test_fixtures/transfer_chunk9_no_scheme_sample.md)",
        )
        self.assertIn("08223510140000", payload)
        self.assertTrue(
            payload.lstrip("\n").startswith("# Evidence report — parcel"),
            "payload corrupt: chunk 9 receipt lacks the report banner",
        )
        self.assertIn(
            "## 7. Provenance footer", payload,
            "payload corrupt: chunk 9 receipt lacks the provenance footer",
        )

    def test_scheme_sample_truncation_marker(self):
        # Chunk 10's sample is frozen as a transfer-time receipt: the doc must
        # still carry exactly the bytes that were posted. The receipt
        # self-validates: the marker's byte counts must match the carried
        # head length, and it must name the cut rule / cut sections.
        payload = self.chunks["10"]
        receipt = _read(FIXTURE_CHUNK10)
        self.assertEqual(
            payload, receipt,
            "payload corrupt: chunk 10 payload != transfer-time receipt "
            "(evidence/test_fixtures/transfer_chunk10_scheme_head.md)",
        )
        self.assertIn(
            TRUNC_MARKER, payload,
            "payload corrupt: TRUNCATED marker missing from chunk 10 receipt",
        )
        marker = payload[payload.index(TRUNC_MARKER):]
        # The marker must name the cut sections, not just say "truncated".
        self.assertIn("M-1-03", marker,
                      "payload corrupt: marker does not name the first cut rule")
        self.assertIn("4-7", marker,
                      "payload corrupt: marker does not name the cut sections")
        m = re.search(r"cut at a section boundary at (\d+) of (\d+) bytes", marker)
        self.assertIsNotNone(
            m, "payload corrupt: marker lacks the '<cut> of <total> bytes' claim")
        cut_at = int(m.group(1))
        carried, _, _ = payload.partition(TRUNC_MARKER)
        carried = carried[1:]  # drop the wrapper newline after the fence
        # The marker's claimed cut point must split the receipt into content
        # bytes + whitespace-only wrapper padding (same split the original
        # live-file test asserted at transfer time).
        self.assertGreater(
            len(carried), cut_at,
            "payload corrupt: receipt shorter than its claimed cut point",
        )
        rest = carried[cut_at:]
        self.assertEqual(
            rest.strip(), "",
            "payload corrupt: non-whitespace between cut point and marker: %r"
            % rest[:80],
        )
        self.assertTrue(
            carried[:cut_at].strip(),
            "payload corrupt: no content bytes before the claimed cut point",
        )
        self.assertTrue(
            carried.startswith("# Evidence report — parcel `08214000240000`"),
            "payload corrupt: chunk 10 receipt head is not the scheme sample",
        )
        self.assertIn("08214000240000", carried)

    def test_fingerprints_parse_and_match_pins(self):
        fps = {}
        for name, pat in FP_LABELS.items():
            m = re.search(pat, self.closing)
            self.assertIsNotNone(
                m, "payload corrupt: fingerprint label %r not parsed from closing note"
                % name)
            fps[name] = m.group(1)
        # Expected values computed LIVE from the canonical fingerprint
        # functions — the same values the engine stamps into reports.
        from prototype import pipeline as P  # noqa: E402
        from useallow import mu_pack, pack as use_pack  # noqa: E402

        live_rule_store = P._rulegraph()[0].fingerprint
        combined, _, _, _ = P._usepack()
        live_combined = combined.fingerprint
        live_mu = mu_pack.load_mu_pack(P._MU_PACK).fingerprint
        live_m1_os_pl = use_pack.load_pack(P._USE_PACK).fingerprint
        live = {
            "rule_store": live_rule_store,
            "use_combined": live_combined,
            "use_mu": live_mu,
            "use_m1_os_pl": live_m1_os_pl,
        }
        pins = {
            "rule_store": PIN_RULE_STORE,
            "use_combined": PIN_USE_COMBINED,
            "use_mu": PIN_USE_MU,
            "use_m1_os_pl": PIN_USE_M1_OS_PL,
        }
        for name in FP_LABELS:
            self.assertEqual(
                live[name], pins[name],
                "pin drift: live-computed %s fingerprint != pinned constant "
                "(store or pack changed without a pin update)" % name,
            )
            self.assertEqual(
                fps[name], live[name],
                "payload corrupt: doc %s fingerprint %s != live %s"
                % (name, fps[name][:12], live[name][:12]),
            )


if __name__ == "__main__":
    unittest.main()
