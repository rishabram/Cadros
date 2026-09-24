"""Instrumented driver for the 10k stress test.

Wraps prototype.pipeline.run_pipeline with per-parcel wall-clock timing
(the screener binds run_pipeline at call time, so patching the module
attribute is picked up), samples own RSS every 5 s via /proc/self/statm,
and delegates everything else to screen.screener.screen_manifest.

Outputs (under the chosen --out root):
  screening_results.csv, summary.json   (from the screener, unmodified)
  timings.csv        parcel_id, seconds  (per-parcel pipeline wall clock)
  rss_profile.csv    t_seconds, rss_mb   (own RSS sampled every 5 s)
  stress_meta.json   peak_rss_mb (getrusage), timing stats, run config

Usage:
  venv/bin/python -m stress.run_stress --limit 200 --out stress/outputs/pilot
  venv/bin/python -m stress.run_stress --out stress/outputs/full   # all 10k
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import resource
import statistics
import sys
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRATCH = os.path.dirname(_HERE)
if _SCRATCH not in sys.path:
    sys.path.insert(0, _SCRATCH)


def _rss_mb() -> float:
    with open("/proc/self/statm") as f:
        pages = int(f.read().split()[1])
    return pages * os.sysconf("SC_PAGE_SIZE") / 1e6


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest",
                    default=os.path.join(_HERE, "manifest_10k.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None,
                    help="run only the first N manifest entries (pilot)")
    ap.add_argument("--rss-interval", type=float, default=5.0)
    args = ap.parse_args(argv)

    import prototype.pipeline as pipeline_mod
    from screen.screener import screen_manifest

    real_run = pipeline_mod.run_pipeline
    timings = []
    lock = threading.Lock()

    def timed_run(parcel_path, zoning_path, finance_path, out_dir,
                  *a, **kw):
        parcel_id = os.path.basename(os.path.abspath(out_dir))
        t0 = time.perf_counter()
        try:
            return real_run(parcel_path, zoning_path, finance_path,
                            out_dir, *a, **kw)
        finally:
            dt = time.perf_counter() - t0
            with lock:
                timings.append((parcel_id, dt))

    pipeline_mod.run_pipeline = timed_run

    rss_rows = []
    stop = threading.Event()
    t_start = time.perf_counter()

    def monitor():
        while not stop.wait(args.rss_interval):
            rss_rows.append((time.perf_counter() - t_start, _rss_mb()))

    mon = threading.Thread(target=monitor, daemon=True)
    mon.start()

    manifest = args.manifest
    if args.limit is not None:
        with open(manifest) as f:
            m = json.load(f)
        m = dict(m)
        m["parcels"] = m["parcels"][:args.limit]
        m["_note"] = (m.get("_note", "") +
                      f" [sliced to first {args.limit} by run_stress]")
        manifest = os.path.join(args.out, "_sliced_manifest.json")
        os.makedirs(args.out, exist_ok=True)
        with open(manifest, "w") as f:
            json.dump(m, f)

    wall0 = time.perf_counter()
    try:
        screen_manifest(manifest, out_root=args.out)
    finally:
        wall = time.perf_counter() - wall0
        stop.set()
        mon.join(timeout=10)

    with lock:
        ordered = sorted(timings, key=lambda t: t[0])
    durs = [d for _, d in ordered]
    durs_sorted = sorted(durs)

    def pct(p):
        if not durs_sorted:
            return None
        i = min(len(durs_sorted) - 1, int(p / 100 * len(durs_sorted)))
        return round(durs_sorted[i], 3)

    with open(os.path.join(args.out, "timings.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["parcel_id", "seconds"])
        for pid, d in ordered:
            w.writerow([pid, f"{d:.3f}"])
    with open(os.path.join(args.out, "rss_profile.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_seconds", "rss_mb"])
        for t, r in rss_rows:
            w.writerow([f"{t:.1f}", f"{r:.1f}"])

    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    meta = {
        "manifest": os.path.abspath(args.manifest),
        "limit": args.limit,
        "parcels_timed": len(durs),
        "wall_seconds": round(wall, 1),
        "per_parcel_seconds": {
            "min": round(min(durs), 3) if durs else None,
            "median": round(statistics.median(durs), 3) if durs else None,
            "p95": pct(95),
            "p99": pct(99),
            "max": round(max(durs), 3) if durs else None,
            "mean": round(statistics.fmean(durs), 3) if durs else None,
        },
        "peak_rss_mb_getrusage": round(peak_rss, 1),
        "rss_profile_samples": len(rss_rows),
        "rss_profile_max_sampled_mb": (round(max(r for _, r in rss_rows), 1)
                                       if rss_rows else None),
        "note": ("Single process, this VM (shared with other worker lanes); "
                 "single-run observation, not a tuned benchmark."),
    }
    with open(os.path.join(args.out, "stress_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
