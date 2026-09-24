"""Delta report: real_slco_v4 (pre-MU-overlay) vs real_slco_v5 (post-MU-overlay).

Usage: venv/bin/python -m screen.delta_report_v4v5
Writes screen/outputs/rescreen_delta_v4_v5.md and prints the headline table.

Honest comparison rules:
- Economics must be byte-identical (geometry/proforma untouched by overlay).
- Scheme verdicts are joined on (parcel_id, scheme_id).
- Rule-level outcomes are read from per-scheme report.json rulegraphs.
- UNKNOWN reasons are aggregated from v5 reasons verbatim; no invented causes.
"""
import csv
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V4 = os.path.join(ROOT, "screen", "outputs", "real_slco_v4")
V5 = os.path.join(ROOT, "screen", "outputs", "real_slco_v5")
OUT_MD = os.path.join(ROOT, "screen", "outputs", "rescreen_delta_v4_v5.md")


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def key(r):
    return (r["parcel_id"], r["scheme_id"])


def si(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def main():
    old = {key(r): r for r in load_csv(os.path.join(V4, "screening_results.csv"))}
    new = {key(r): r for r in load_csv(os.path.join(V5, "screening_results.csv"))}
    common = sorted(set(old) & set(new))
    only_old = sorted(set(old) - set(new))
    only_new = sorted(set(new) - set(old))
    # only scheme rows carry rulegraph verdicts; diagnostic rows are empty
    scored = [k for k in common if old[k]["rg_verdict"] and new[k]["rg_verdict"]]

    lines = ["# Rescreen delta: real_slco_v4 -> real_slco_v5",
             "",
             "Caddy extraction v2 (MU) param overlay applied in-memory at RuleGraph "
             "load (32 MU rules executable; MU-5-09/MU-6-09/MU-OPENSPACE-01 remain "
             "evaluator-less; canonical store + fingerprint untouched).",
             "",
             f"- scheme rows compared: {len(scored)} (raw rows: {len(common)}; "
             f"v4-only: {len(only_old)}, v5-only: {len(only_new)})"]

    # --- economics identity ---
    econ_cols = ["lots", "road_ft", "revenue", "total_cost", "profit",
                 "margin"]
    econ_diffs = 0
    for k in scored:
        for c in econ_cols:
            if old[k][c] != new[k][c]:
                econ_diffs += 1
                break
    lines.append(f"- economics identical across all compared schemes: "
                 f"{'YES' if econ_diffs == 0 else f'NO ({econ_diffs} differ)'}")

    # --- scheme-level verdict transitions ---
    trans = Counter()
    trans_by_district = defaultdict(Counter)
    unk_delta = []
    pass_delta = []
    for k in scored:
        a, b = old[k]["rg_verdict"], new[k]["rg_verdict"]
        trans[(a, b)] += 1
        trans_by_district[old[k]["district"]][(a, b)] += 1
        uo, un = si(old[k]["rg_unknown"]), si(new[k]["rg_unknown"])
        if uo is not None and un is not None:
            unk_delta.append(un - uo)
        po, pn = si(old[k]["rg_pass"]), si(new[k]["rg_pass"])
        if po is not None and pn is not None:
            pass_delta.append(pn - po)
    lines += ["",
              "## Scheme-level rg_verdict transitions (v4 -> v5)",
              "",
              "| v4 | v5 | schemes |",
              "|---|---|---|"]
    for (a, b), n in trans.most_common():
        lines.append(f"| {a} | {b} | {n} |")
    lines += ["",
              "### By district",
              "",
              "| district | UNKNOWN->UNKNOWN | UNKNOWN->PASS | UNKNOWN->FAIL | "
              "PASS->PASS | other |"]
    for d in sorted(trans_by_district):
        c = trans_by_district[d]
        uu = c.get(("UNKNOWN", "UNKNOWN"), 0)
        up = c.get(("UNKNOWN", "PASS"), 0)
        uf = c.get(("UNKNOWN", "FAIL"), 0)
        pp = c.get(("PASS", "PASS"), 0)
        other = sum(n for t, n in c.items()
                    if t not in {("UNKNOWN", "UNKNOWN"), ("UNKNOWN", "PASS"),
                                 ("UNKNOWN", "FAIL"), ("PASS", "PASS")})
        lines.append(f"| {d} | {uu} | {up} | {uf} | {pp} | {other} |")
    import statistics
    lines += ["",
              f"- mean rg_unknown change per scheme: "
              f"{statistics.mean(unk_delta):+.2f}",
              f"- mean rg_pass change per scheme: "
              f"{statistics.mean(pass_delta):+.2f}"]

    # --- rule-level transitions ---
    rule_trans = Counter()
    reason_samples = defaultdict(Counter)
    n_schemes_with_rules = 0
    for k in scored:
        po = os.path.join(V4, k[0], "report.json")
        pn = os.path.join(V5, k[0], "report.json")
        if not (os.path.exists(po) and os.path.exists(pn)):
            continue
        ro = json.load(open(po))
        rn = json.load(open(pn))
        go = {s["scheme_id"]: {o["rule_id"]: o for o in s["rulegraph"]}
              for s in ro["schemes"]}
        gn = {s["scheme_id"]: {o["rule_id"]: o for o in s["rulegraph"]}
              for s in rn["schemes"]}
        if k[1] not in go or k[1] not in gn:
            continue
        n_schemes_with_rules += 1
        for rid, oo in go[k[1]].items():
            on = gn[k[1]].get(rid)
            if on is None:
                continue
            a, b = oo["outcome"], on["outcome"]
            if a != b:
                rule_trans[(rid, a, b)] += 1
            if b == "UNKNOWN" and on.get("applicable"):
                reason_samples[rid][on["reason"][:90]] += 1
    lines += ["",
              f"## Rule-level outcome changes ({n_schemes_with_rules} schemes "
              "with rulegraphs)",
              "",
              "| rule | v4 | v5 | schemes |",
              "|---|---|---|---|"]
    for (rid, a, b), n in rule_trans.most_common(40):
        lines.append(f"| {rid} | {a} | {b} | {n} |")
    if not rule_trans:
        lines.append("| (none) | | | |")
    lines += ["",
              "## Remaining UNKNOWN: top reasons in v5 (applicable rules)",
              ""]
    for rid in sorted(reason_samples,
                      key=lambda r: -sum(reason_samples[r].values()))[:15]:
        total = sum(reason_samples[rid].values())
        top = reason_samples[rid].most_common(1)[0]
        lines.append(f"- **{rid}** ({total}): {top[0]}... x{top[1]}")

    md = "\n".join(lines) + "\n"
    with open(OUT_MD, "w") as f:
        f.write(md)
    print(md)
    print("wrote", OUT_MD)


if __name__ == "__main__":
    main()
