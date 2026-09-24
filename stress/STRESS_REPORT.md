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

## Full run (10,000 parcels) — MEASURED
- Wall clock total: FILL s (FILL min)
- Parcels: 10,000 in manifest / FILL screened / FILL no_schemes / FILL errored
- Scheme rows: FILL; error rows: FILL (list any)
- Per-parcel pipeline seconds: min FILL / median FILL / p95 FILL / p99 FILL / max FILL / mean FILL
- Peak RSS (getrusage): FILL MB; max sampled RSS: FILL MB
- Disk: outputs/full = FILL (FILL per parcel); manifest 15.3 MB
- RuleGraph rule outcomes: FILL
- Vacuous-PASS schemes: FILL (not compliance findings)
- Use-allowance verdicts: FILL
- IO pattern: FILL files written (per parcel: inputs ×3–4, report.json,
  comparison.csv, schemes/*.dxf + *.proforma.json); sequential per-parcel
  writes, no random IO; aggregate CSV/summary written once at end.

## What this does and does not claim
- DOES: the single-parcel pipeline sustains FILL parcels/sec on this VM
  with peak RSS FILL MB and ~FILL disk per parcel; the screener never
  aborted and every failure was captured as a loud error row (or zero).
- DOES NOT: statewide readiness, real-shape performance, GIS ingestion
  throughput, or multi-process scaling. A kill at this scale costs the
  full run (no resume) — the dominant operational risk above 10k.

## Artifacts
- `stress/manifest_10k.json` (15.3 MB, deterministic)
- `stress/outputs/full/` — per-parcel dirs, screening_results.csv,
  summary.json, timings.csv, rss_profile.csv, stress_meta.json
- `stress/outputs/pilot/` — 200-parcel calibration run
- `stress/DESIGN.md`, `stress/KILL_TEST.md`, this report
- `stress/generate.py`, `stress/run_stress.py`
