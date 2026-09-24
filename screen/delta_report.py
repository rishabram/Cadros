"""Delta report: real_slco_v3 (pre-Caddy-overlay) vs real_slco_v4 (post-overlay).

Usage: venv/bin/python -m screen.delta_report
Writes screen/outputs/rescreen_delta_v3_v4.md and prints the headline table.

Honest comparison rules:
- Economics must be byte-identical (geometry/proforma untouched by overlay).
- Scheme verdicts are joined on (parcel_id, scheme_id).
- Rule-level outcomes are read from per-scheme report.json rulegraphs.
- UNKNOWN reasons are aggregated from v4 reasons verbatim; no invented causes.
"""
import csv
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V3 = os.path.join(ROOT, "screen", "outputs", "real_slco_v3")
V4 = os.path.join(ROOT, "screen", "outputs", "real_slco_v4")
OUT_MD = os.path.join(ROOT, "screen", "outputs", "rescreen_delta_v3_v4.md")


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
    v3 = {key(r): r for r in load_csv(os.path.join(V3, "screening_results.csv"))}
    v4 = {key(r): r for r in load_csv(os.path.join(V4, "screening_results.csv"))}
    common = sorted(set(v3) & set(v4))
    only_v3 = sorted(set(v3) - set(v4))
    only_v4 = sorted(set(v4) - set(v3))
    # only scheme rows carry rulegraph verdicts; diagnostic rows are empty
    scored = [k for k in common if v3[k]["rg_verdict"] and v4[k]["rg_verdict"]]

    lines = ["# Rescreen delta: real_slco_v3 -> real_slco_v4",
             "",
             "Caddy extraction v1 param overlay applied in-memory at RuleGraph "
             "load (10 M-1/OS/PL rules executable; M-1-06/OS-05 remain "
             "evaluator-less; canonical store + fingerprint untouched).",
             "",
             f"- scheme rows compared: {len(scored)} (raw rows: {len(common)}; "
             f"v3-only: {len(only_v3)}, v4-only: {len(only_v4)})"]

    # --- economics identity ---
    econ_cols = ["lots", "road_ft", "revenue", "total_cost", "profit",
                 "margin"]
    econ_diffs = 0
    for k in scored:
        for c in econ_cols:
            if v3[k][c] != v4[k][c]:
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
        a, b = v3[k]["rg_verdict"], v4[k]["rg_verdict"]
        trans[(a, b)] += 1
        trans_by_district[v3[k]["district"]][(a, b)] += 1
        u3, u4 = si(v3[k]["rg_unknown"]), si(v4[k]["rg_unknown"])
        if u3 is not None and u4 is not None:
            unk_delta.append(u4 - u3)
        p3, p4 = si(v3[k]["rg_pass"]), si(v4[k]["rg_pass"])
        if p3 is not None and p4 is not None:
            pass_delta.append(p4 - p3)
    lines += ["",
              "## Scheme-level rg_verdict transitions (v3 -> v4)",
              "",
              "| v3 | v4 | schemes |",
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
        p3 = os.path.join(V3, k[0], "report.json")
        p4 = os.path.join(V4, k[0], "report.json")
        if not (os.path.exists(p3) and os.path.exists(p4)):
            continue
        r3 = json.load(open(p3))
        r4 = json.load(open(p4))
        g3 = {s["scheme_id"]: {o["rule_id"]: o for o in s["rulegraph"]}
              for s in r3["schemes"]}
        g4 = {s["scheme_id"]: {o["rule_id"]: o for o in s["rulegraph"]}
              for s in r4["schemes"]}
        if k[1] not in g3 or k[1] not in g4:
            continue
        n_schemes_with_rules += 1
        for rid, o3 in g3[k[1]].items():
            o4 = g4[k[1]].get(rid)
            if o4 is None:
                continue
            a, b = o3["outcome"], o4["outcome"]
            if a != b:
                rule_trans[(rid, a, b)] += 1
            if b == "UNKNOWN" and o4.get("applicable"):
                reason_samples[rid][o4["reason"][:90]] += 1
    lines += ["",
              f"## Rule-level outcome changes ({n_schemes_with_rules} schemes "
              "with rulegraphs)",
              "",
              "| rule | v3 | v4 | schemes |",
              "|---|---|---|---|"]
    for (rid, a, b), n in rule_trans.most_common(40):
        lines.append(f"| {rid} | {a} | {b} | {n} |")
    if not rule_trans:
        lines.append("| (none) | | | |")
    lines += ["",
              "## Remaining UNKNOWN: top reasons in v4 (applicable rules)",
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
