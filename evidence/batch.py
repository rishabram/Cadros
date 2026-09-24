"""Batch per-parcel evidence reports for a mass-screen output directory.

Reads every parcel's report.json under <screen_dir>/<parcel_id>/report.json,
writes one deterministic markdown evidence report per parcel to
<screen_dir>/evidence_reports/<parcel_id>.md, plus an index.md.

Parcel outcomes handled (nothing silently skipped):
  - scheme parcels (status "ok"): full evidence report.
  - no-scheme parcels (status "no_schemes_generated"): diagnostic report
    naming the scheme_generation verdict.
  - error parcels (from summary.json "errors", or report.json status
    "error"): explicit error reports.

Deterministic: parcels processed in sorted order; report content carries
no wall-clock timestamps (see evidence/report.py).

Usage:
    venv/bin/python -m evidence.batch --screen-dir screen/outputs/real_slco_v3 \\
        --store rulegraph/verified_rules.json [--out <dir>]
"""

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from evidence import report as R  # noqa: E402

SUMMARY_FILENAME = "summary.json"
REPORTS_DIRNAME = "evidence_reports"


def _parcel_dirs(screen_dir):
    """Sorted parcel ids that contain a report.json."""
    ids = []
    for name in sorted(os.listdir(screen_dir)):
        pdir = os.path.join(screen_dir, name)
        if os.path.isdir(pdir) and os.path.isfile(os.path.join(pdir, "report.json")):
            ids.append(name)
    return ids


def _money(v):
    return "${:,.0f}".format(v) if v is not None else "n/a"


def build_reports(screen_dir, store_path, out_dir):
    """Generate one markdown report per parcel; return a result manifest.

    Loud on anything unexpected (missing report.json, unreadable JSON):
    a batch that silently dropped a parcel would be worse than one that
    failed.
    """
    with open(store_path) as f:
        store = json.load(f)
    summary_path = os.path.join(screen_dir, SUMMARY_FILENAME)
    with open(summary_path) as f:
        summary = json.load(f)

    parcel_ids = _parcel_dirs(screen_dir)
    if not parcel_ids:
        raise RuntimeError("no parcel report.json files found under {}".format(screen_dir))

    os.makedirs(out_dir, exist_ok=True)
    index_rows = []
    counts = {"scheme": 0, "no_schemes": 0, "error": 0}

    error_by_id = {e["parcel_id"]: e.get("error", "") for e in summary.get("errors", [])}

    for pid in parcel_ids:
        rpath = os.path.join(screen_dir, pid, "report.json")
        with open(rpath) as f:
            rep = json.load(f)
        status = rep.get("status", "")
        schemes = rep.get("schemes") or []
        if pid in error_by_id or status == "error":
            err = error_by_id.get(pid) or rep.get("error") or "unspecified error"
            text = R.generate_error_report(
                pid, err,
                district=(rep.get("zoning") or {}).get("district", "unknown"),
                zone_label=(rep.get("zoning") or {}).get("zone_label", "unknown"),
            )
            kind = "error"
        elif status != "ok" or not schemes:
            text = R.generate_from_objects(rep, store)
            kind = "no_schemes"
        else:
            text = R.generate_from_objects(rep, store)
            kind = "scheme"
        counts[kind] += 1
        out_path = os.path.join(out_dir, pid + ".md")
        with open(out_path, "w") as f:
            f.write(text)
        z = rep.get("zoning") or {}
        top_profit = None
        top = None
        if schemes and rep.get("ranked_order"):
            smap = {s["scheme_id"]: s for s in schemes}
            top = smap.get(rep["ranked_order"][0])
            if top is not None:
                top_profit = (top.get("proforma") or {}).get("profit")
        rgv = top.get("rulegraph_verdict", "n/a") if top else "n/a"
        usev = top.get("use_verdict", "n/a") if top else "n/a"
        # rg_verdict_basis mirrors screen/screener.py's vacuous-PASS
        # qualifier so the index can't be misread: a PASS with zero
        # applicable rules is "no_applicable_rules" (NOT a compliance
        # finding); anything else with a top scheme is "evaluated"; parcels
        # with no top scheme get "".
        applicable = top.get("rulegraph_applicable_rules", "") if top else ""
        if rgv == "PASS" and applicable == 0:
            basis = "no_applicable_rules"
        elif applicable == "":
            basis = ""
        else:
            basis = "evaluated"
        index_rows.append({
            "parcel_id": pid,
            "status": status or ("error" if kind == "error" else "?"),
            "district": z.get("district", "?"),
            "schemes": len(schemes),
            "top_profit": top_profit,
            "rg_verdict": rgv,
            "rg_verdict_basis": basis,
            "use_verdict": usev,
        })

    # Cross-check: every parcel dir got exactly one report — a batch that
    # silently dropped a parcel would be worse than one that failed.
    if len(index_rows) != len(parcel_ids):
        raise RuntimeError("report count mismatch: {} vs {} parcel dirs".format(
            len(index_rows), len(parcel_ids)))

    index_path = os.path.join(out_dir, "index.md")
    with open(index_path, "w") as f:
        f.write("# Evidence reports — `{}`\n\n".format(os.path.basename(screen_dir)))
        f.write("> **{}**\n\n".format(R.MACHINE_DRAFT_LABEL))
        f.write(
            "One deterministic machine-draft evidence report per screened "
            "parcel. `no_schemes` parcels carry their named generation "
            "diagnostic; `error` parcels carry an explicit error report. "
            "UNKNOWN is never treated as a pass anywhere. The `rg basis` "
            "column qualifies the `rg verdict` column: `evaluated` means at "
            "least one store rule applied to the top scheme's district; "
            "`no_applicable_rules` means the PASS verdict has zero "
            "applicable rules — no verified rule covered the district, so "
            "it is NOT a compliance finding.\n\n"
        )
        f.write("| parcel | status | district | schemes | top profit | rg verdict | rg basis | use verdict |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for r in index_rows:
            f.write("| [`{pid}`](./{pid}.md) | `{status}` | `{district}` | {schemes} | {profit} | {rgv} | {basis} | {usev} |\n".format(
                pid=r["parcel_id"], status=r["status"], district=r["district"],
                schemes=r["schemes"], profit=_money(r["top_profit"]),
                rgv=r["rg_verdict"], basis=r["rg_verdict_basis"], usev=r["use_verdict"]))
    manifest = {
        "screen_dir": os.path.abspath(screen_dir),
        "store": os.path.abspath(store_path),
        "out_dir": os.path.abspath(out_dir),
        "reports": len(index_rows),
        "counts": counts,
        "rule_store_fingerprint": R.store_fingerprint(store),
    }
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description="Batch per-parcel evidence reports")
    parser.add_argument("--screen-dir", required=True,
                        help="mass-screen output dir (parcel subdirs with report.json)")
    parser.add_argument("--store", required=True, help="RuleGraph verified_rules.json")
    parser.add_argument("--out", default=None,
                        help="output dir (default: <screen-dir>/evidence_reports)")
    args = parser.parse_args(argv)
    out_dir = args.out or os.path.join(args.screen_dir, REPORTS_DIRNAME)
    manifest = build_reports(args.screen_dir, args.store, out_dir)
    print("wrote {} reports to {}".format(manifest["reports"], manifest["out_dir"]))
    print("counts: {}".format(json.dumps(manifest["counts"], sort_keys=True)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
