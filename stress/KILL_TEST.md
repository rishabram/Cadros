# Kill / restart behavior test (LoadRunner, 2026-09-24)

## Method
Started the full 10k synthetic run (`stress/run_stress.py --out
stress/outputs/killtest`), sent SIGTERM after 789 parcel dirs were
complete (~2.5 min in), then inspected the output tree directly.
(All numbers below are from direct inspection, not from the watchdog
loop, whose relative-path check ran in the wrong cwd — see note.)

## Findings (measured, not assumed)
1. **SIGTERM suffices.** The screener installs no signal handlers; the
   process dies mid-parcel and in-flight parcel work is abandoned.
   No SIGKILL was needed.
2. **All aggregation is lost on kill.** `screening_results.csv` and
   `summary.json` are written only after every parcel completes — 789
   parcels of compute produced no usable aggregate.
3. **Driver-side measurements are lost too.** `timings.csv`,
   `rss_profile.csv`, `stress_meta.json` are written after
   `screen_manifest` returns; SIGTERM killed the interpreter first.
4. **Completed per-parcel dirs survive intact.** `stress-00001/`
   contained `report.json` (valid JSON, `no_schemes_generated` with a
   full scheme-generation diagnostic), `comparison.csv`, `inputs/`,
   `schemes/`. Partial parcels are never half-written into the
   aggregate because the aggregate doesn't exist yet.
5. **No checkpoint/resume in the shipped pipeline.** A restart redoes
   all parcels from scratch. Per-parcel outputs are deterministic and
   idempotent (same manifest → byte-identical), so a resume-by-skip
   wrapper (skip parcel_ids with an existing valid `report.json`) is
   feasible, but it is not part of the shipped pipeline and was not
   implemented here — out of scope for a measurement lane.

## Operational implication (honest)
At 10k scale (~30 min/run) a kill costs the full run. If NERON ever
screens at 100k+ parcels or multi-hour runs, the missing resume is the
dominant operational risk — recommend an incremental-CSV or `--resume`
flag before claiming anything at that scale. This test does not claim
the pipeline is production-ready at any scale; it documents exactly
what happens when a run dies.

## Watchdog-loop note (process lesson)
The kill watchdog's `ls stress/outputs/killtest` check ran in the
foreground shell whose cwd was never changed (the `cd` was inside the
backgrounded `&&`-chain), so it counted 0 dirs forever while the real
run passed 700+. Lesson: in backgrounded compound commands, `cd`
explicitly in every shell that uses relative paths — or use absolute
paths everywhere. The kill itself was verified by direct inspection,
so the finding stands.
