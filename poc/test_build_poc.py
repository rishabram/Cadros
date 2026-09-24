"""Tests for poc/build_poc.py (NERON POC single-file HTML builder).

The coverage sweep found this was the only genuinely untested first-party
module (everything else is imported by at least one test). It is a script
with import-time side effects, so these tests run it as a subprocess and
assert on the built artifact — the audit-round-2 finding (stale labels,
canned numbers unlabeled) is exactly what this pins down.

Produces and implies no human verdicts.
"""
import json
import os
import re
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "poc", "build_poc.py")
OUT = os.path.join(REPO, "poc", "neron_poc.html")
PY = os.path.join(REPO, "venv", "bin", "python")


def _build():
    proc = subprocess.run(
        [PY, SCRIPT], capture_output=True, text=True, cwd=REPO, timeout=120
    )
    assert proc.returncode == 0, "build_poc.py failed: %s" % proc.stderr[-2000:]
    with open(OUT, encoding="utf-8") as f:
        return f.read()


def _import_freshness():
    sys.path.insert(0, os.path.join(REPO, "poc"))
    import input_freshness

    return input_freshness


class TestBuildPoc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = _build()

    def test_builds_and_is_deterministic(self):
        # A second build from the same inputs must be byte-identical.
        again = _build()
        self.assertEqual(again, self.page)

    def test_embedded_rules_parse(self):
        m = re.search(r"const RULES = (\[.*?\]);\n", self.page, re.S)
        self.assertIsNotNone(m, "embedded RULES blob missing")
        rules = json.loads(m.group(1))
        self.assertEqual(len(rules), 59)
        ids = {r["rule_id"] for r in rules}
        self.assertEqual(len(ids), 59)

    def test_embedded_uses_parse(self):
        m = re.search(r"const USES = (\[.*?\]);\n", self.page, re.S)
        self.assertIsNotNone(m, "embedded USES blob missing")
        uses = json.loads(m.group(1))
        self.assertEqual(len(uses), 513)
        dists = {u["district"] for u in uses}
        self.assertTrue({"M-1", "OS", "PL", "MU-5", "MU-6", "MU-11"} <= dists)

    def test_no_stale_vocabulary(self):
        # The vocab wave renamed NOT_PERMITTED -> FAIL in the engine; the POC
        # must never resurrect it, and the machine-draft banner must survive.
        self.assertNotIn("NOT_PERMITTED", self.page)
        self.assertIn("MACHINE DRAFT", self.page)
        self.assertIn("Not a compliance finding", self.page)

    def test_provisional_labeling_present(self):
        self.assertIn("provisional", self.page.lower())
        self.assertIn("canned demo numbers", self.page)

    def test_banner_carries_input_fingerprints(self):
        # The NERON lane validates fingerprints on receipt; the banner must
        # carry the 12-char prefixes of all three embedded inputs.
        mod = _import_freshness()
        for name, fp in mod.EXPECTED_INPUTS.items():
            self.assertIn(fp[:12], self.page, "banner missing %s fingerprint" % name)

    def test_assert_inputs_fresh_unit(self):
        mod = _import_freshness()
        fps = mod.EXPECTED_INPUTS
        live = mod.assert_inputs_fresh(fps["rule_store"], fps["pack_m1_os_pl"], fps["pack_mu"])
        self.assertEqual(set(live), set(fps))
        with self.assertRaises(mod.StalePocInputsError):
            mod.assert_inputs_fresh("0" * 64, fps["pack_m1_os_pl"], fps["pack_mu"])

    def test_cross_seed_determinism(self):
        # NERON validates fingerprints on receipt: the build must be
        # byte-identical across PYTHONHASHSEED values (the DXF wave proved
        # hash-randomization breaks cross-process byte-identity; seed 0
        # disables it, any nonzero seed enables it, so 0 vs 12345 is the
        # meaningful axis). Build in a temp dir (same symlink layout as the
        # freshness test) under both seeds and compare sha256.
        import hashlib
        import shutil
        import tempfile

        tmp = tempfile.mkdtemp(prefix="poc_crossseed_", dir=os.path.dirname(REPO))
        try:
            for name in ("rulegraph", "useallow", "caddy_drop"):
                os.symlink(os.path.join(REPO, name), os.path.join(tmp, name))
            poc_copy = os.path.join(tmp, "poc")
            shutil.copytree(
                os.path.join(REPO, "poc"),
                poc_copy,
                ignore=shutil.ignore_patterns("__pycache__", "neron_poc.html"),
            )
            hashes = []
            for seed in ("0", "12345"):
                env = dict(os.environ)
                env["PYTHONHASHSEED"] = seed
                proc = subprocess.run(
                    [PY, os.path.join(poc_copy, "build_poc.py")],
                    capture_output=True,
                    text=True,
                    cwd=tmp,
                    timeout=120,
                    env=env,
                )
                self.assertEqual(
                    proc.returncode, 0, "seed %s build failed: %s" % (seed, proc.stderr[-2000:])
                )
                with open(os.path.join(poc_copy, "neron_poc.html"), "rb") as f:
                    hashes.append(hashlib.sha256(f.read()).hexdigest())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(
            hashes[0],
            hashes[1],
            "build differs across PYTHONHASHSEED (0 vs 12345) — receipt validation would break",
        )

    def test_freshness_gate_blocks_stale_inputs(self):
        # Simulate a store change WITHOUT mutating the real source tree: build
        # a temp dir (sibling of neron-zoning, so the packs' default paths
        # resolve) with symlinks to the real rulegraph/useallow/caddy_drop,
        # plus a copy of poc/ whose input_freshness.py carries a wrong pin.
        # The copied build must fail loudly naming the stale input — never
        # write a stale HTML. (An earlier version of this test tampered the
        # real file in place; that breaks parallel test runs, because two
        # unittest processes share the file — found the hard way when a
        # concurrent discover run's tamper window failed this file's own
        # setUpClass build.)
        import shutil
        import tempfile

        mod = _import_freshness()
        tmp = tempfile.mkdtemp(prefix="poc_freshness_", dir=os.path.dirname(REPO))
        try:
            for name in ("rulegraph", "useallow", "caddy_drop"):
                os.symlink(os.path.join(REPO, name), os.path.join(tmp, name))
            poc_copy = os.path.join(tmp, "poc")
            shutil.copytree(
                os.path.join(REPO, "poc"),
                poc_copy,
                ignore=shutil.ignore_patterns("__pycache__", "neron_poc.html"),
            )
            fresh_path = os.path.join(poc_copy, "input_freshness.py")
            with open(fresh_path, encoding="utf-8") as f:
                content = f.read()
            tampered = content.replace(mod.EXPECTED_INPUTS["rule_store"], "0" * 64, 1)
            self.assertNotEqual(tampered, content, "pin replacement missed")
            with open(fresh_path, "w", encoding="utf-8") as f:
                f.write(tampered)
            proc = subprocess.run(
                [PY, os.path.join(poc_copy, "build_poc.py")],
                capture_output=True,
                text=True,
                cwd=tmp,
                timeout=120,
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertNotEqual(proc.returncode, 0, "stale build must fail loudly")
        self.assertIn("StalePocInputsError", proc.stderr)
        self.assertIn("rule_store", proc.stderr)
        self.assertIn("BUILD_DATE", proc.stderr)


if __name__ == "__main__":
    unittest.main()
