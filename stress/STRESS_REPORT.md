# 10,000-parcel stress test — report (LoadRunner, 2026-09-24)

## Configuration
- Input: `stress/manifest_10k.json` — 10,000 synthetic procedural parcels,
  seed 20260924, sha256 `07da24788bb78b7c3fbf0096c01006ef8244b0195e6081fa08f7b4376290dbe5`
  (three independent generations byte-identical).
- District mix mirrors the real county screen ×20; zoning/finance configs
  verbatim from `screen/real_manifest_v2.json`; `max_schemes: 8`.
- Path: production `screen/screener.py` → `prototype.pipeline.run_pipeline`,
  unmodified. Driver only adds timing + RSS sampling.
- Environment: this VM, single process, `PYTHONHASHSEED=0`, shared with
  other worker lanes. Single-run observation, not a tuned benchmark.

## Design + limits
See `stress/DESIGN.md`. In short: synthetic shapes test throughput and
robustness; they do NOT prove real-world shape handling, GIS-scale
ingestion, or multi-process scaling.

## Pilot (200 parcels, same manifest, `--limit 200`)
- 200 screened, 0 errored, 42 no_schemes (20 below size threshold,
  22 legitimate no-conforming-lots diagnostics — engine working as designed).
- Wall 36.2 s; per-parcel median 0.157 s, p95 0.424 s, max 0.603 s.
- Peak RSS 123.5 MB. Disk 51 MB (~255 KB/parcel).

## Kill / restart behavior
See `stress/KILL_TEST.md`. Headline: SIGTERM kills the run; all
aggregation (CSV/summary) is lost because it is written only at
completion; completed per-parcel dirs survive intact and valid; the
shipped pipeline has no checkpoint/resume.

## Full run (10,000 parcels) — MEASURED (2026-09-24 ~16:08–16:42 UTC)
- Wall clock total: **2009.9 s (33.5 min)** → **4.97 parcels/sec**
- Parcels: 10,000 in manifest / 10,000 screened / 1,955 no_schemes / **0 errored**
- no_schemes by diagnostic: 710 below_size_threshold, 1,245 no-conforming-lots
  ("unexpected" = engine's honest diagnostic when road dedication leaves no
  conforming lots; verified legitimate on the pilot, not a generator bug)
- Scheme rows: 54,141; top-scheme lots total: 162,673
- Profit: mean $2,083,195.93, median $1,378,070.25; margin mean 0.595, median 0.7139
- Per-parcel pipeline seconds: min 0.003 / **median 0.164** / **p95 0.495** /
  p99 0.676 / max 1.865 / mean 0.199
- Peak RSS (getrusage): **196.2 MB**; max sampled RSS: 201.1 MB (401 samples)
- RSS drift: 122 MB → 201 MB over the run (mean first half 142.6 MB, second
  half 181.8 MB). Consistent with the screener's in-memory `rows` list:
  56,096 dict rows × ~1.4 KB/row ≈ 79 MB observed drift. Inference, not
  proof — but it means aggregate memory grows O(n) with parcels; at 100k
  parcels the rows list alone would approach ~1 GB. Streaming CSV writes
  would flatten this.
- Disk: outputs/full = **2.5 GB** (~250 KB/parcel); manifest 15.3 MB
- RuleGraph rule outcomes: PASS 2,866,215 / UNKNOWN 328,104 / FAIL 0 /
  CONDITIONAL_PASS 0 / MANUAL_REVIEW 0
- Vacuous-PASS schemes: 27,816 (PASS with zero applicable rules — not
  compliance findings; district not covered by the store)
- Use-allowance verdicts: 54,141 UNKNOWN (no building programs supplied —
  never defaulted to allowed)
- IO pattern: **158,287 files** written; per parcel: inputs ×3–4
  (parcel.geojson, zoning.json, finance.json), report.json,
  comparison.csv, schemes/*.dxf + *.proforma.json (up to 8 schemes).
  Sequential per-parcel writes, no random IO; screening_results.csv
  (12.3 MB) + summary.json written once at completion.
- Error rows: zero. The screener never aborted; every parcel produced
  either scheme rows, a diagnosed no_schemes row, or (none this run) an
  error row.

## What this does and does not claim
- DOES: the single-parcel pipeline sustains **~5 parcels/sec** on this VM
  (median 0.164 s/parcel, p95 0.495 s) with peak RSS **196 MB** and ~250 KB
  disk per parcel; the screener processed 10,000/10,000 parcels with zero
  errors and zero aborts, every outcome captured as a loud row.
- DOES NOT: statewide readiness, real-shape performance, GIS ingestion
  throughput, or multi-process scaling. A kill at this scale costs the
  full run (no resume — see KILL_TEST.md), and aggregate memory grows
  O(n) via the in-memory rows list: both are the dominant operational
  risks above 10k and should be addressed (incremental CSV / --resume /
  streaming writes) before any larger-scale claim.

## Artifacts
- `stress/manifest_10k.json` (15.3 MB, deterministic)
- `stress/outputs/full/` — per-parcel dirs, screening_results.csv,
  summary.json, timings.csv, rss_profile.csv, stress_meta.json
- `stress/outputs/pilot/` — 200-parcel calibration run
- `stress/DESIGN.md`, `stress/KILL_TEST.md`, this report
- `stress/generate.py`, `stress/run_stress.py`
