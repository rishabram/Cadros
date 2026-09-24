#!/usr/bin/env python3
"""run_evals.py — replay all golden projects, score per-metric, print pass/fail.

Phase 0 eval harness (build plan §14). Deterministic: same code + same
fixtures must produce identical scores.

Exit-code policy
----------------
The golden_bad_01 fixture is ADVERSARIAL: its "must FAIL" rows assert the
validator flags known-bad geometry, so a FAIL status on one of those rows is
the assertion succeeding — a failure BY DESIGN, not a defect. A must-FAIL
row with any other status (the validator let bad geometry through), a
golden_bad_01 control row ("must PASS") that FAILs, or a FAIL anywhere
outside golden_bad_01, is a REAL failure.

Exit 0 iff there are no real failures (by-design failures are fine).
Exit 1 iff at least one real failure exists.

The printed summary always distinguishes the two, e.g.:
  "52 checks: 37 passed, 6 failed by design, 9 n/a — no real failures"
Model-dependent metrics report n/a and never fail.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evals import score as S
from evals import synthetic as SYN
from prototype import pipeline

TARGETS = {
    "geometry_iou": 0.90,
    "constraint_satisfaction": 1.00,
    "dxf_validity": 1.00,
    "edit_safety": 1.00,
}

Row = tuple  # (case, metric, score_str, target_str, status)

# Case label used by eval_bad_geometry(). Only rows from this fixture can
# ever be by-design failures.
_ADVERSARIAL_CASE = "golden_bad_01"


def is_by_design_failure(case: str, metric: str) -> bool:
    """True for FAIL rows that are the adversarial harness asserting correctly.

    The golden_bad_01 fixture's bad-case rows are assertions of the form
    "<check> must FAIL" — a FAIL status there means the validator caught the
    bad geometry, which is the desired outcome. Control rows ("must PASS")
    are never by design: they pin the harness against vacuous all-fail.
    """
    return case == _ADVERSARIAL_CASE and "must FAIL" in metric


def classify_rows(rows: list[Row]) -> dict:
    """Split rows into passed / by-design failures / real failures / n/a.

    Returns a dict with counts. A golden_bad_01 "must FAIL" row is by design
    only when its status is FAIL (the validator flagged the bad geometry);
    any other status on such a row means the validator let bad geometry
    through — a real failure. Every other FAIL row is real as well.
    """
    counts = {"passed": 0, "by_design": 0, "real_failures": 0, "n_a": 0}
    for case, metric, _score, _target, status in rows:
        if is_by_design_failure(case, metric):
            if status == "FAIL":
                counts["by_design"] += 1
            else:
                counts["real_failures"] += 1
        elif status == "FAIL":
            counts["real_failures"] += 1
        elif status == "N/A":
            counts["n_a"] += 1
        else:
            counts["passed"] += 1
    return counts


def eval_golden(path: str) -> list[Row]:
    rows: list[Row] = []
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path) as f:
        g = json.load(f)
    exp = g["expected"]
    tmp = tempfile.mkdtemp(prefix="eval_")
    res = pipeline.run_pipeline_objects(
        g["parcel"]["parcel_id"],
        g["parcel"]["boundary"],
        {"crs": g["parcel"].get("crs", "local-feet")},
        g["zoning"],
        g["finance"],
        tmp,
        max_schemes=g["meta"]["max_schemes"],
    )
    report = res["report"]
    ranked, proformas, validations = res["ranked"], res["proformas"], res["validations"]

    def add(metric, ok, score_s, target_s):
        rows.append((name, metric, score_s, target_s, "PASS" if ok else "FAIL"))

    # structural replay checks
    add("scheme_count", len(ranked) == exp["scheme_count"],
        f"{len(ranked)}", f"{exp['scheme_count']}")
    top = ranked[0]
    add("top_scheme_lots", len(top.lots) == exp["top_scheme_lots"],
        f"{len(top.lots)}", f"{exp['top_scheme_lots']}")
    profit = proformas[top.scheme_id].profit
    add("top_scheme_profit", abs(profit - exp["top_scheme_profit"]) < 1.0,
        f"${profit:,.0f}", f"${exp['top_scheme_profit']:,.0f}")
    clean = all(pipeline.validation.scheme_is_clean(v) for v in validations.values())
    add("all_schemes_clean", clean == exp["all_clean"], str(clean), str(exp["all_clean"]))
    add("ranked_order_stable",
        report["ranked_order"] == exp["ranked_order"],
        "match" if report["ranked_order"] == exp["ranked_order"] else "DIFF", "match")

    # §14 metrics
    exp_schemes = {s["scheme_id"]: s for s in exp["schemes"]}
    ious = [
        S.score_geometry_iou(s.lots, exp_schemes[s.scheme_id]["lots"]) for s in ranked
    ]
    mean_iou = sum(ious) / len(ious) if ious else 0.0
    add("geometry_iou (mean)", mean_iou >= TARGETS["geometry_iou"],
        f"{mean_iou:.4f}", f">= {TARGETS['geometry_iou']:.2f}")

    frac, fails, total = S.score_constraint_satisfaction(validations)
    add("constraint_satisfaction", frac >= TARGETS["constraint_satisfaction"],
        f"{frac:.3f} ({total - fails}/{total})", f">= {TARGETS['constraint_satisfaction']:.2f}")

    dxf_paths = [os.path.join(tmp, "schemes", f"{s.scheme_id}.dxf") for s in ranked]
    dfrac, derrs = S.score_dxf_validity(dxf_paths)
    add("dxf_validity (reopen+audit)", dfrac >= TARGETS["dxf_validity"],
        f"{dfrac:.2f}" + ("" if not derrs else f" ERRORS in {len(derrs)} files"),
        f">= {TARGETS['dxf_validity']:.2f}")

    # model-dependent metrics: not wired in scaffold
    for m, fn in (("plan_classification", S.score_plan_classification),
                  ("titleblock_extraction", S.score_titleblock_extraction),
                  ("bearing_transcription", S.score_bearing_transcription)):
        r = fn(None, None)
        rows.append((name, m, "n/a", "—", "N/A"))
    return rows


def eval_bad_geometry(path: str) -> list[Row]:
    """Adversarial fixture: known-invalid geometry the validator MUST reject.

    Rows report the validator's own check verdicts. A FAIL row here is the
    assertion succeeding (the validator caught the bad input); any other
    outcome on a bad case is a genuine harness failure. The control case must
    pass every check, pinning the harness against vacuous all-fail.
    """
    rows: list[Row] = []
    from prototype.schema import Scheme
    from prototype import validation as V
    with open(path) as f:
        g = json.load(f)
    parcel, zoning = g["parcel"]["boundary"], g["zoning"]
    for case in g["bad_cases"]:
        scheme = Scheme(**case["scheme"])
        by_id = {r.rule_id: r for r in V.validate_scheme(scheme, parcel, zoning)}
        for rid in case["must_fail"]:
            r = by_id.get(rid)
            actual = r.status.upper() if r is not None else "MISSING"
            rows.append((
                "golden_bad_01",
                f"{case['case_id']}: {rid} must FAIL",
                r.detail if r else "no such check",
                "validator must flag",
                actual,
            ))
    for case in g.get("good_cases", []):
        scheme = Scheme(**case["scheme"])
        for r in V.validate_scheme(scheme, parcel, zoning):
            rows.append((
                "golden_bad_01",
                f"{case['case_id']} control: {r.rule_id} must PASS",
                r.detail,
                "must PASS",
                r.status.upper(),
            ))
    return rows


def eval_synthetic() -> list[Row]:
    rows: list[Row] = []
    with tempfile.TemporaryDirectory(prefix="synth_") as d1, \
         tempfile.TemporaryDirectory(prefix="synth_") as d2:
        p1 = SYN.generate_cases(5, seed=999, out_dir=d1)
        p2 = SYN.generate_cases(5, seed=999, out_dir=d2)
        h1, h2 = SYN.cases_fingerprint(p1), SYN.cases_fingerprint(p2)
        rows.append(("synthetic", "seeded_determinism",
                     f"{h1}", f"{h2}", "PASS" if h1 == h2 and p1 else "FAIL"))
        # ground-truth self-consistency: regenerate each case's parcel and
        # confirm the stored ground-truth fingerprint reproduces
        ok = True
        for p in p1:
            with open(p) as f:
                case = json.load(f)
            gt = case["ground_truth"]
            from prototype import geometry as G
            schemes = G.generate_schemes(
                case["parcel"]["boundary"], case["zoning"],
                case["parcel"]["parcel_id"], max_schemes=6)
            match = [s for s in schemes if s.fingerprint == gt["fingerprint"]]
            ok = ok and len(match) == 1
        rows.append(("synthetic", "ground_truth_reproducible",
                     f"{len(p1)} cases", "all match", "PASS" if ok else "FAIL"))
    return rows


def eval_edits() -> list[Row]:
    results = S.score_edit_safety()
    return [
        ("edit_safety", k.replace("_", " "), "—", "must hold",
         "PASS" if v else "FAIL")
        for k, v in results.items()
    ]


def main() -> int:
    base = os.path.dirname(os.path.abspath(__file__))
    rows: list[Row] = []
    # Golden fixtures live at inputs/golden_*.json; make_golden.py also writes
    # to inputs/golden/. Search both so the replay suite can never silently
    # run empty (a glob matching nothing used to skip every golden check).
    golden_paths = {}
    for pat in (os.path.join(base, "inputs", "golden", "*.json"),
                os.path.join(base, "inputs", "golden_*.json")):
        for path in glob.glob(pat):
            golden_paths[os.path.basename(path)] = path
    for path in sorted(golden_paths.values()):
        with open(path) as f:
            probe = json.load(f)
        if probe.get("meta", {}).get("bad_fixture"):
            rows.extend(eval_bad_geometry(path))  # adversarial: FAILs are by design
        else:
            rows.extend(eval_golden(path))
    rows.extend(eval_synthetic())
    rows.extend(eval_edits())

    w_case, w_met = 12, 32
    print(f"{'case':<{w_case}} {'metric':<{w_met}} {'score':<28} {'target':<16} status")
    print("-" * (w_case + w_met + 28 + 16 + 8))
    for case, metric, score_s, target_s, status in rows:
        print(f"{case:<{w_case}} {metric:<{w_met}} {score_s:<28} {target_s:<16} {status}")
    print()
    counts = classify_rows(rows)
    summary = (
        f"{len(rows)} checks: {counts['passed']} passed, "
        f"{counts['by_design']} failed by design, {counts['n_a']} n/a"
    )
    if counts["real_failures"]:
        summary += f" — {counts['real_failures']} REAL FAILURES"
    else:
        summary += " — no real failures"
    print(summary)
    print("(by-design failures are golden_bad_01 'must FAIL' rows: the validator "
          "correctly flagging known-bad geometry)")
    return 1 if counts["real_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
