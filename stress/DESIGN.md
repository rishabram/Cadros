# 10,000-parcel stress test — design (LoadRunner, 2026-09-24)

## What this test is
A throughput / resource / robustness measurement of the production mass
screener (`screen/screener.py` → `prototype.pipeline.run_pipeline`) over
10,000 parcels. It feeds the growth-scorecard aim "10k-parcel stress test
passed (+ memory/disk profile)".

## Input set: 10,000 synthetic procedural parcels
- Deterministic generator (`generate.py`), seed **20260924**, stdlib
  `random.Random` only. Same seed → byte-identical manifest.
- District mix mirrors the real 500-parcel county screen ×20:
  M-1 1180, R-1-7000 3180, R-1-5000 260, RMF-30 20, OS 700, M-2 760,
  EI 60, MU-5 2740, FR-3 420, FR-2 400, BP 260, MU-11 20 (= 10,000).
- Zoning and finance configs are reused VERBATIM from the real county
  screen (`real_manifest_v2.json`, first entry per district) — the same
  production inputs, only the parcel polygons are synthetic.
- Shape families: rectangle 40%, L-shape 30%, trapezoid 20%,
  skinny rectangle (aspect up to 8:1) 10%. Areas log-uniform 0.5–40 acres.
  Random rotation 0–90°. All parcels labeled SYNTHETIC in properties.
- `max_schemes: 8`, same as the county screen.

## Why synthetic, not tiled real parcels
Tiling the 500 real parcels 20× would measure throughput on real shapes
but add zero geometric diversity and zero new robustness signal (the v5
screen already covers those shapes). Synthetic shapes test the engine
against geometries it has never seen, which is the honest robustness
question at 10k scale.

## What the test proves
- Wall-clock total and per-parcel timing (median/p95) of the real
  pipeline path, single-process, on this VM.
- Peak RSS and RSS-over-time profile (5 s sampling via /proc/self/statm).
- Temp disk usage of per-parcel artifacts (report.json, DXFs, inputs).
- Failure behavior: error rows vs aborts; kill-mid-run behavior.

## What the test does NOT prove
- Real-world parcel-shape distribution handling (synthetic shapes only).
- GIS-scale data loading / statewide data-pipeline readiness.
- Multi-process or distributed scaling (single process only).
- Timing under production machine load (this VM is shared with other
  worker lanes; timings are single-run observations, not benchmarks).
- Anything about commercial readiness. This is an engineering
  measurement, not a product claim.

## No-resume finding (expected)
`screen_manifest` has no checkpoint/resume: a kill loses the aggregate
CSV/summary (written only at completion); per-parcel dirs already written
are idempotent and deterministic, so a resume-by-skip wrapper is possible
but is not part of the shipped pipeline. The kill test below documents
this rather than assuming it.
