# NERON v0.1 Scaffold — Adversarial Audit
**Date:** 2026-09-23 · **Scope:** `~/workspace/neron-scratch` (prototype/, evals/, run.py, run_evals.py)
**Baseline:** demo 8 schemes clean · golden_01/02/03 reproduce exactly · run_evals 7/7 PASS
**Post-audit:** `run.py` exit 0 · `run_evals.py` **40 checks: 31 passed, 0 failed, 9 n/a** · all golden fingerprints byte-identical to pre-audit
**Constraint honored:** `~/workspace/your_files/neron-v01-scaffold.zip` untouched; no golden fixtures modified; geometry/optimizer logic not redesigned (one input guard added, no algorithm change).

Fixes are minimal and surgical. Each issue below: severity, location, what was wrong, what changed, verification.

---

## A1 — Golden replay suite was dead: glob matched nothing (HIGH — eval integrity)
**File:** `run_evals.py:144` (was `inputs/golden/*.json`)
**What was wrong:** `make_golden.py` writes fixtures to `inputs/golden/`, but the checked-in fixtures live at `inputs/golden_01.json` (top level of `inputs/`). The eval glob `inputs/golden/*.json` matched **zero files**, so `eval_golden()` never executed. The advertised "replay all golden projects" ran 0 golden checks; "7/7 PASS" was 2 synthetic + 5 edit-safety only. A full engine regression could ship undetected behind a green suite.
**What changed:** glob both `inputs/golden/*.json` and `inputs/golden_*.json`, deduped by basename, with a comment explaining why.
**Verified:** suite now runs 40 checks (3 goldens × 11 rows + 2 synthetic + 5 edit-safety); all pass; `geometry_iou` mean = 1.0000 on all three goldens.

## A2 — `detect_tamper()` claimed "no tamper" with no baseline (HIGH — silent PASS on unknown)
**File:** `prototype/edits.py:65-80`
**What was wrong:** `Scheme.fingerprint` defaults to `""`. For a scheme that never had a fingerprint recorded, `detect_tamper()` returned `(False, "no tamper: fingerprint matches")` — asserting a clean bill of health when tamper status was unverifiable. Direct violation of the cardinal rule (unknown → PASS).
**What changed:** empty/missing fingerprint now returns `(False, "unknown: no baseline fingerprint recorded — tamper status cannot be verified")`. Signature unchanged; message and docstring are honest.
**Verified:** probe on fingerprnt-less scheme returns the unknown message; pipeline-set schemes still verify normally; `score_edit_safety` still passes.

## A3 — DXF artifacts not byte-deterministic across runs (MEDIUM — determinism)
**File:** `prototype/dxf_export.py:17`
**What was wrong:** ezdxf stamped per-run random `$FINGERPRINTGUID`/`$VERSIONGUID`, current-date `$TDCREATE`/`$TDUPDATE` (regenerated at save time), and `"1.4.4 @ <timestamp>"` dictionary variables. Two runs of identical inputs produced different DXF bytes (confirmed via sha256).
**What changed:** set ezdxf's first-class `ezdxf.options.write_fixed_meta_data_for_testing = True`, which pins all of the above (fixed 2000-01-01 date, constant GUIDs, constant marker string). No manual header surgery.
**Verified:** `scheme_00.dxf` byte-identical across two full pipeline runs; `audit_dxf()` still reports zero errors; `dxf_validity` eval still passes.

## A4 — `report.json` embedded absolute machine paths (MEDIUM — determinism/portability)
**File:** `prototype/pipeline.py:102`
**What was wrong:** `report["schemes"][i]["dxf"]` stored the absolute filesystem path (e.g. `/home/hatch/workspace/...`), leaking machine identity into artifacts and breaking cross-machine comparability.
**What changed:** store `os.path.relpath(p, out_dir)` (`schemes/scheme_00.dxf`).
**Verified:** report now shows relative paths; eval does not consume this field (builds its own tmp paths), so no eval impact.

## A5 — Negative finance inputs priced silently (MEDIUM — schema/validation gap)
**File:** `prototype/finance.py:14-32`
**What was wrong:** `run_proforma` accepted negative `sale_price_per_lot` etc. without complaint (probe: price −5000 → revenue −$55,000, profit −$465,300, no error). Missing keys raised a raw `KeyError: 'road_cost_per_lf'`.
**What changed:** upfront validation — missing required keys (`sale_price_per_lot`, `road_cost_per_lf`, `soft_costs_fixed`) and any negative value (incl. `contingency_pct`) raise `ValueError` with a clean message naming the key.
**Verified:** negative/missing inputs raise `ValueError`; demo + Jefferson + all goldens (positive values) unaffected; hand-check of finance arithmetic matches module exactly ($1,045,000 / $253,000 / $120,000 / $37,300 / $410,300 / $634,700 / 0.6074).

## A6 — Zoning config: raw KeyError or silent garbage on bad input (MEDIUM)
**File:** `prototype/pipeline.py:15-32` (new `_validate_zoning`, called in `run_pipeline_objects`)
**What was wrong:** missing `min_lot_area_sqft` → raw `KeyError` from three different modules; **negative** `min_lot_area_sqft` was worse — geometry filter `area < negative*0.98` admits everything, silently producing garbage lots.
**What changed:** single choke-point validator in `run_pipeline_objects` (covers file and direct-object call paths): required keys `min_lot_area_sqft`, `min_frontage_ft`, `road_width_ft` must be present and > 0, else clean `ValueError`.
**Verified:** missing/negative/zero zoning raises `ValueError`; all goldens, demo, Jefferson, synthetic presets pass validation.

## A7 — Zero-scheme run wrote a "successful-looking" empty report (MEDIUM — silent empty result)
**Files:** `prototype/pipeline.py:112`, `prototype/__main__.py:40`
**What was wrong:** a parcel too small to subdivide produced 0 schemes, yet the pipeline wrote a complete `report.json`/`comparison.csv` and exited 0 with no indication of failure — downstream consumers would read it as a completed screen.
**What changed:** `report["status"]` = `"ok"` | `"no_schemes_generated"`; CLI prints a loud `WARNING` when zero schemes are produced. Exit code unchanged (zero feasible schemes is a legitimate screening outcome, now labeled).
**Verified:** tiny-parcel probe → warning printed, `status: no_schemes_generated`; normal runs → `status: ok`.

## A8 — Multi-feature FeatureCollection silently analyzed only the first parcel (LOW-MEDIUM)
**File:** `prototype/pipeline.py:41-50`
**What was wrong:** `load_inputs` took `features[0]` with no check — a 2-parcel file silently screened the wrong parcel (probe confirmed: 900×900 second feature dropped, `parcel_id: FIRST` used).
**What changed:** raise clean `ValueError` unless the collection has exactly one feature (also converts the old raw `IndexError` on empty collections).
**Verified:** 2-feature input raises; single-feature and `Feature` inputs still load.

## A9 — Empty/zero-area parcel → raw GEOS traceback (LOW — robustness)
**File:** `prototype/geometry.py:32-40`
**What was wrong:** `to_polygon([])` returned an empty polygon; `generate_schemes` then died deep in shapely with `GEOSException: IllegalArgumentException: Points of LinearRing do not form a closed linestring`.
**What changed:** 2-line guard in `to_polygon` raising `ValueError("parcel boundary is empty or has zero area …")`. Guard only — no algorithm change.
**Verified:** empty boundary raises clean `ValueError`; bowtie (self-intersecting) input still repairs via `buffer(0)` as before.

## A10 — Valid raw GeoJSON Polygon file rejected with KeyError (LOW)
**File:** `prototype/pipeline.py:52-54`
**What was wrong:** a file of `{"type": "Polygon", "coordinates": [...]}` fell through to the raw-`boundary` branch → raw `KeyError: 'boundary'`.
**What changed:** handle `type == "Polygon"` explicitly.
**Verified:** raw Polygon file loads correctly.

## A11 — `set_label` logged "applied" but did nothing (LOW — false action claim)
**File:** `prototype/edits.py:54-55`
**What was wrong:** `set_label` is in `LOW_RISK` but had no handler — the call returned `(True, "applied …")` and logged `result: applied` while changing nothing.
**What changed:** implemented — stores the label in `scheme.params["label"]`.
**Verified:** `apply_edit({"type":"set_label","label":"corner lot"})` → True, `params == {"label": "corner lot"}`, provenance `applied`.

## A12 — R-6 RuleBinding disagreed with the executed check (LOW — declared vs executed rule)
**File:** `prototype/validation.py:62`
**What was wrong:** the declared binding stored `round(parcel_area/min_area, 1)` while `validate_scheme` enforced the unrounded `parcel.area / min_area` — borderline lot counts could pass the declared rule and fail the executed one (or vice versa).
**What changed:** binding now stores the unrounded value, identical to the check.
**Verified:** all goldens still validate clean; bindings are documentation-only (not in golden fixtures).

## A13 — Eval used a looser "clean" than the pipeline (LOW — latent inconsistency)
**File:** `run_evals.py:63`
**What was wrong:** three definitions of clean coexisted: `validation.scheme_is_clean` (all `pass`, strict), `compare.comparison_table` ("clean" only with 0 fail + 0 warning, strict), and the eval/`make_golden` `all_clean` (no `fail`, warnings OK, loose). A future golden with a stub-road warning would PASS the eval while `report.json` says `clean: false`.
**What changed:** eval replay now uses `pipeline.validation.scheme_is_clean` (strict), matching the pipeline's own flag. Stored golden `expected.all_clean` values untouched (all True, zero warnings in current goldens → no behavior change).
**Verified:** `all_schemes_clean` still True/True on all goldens.

---

## Deliberately NOT fixed (with reasoning)

- **N1 — `constraint_satisfaction` is tautological.** It scores the validator against itself: a validator that never fails scores 1.00 → PASS. Demonstrated empirically: monkeypatched `validate_scheme` to always return `pass`; the suite (incl. golden rows, by the same logic) still passed. Fixing requires a **known-bad fixture** (a scheme engineered to fail specific checks) — new eval design, beyond minimal-fix scope. **Recommend:** add `golden_bad_01` with a deliberately violating scheme and assert named checks FAIL.
- **N2 — `geometry_iou` on same-engine replay is a regression tripwire, not a quality metric.** It will read 1.0000 until the engine changes, by construction (docstring acknowledges this). Fine as a change detector; do not mistake it for extraction accuracy. Same known-bad-fixture recommendation applies for real validator coverage.
- **N3 — R-5 binding (`value=2.0`, operator `"touches"`) doesn't encode the warning-on-1 semantics.** Cosmetic doc-level mismatch; the executed logic (pass ≥2, warning =1, fail =0) is sound and tested. Left alone to keep the diff minimal.
- **N4 — `synthetic.py` silently skips degenerate draws** (`if not schemes: continue`). Deterministic (seeded RNG, both harness runs skip identically), and `ground_truth_reproducible` covers what is generated. Noted, not changed.
- **N5 — `edits.py` provenance timestamps** (`datetime.now(timezone.utc)`). In-memory only — `report.json`/`proforma.json` never serialize provenance (verified). No artifact contamination.
- **N6 — Geometry/optimizer internals** (per instructions): the `< 4 lots` silent drop in `generate_schemes`, `EXTEND=100.0`, the 2% tolerance shared by geometry+validation (consistent), and `_signature` diversity rule were reviewed but not altered. No unseeded randomness, no set/dict-order leakage into outputs (sorts are stable; `seen` is membership-only), no float instability beyond normal cross-platform shapely variance.
- **N7 — `margin` when revenue is 0** returns `0.0` by defined convention (`profit/revenue if revenue else 0.0`); now unreachable anyway since negative prices are rejected and lot counts are ≥ 0.

## Verification summary
| Check | Result |
|---|---|
| `run.py` demo | 8 schemes, all clean, top 11 lots / $634,700 / 60.7% — matches baseline |
| `run.py` Jefferson | 2 schemes clean — matches baseline |
| `run_evals.py` | **40 checks: 31 passed, 0 failed, 9 n/a** (was 7/7 with goldens silently skipped) |
| Golden fingerprints | byte-identical to pre-audit snapshot AND to stored fixtures (all 3) |
| DXF determinism | byte-identical across runs; `audit_dxf` zero errors |
| Finance arithmetic | hand-verified exact match |
| 9 targeted fix probes + empty-run probe | all behave as documented above |
