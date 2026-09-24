#!/usr/bin/env python3
"""evals/regression.py — automated regression harness for frozen baselines.

Runs the manual baseline checks from the canonical-integration wave as one
command, so a store change can never silently move a baseline again.

Semantics (standing NERON rules)
--------------------------------
- Geometry + economics are BYTE-IDENTITY assertions: any change is a FAILURE.
- Compliance verdicts (RuleGraph / use-allowance) are FINDINGS: recorded every
  run, compared against the pinned record; a change is reported, never a
  failure. (Knowledge pool: "A compliance-verdict change is a finding, not a
  failure.")
- Store fingerprints are recorded in every report; a fingerprint that does not
  match its test-suite pin is a FAILURE (tamper-evidence).

Modes
-----
- ``--mode fast`` (CI): golden replays (01-03 + bad_01), synthetic + edits
  evals, fingerprint pins. No pipeline file runs (~10s).
- ``--mode full``: everything in fast, plus the demo and Jefferson pipeline
  runs with baseline assertions and verdict recording (~20s).

Exit code: 0 iff zero real failures. Findings never affect the exit code.

Usage:
    venv/bin/python -m evals.regression --mode fast
    venv/bin/python -m evals.regression --mode full --out evals/regression_last.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import tempfile
from collections import Counter
from typing import Any, Dict, List

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import run_evals as E  # noqa: E402
from prototype import pipeline as P  # noqa: E402
from rulegraph.fingerprint import canonical_hash  # noqa: E402

# Fingerprint pins — MUST match the pins in the unit-test suite
# (rulegraph/test_rulegraph.py::PINNED_FINGERPRINT,
#  useallow/test_pack.py::PINNED_PACK_FINGERPRINT and the MU/combined pins).
# A legitimate store change updates both places together.
PIN_RULE_STORE = "9cc91ac71f5f1de221b9609291ce264ca33d6c6ba9b98f7e7f898778fd0cfd1c"
PIN_USE_M1_OS_PL = "5a3a06db51f04b7cefafe57ae9339b44ebdec6e4a3f7404d67687faec4fbc90e"
PIN_USE_MU = "bf741fd283b46ee39b937e5a5ff8c04fb5d9b3a3fb7a4a577bb4e3f8eb58bd6c"
PIN_USE_COMBINED = "02a78aa4a9adeb5b243b3393a76494ecb636aa29f48cc2e9db9fc807214425b3"

# Geometry + economics baselines (byte-identity; tolerances are sub-cent).
BASELINES = {
    "demo": {
        "parcel": "inputs/demo_parcel.geojson",
        "zoning": "inputs/zoning.json",
        "finance": "inputs/finance.json",
        "program": "inputs/demo_program.json",
        "max_schemes": 8,
        "lots": 11,
        "profit": 634700.0,
        "margin": 0.6074,
    },
    "jefferson": {
        "parcel": "inputs/jefferson_parcel.geojson",
        "zoning": "inputs/jefferson_zoning.json",
        "finance": "inputs/jefferson_finance.json",
        "program": None,
        "max_schemes": 8,
        "lots": 4,
        "profit": 602392.32,
        "margin": 0.814,
    },
}

VERDICT_PINS_PATH = os.path.join(BASE, "evals", "regression_verdict_pins.json")


def check_fingerprints(report: Dict) -> None:
    """Fingerprint pins — FAILURE on mismatch (tamper-evidence).

    The rule-store fingerprint is taken from the loaded RuleGraph object
    (``canonical_hash({"rules": rules})``) — exactly what the engine stamps
    on every evaluation — not from the raw file bytes.
    """
    graph, _rg_adapter = P._rulegraph()
    store_fp = graph.fingerprint
    combined, _a, _e, parts = P._usepack()
    fps = {
        "rule_store": store_fp,
        "use_m1_os_pl": parts["m1_os_pl"],
        "use_mu": parts["mu"],
        "use_combined": combined.fingerprint,
    }
    report["fingerprints"] = fps
    pins = {
        "rule_store": PIN_RULE_STORE,
        "use_m1_os_pl": PIN_USE_M1_OS_PL,
        "use_mu": PIN_USE_MU,
        "use_combined": PIN_USE_COMBINED,
    }
    for name, pin in pins.items():
        ok = fps[name] == pin
        report["checks"].append({
            "check": f"fingerprint:{name}",
            "status": "PASS" if ok else "FAIL",
            "detail": f"{fps[name][:12]}… == pin" if ok
                      else f"MISMATCH: got {fps[name][:16]}…, pin {pin[:16]}…",
        })


def check_goldens(report: Dict) -> None:
    """Golden replays via run_evals; real failures are harness FAILURES."""
    rows: List[E.Row] = []
    golden_paths: Dict[str, str] = {}
    for pat in (os.path.join(BASE, "inputs", "golden", "*.json"),
                os.path.join(BASE, "inputs", "golden_*.json")):
        for path in glob.glob(pat):
            golden_paths[os.path.basename(path)] = path
    for path in sorted(golden_paths.values()):
        with open(path) as f:
            probe = json.load(f)
        if probe.get("meta", {}).get("bad_fixture"):
            rows.extend(E.eval_bad_geometry(path))
        else:
            rows.extend(E.eval_golden(path))
    rows.extend(E.eval_synthetic())
    rows.extend(E.eval_edits())
    counts = E.classify_rows(rows)
    report["run_evals"] = {
        "checks": len(rows),
        "passed": counts["passed"],
        "by_design": counts["by_design"],
        "n_a": counts["n_a"],
        "real_failures": counts["real_failures"],
    }
    real = [
        (c, m) for c, m, _s, _t, st in rows
        if st == "FAIL" and not E.is_by_design_failure(c, m)
    ]
    for case, metric in real:
        report["checks"].append({
            "check": f"golden:{case}:{metric}",
            "status": "FAIL",
            "detail": "real failure in golden/eval replay",
        })
    report["checks"].append({
        "check": "goldens:real_failures==0",
        "status": "PASS" if not real else "FAIL",
        "detail": f"{len(rows)} checks: {counts['passed']} passed, "
                  f"{counts['by_design']} by design, {counts['n_a']} n/a",
    })


def _run_baseline(name: str, spec: Dict, report: Dict) -> Dict[str, Counter]:
    """Run one baseline project; assert geometry+economics byte-identity."""
    tmp = tempfile.mkdtemp(prefix=f"regression_{name}_")
    res = P.run_pipeline(
        os.path.join(BASE, spec["parcel"]),
        os.path.join(BASE, spec["zoning"]),
        os.path.join(BASE, spec["finance"]),
        tmp,
        max_schemes=spec["max_schemes"],
        building_program=(os.path.join(BASE, spec["program"])
                          if spec["program"] else None),
    )
    top = res["ranked"][0]
    prof = res["proformas"][top.scheme_id]
    lots = len(top.lots)
    ok_lots = lots == spec["lots"]
    ok_profit = abs(prof.profit - spec["profit"]) < 0.01
    ok_margin = abs(prof.margin - spec["margin"]) < 0.00005
    ok = ok_lots and ok_profit and ok_margin
    report["checks"].append({
        "check": f"baseline:{name}",
        "status": "PASS" if ok else "FAIL",
        "detail": (f"lots={lots} profit=${prof.profit:,.2f} "
                   f"margin={prof.margin:.4f}"),
    })
    rg = Counter(s.get("rulegraph_verdict") for s in res["report"]["schemes"])
    use = Counter(s.get("use_verdict") for s in res["report"]["schemes"])
    return {"rulegraph": rg, "use_allowance": use}


def check_verdicts(report: Dict, observed: Dict[str, Dict[str, Counter]]) -> None:
    """Verdict distributions are FINDINGS, never failures.

    Compared against evals/regression_verdict_pins.json (created on first
    run from observed values). Any change is reported as a finding.
    """
    serial = {
        name: {k: dict(v) for k, v in kinds.items()}
        for name, kinds in observed.items()
    }
    report["verdicts_observed"] = serial
    if not os.path.exists(VERDICT_PINS_PATH):
        with open(VERDICT_PINS_PATH, "w") as f:
            json.dump({"pinned_on": "2026-09-24",
                       "distributions": serial}, f, indent=2, sort_keys=True)
        report["findings"].append(
            "verdict pins established on this run "
            f"({VERDICT_PINS_PATH}); future changes will be findings")
        return
    with open(VERDICT_PINS_PATH) as f:
        pinned = json.load(f)["distributions"]
    for name, kinds in serial.items():
        for kind, dist in kinds.items():
            old = pinned.get(name, {}).get(kind)
            if old != dist:
                report["findings"].append(
                    f"verdict change [{name}/{kind}]: "
                    f"{old} -> {dist}")


def run(mode: str = "fast") -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "mode": mode,
        "checks": [],
        "findings": [],
    }
    check_fingerprints(report)
    check_goldens(report)
    if mode == "full":
        observed: Dict[str, Dict[str, Counter]] = {}
        for name, spec in BASELINES.items():
            observed[name] = _run_baseline(name, spec, report)
        check_verdicts(report, observed)
    else:
        report["findings"].append(
            "verdict distributions only recorded in --mode full")
    fails = [c for c in report["checks"] if c["status"] == "FAIL"]
    report["real_failures"] = len(fails)
    report["verdict"] = "FAIL" if fails else "PASS"
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="NERON regression harness")
    ap.add_argument("--mode", choices=("fast", "full"), default="fast")
    ap.add_argument("--out", default=None,
                    help="write JSON report here (default: print only)")
    args = ap.parse_args()
    report = run(args.mode)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(report, f, indent=2, sort_keys=True)
        print(f"report: {args.out}")
    for c in report["checks"]:
        print(f"[{c['status']}] {c['check']} — {c['detail']}")
    for finding in report["findings"]:
        print(f"[FINDING] {finding}")
    fps = report["fingerprints"]
    print(f"fingerprints: rule_store={fps['rule_store'][:12]}… "
          f"use_combined={fps['use_combined'][:12]}…")
    print(f"regression harness: {report['verdict']} "
          f"({report['real_failures']} real failures, "
          f"{len(report['findings'])} findings)")
    return 1 if report["real_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
