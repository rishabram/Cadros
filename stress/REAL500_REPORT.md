# 500-parcel real-shape pipeline measurement — report (LoadRunner-2, 2026-09-24)

## Configuration
- Input: `screen/real_manifest_v2.json` — 500 real Salt Lake County parcels
  (Utah AGRC "Utah Statewide Parcels", pulled 2026-09-23; bbox lon
  −111.95..−111.80, lat 40.72..40.80; see `screen/real_parcels/SOURCES.md`).
  Same production path as the 10k run: `screen/screener.py` →
  `prototype.pipeline.run_pipeline`, unmodified; driver only adds timing +
  RSS sampling (`stress/run_stress.py --manifest screen/real_manifest_v2.json
  --out stress/outputs/real500`).
- `max_schemes: 8`; zoning/finance configs per district from the manifest.
- Environment: this VM, single process, `PYTHONHASHSEED=0`, shared with
  other worker lanes. Single-run observation, not a tuned benchmark.

## Shape facts (the actual question)
- Real parcel vertices: min 4 / **median 7** / p95 37 / max 209.
- Synthetic 10k generator shapes: rect / L / trapezoid / skinny — all
  ≤ ~8 vertices. So the real corpus has a long complex-shape tail the
  synthetic run never exercised, but its median parcel is a simple
  rectangle in both corpora.
- The 55 real parcels that produced schemes are the complex ones:
  vertices median 20 / p95 144 / max 186 (larger industrial/airport/MU
  parcels). The simple rectangles mostly fell below the size threshold.

## Measured (2026-09-24, wall 14.4 s)
- Parcels: 500 in manifest / **500 screened / 0 errored** /
  445 no_schemes (413 below_size_threshold, 32 unexpected) / 55 with schemes
- Scheme rows: 312; top-scheme lots total: 494
- Per-parcel pipeline seconds (all 500): min 0.002 / median 0.005 /
  **p95 0.183** / p99 0.300 / max 0.878 / mean 0.028
- Peak RSS (getrusage): **74.2 MB**; max sampled 77.4 MB (2 samples — run
  lasted 14.4 s at a 5 s sample interval)
- Disk: `stress/outputs/real500` = **29 MB** (~58 KB/parcel); 3,129 files
- RuleGraph outcomes: PASS 17,004 / UNKNOWN 1,404 / FAIL 0 /
  CONDITIONAL_PASS 0 / MANUAL_REVIEW 0; vacuous-PASS schemes 58;
  use-allowance 312 UNKNOWN (no building programs — never defaulted)

## Honest comparison vs the synthetic 10k numbers
The headline delta — corpus median 0.005 s vs synthetic median 0.164 s —
is **a composition effect, not a shape effect**: 89% of the real parcels
hit the below-size-threshold fast path (median 0.005 s), while the
synthetic corpus was built at 0.5–40 acres so only 19.6% were no_schemes
(and 64% of those ran the full pipeline and failed on no-conforming-lots).

Like-for-like, parcels that ran the full pipeline and produced schemes:

| metric (s/parcel) | real shapes (n=55) | synthetic (n=8045) |
|---|---|---|
| median | **0.155** | 0.196 |
| p95 | **0.436** | 0.520 |
| mean | 0.184 | 0.236 |
| max | 0.878 | 1.865 |

Answer to the open question: **real shapes are not slower.** On
like-for-like full-pipeline parcels, real parcels (median 20 vertices,
tail to 186) run at essentially the same speed as synthetic ones —
slightly faster at every percentile. Nothing in the timing data suggests
a shape-complexity penalty at the observed vertex counts.

## Where the time goes (2 single-parcel cProfile runs — proportions only)
- Median scheme parcel (0.155 s, 9 schemes): **DXF export ~52%**
  (ezdxf document save/write), geometry plan_generation ~24%
  (shapely intersection), JSON writes ~11%. RuleGraph evaluation does not
  appear in the top 25 functions.
- Slowest parcel (0.878 s, OS district, 20 vertices, 10 schemes):
  geometry ~36% (24,258 shapely intersection calls), DXF ~30%,
  scheme validation ~28%. Rules again negligible.
- Consistent story: **ezdxf export + shapely geometry dominate; rule
  evaluation is not the bottleneck.** If per-parcel time ever needs
  cutting, DXF serialization is the first target — not the rules engine.
  (Two parcels only; treat as directional, not a corpus profile.)

## What this does and does not claim
- DOES: on 500 real SLC parcels the production pipeline sustains
  ~35 parcels/sec overall (14.4 s wall), 0 errors, 0 aborts; full-pipeline
  parcels run at median 0.155 s (p95 0.436 s) — no shape-complexity
  penalty vs synthetic at observed vertex counts; peak RSS 74.2 MB;
  time is dominated by DXF export + shapely geometry, not rule
  evaluation.
- DOES NOT: statewide readiness, GIS-scale ingestion throughput,
  multi-process scaling, or performance on shapes beyond the observed
  range (max 209 vertices). The kill/no-resume finding from
  STRESS_REPORT.md still stands (untested at this scale, same code).
  Single run on a shared VM — treat all figures as observed, not rated.

## Artifacts
- `stress/outputs/real500/` — per-parcel dirs, screening_results.csv,
  summary.json, timings.csv, rss_profile.csv, stress_meta.json
  (gitignored, same as the 10k outputs)
- `stress/run_stress.py` (reused unmodified)
