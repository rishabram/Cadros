# Evals

Deterministic replay harness: `venv/bin/python run_evals.py` (from the repo root).

## What it runs

| Section | What it checks |
|---|---|
| `golden_01`–`golden_03` | Structural replay (scheme count, top-scheme lots/profit, all-clean, ranked order), §14 metrics: geometry IoU ≥ 0.90, constraint satisfaction = 1.00, DXF validity = 1.00 |
| `golden_bad_01` | **Adversarial fixture.** Known-invalid geometry the validator MUST reject. Bad-case rows assert "`<check>` must FAIL" — a FAIL there means the validator caught it (the assertion succeeding). `good_cases` are the control: every check must PASS, pinning the harness against vacuous all-fail. |
| `synthetic` | Seeded case generation is deterministic; stored ground-truth fingerprints reproduce |
| `edit_safety` | `evals/score.py::score_edit_safety` — edit risk gates |

Model-dependent metrics (plan classification, titleblock extraction, bearing
transcription) are not wired in the scaffold: they report `n/a` and never fail.

## Exit-code policy

**Exit 0** iff the ONLY failures are the by-design `golden_bad_01` "must FAIL"
rows (see `run_evals.is_by_design_failure`). **Exit 1** iff at least one REAL
failure exists: a must-FAIL row with any other status (the validator let bad
geometry through), a `golden_bad_01` control row that FAILs, or a FAIL
anywhere else in the suite.

The one-line summary always distinguishes the two:

```
52 checks: 37 passed, 6 failed by design, 9 n/a — no real failures
```

A run with real failures ends with `— N REAL FAILURES` instead, and exits 1.

## Determinism

Same code + same fixtures must produce identical rows. Golden fixtures live
in `inputs/golden_*.json` (and `inputs/golden/`); the runner searches both
and refuses to run silently empty.

## Regression harness (`evals/regression.py`)

Automated version of the manual baseline checks from the canonical-store
integration wave. Run after every rule-store or use-pack change.

```bash
venv/bin/python -m evals.regression --mode fast   # CI: goldens + fingerprints (~10s)
venv/bin/python -m evals.regression --mode full --out evals/regression_last.json  # + demo/Jefferson (~20s)
```

Semantics:
- **Geometry + economics are byte-identity assertions** — demo (11 lots /
  $634,700 / 60.7%), Jefferson (4 lots / $602,392.32 / 81.4%). Any change is
  a FAILURE.
- **Compliance verdicts are findings, never failures** — recorded every full
  run, compared against `evals/regression_verdict_pins.json`; a change is
  reported, not failed.
- **Store fingerprints are tamper-evidence** — rule store + use packs
  (M-1/OS/PL, MU, combined 513) pinned; mismatch is a FAILURE. Pins must match
  the unit-test pins (`rulegraph/test_rulegraph.py`, `useallow/test_pack.py`);
  a legitimate store change updates all of them together.

Exit 0 iff zero real failures. Findings never affect the exit code.
