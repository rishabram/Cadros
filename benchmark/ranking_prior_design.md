# Product-Mix Ranking Prior — Design

**Status:** DESIGN ONLY (2026-09-24). Not implemented. The current ranker
(`prototype/compare.py::rank`) sorts by `(−profit, −lot count)` — i.e., it
maximizes yield under the most permissive minimums. Daybreak V12B Plat 1 proved
this is the wrong objective for planned communities: the generator produced
59/60/62-lot schemes (all within ±15% of the approved 61), but the ranker picked
76 because it assumed every lot is the smallest legal lot, while the human
designer mixed Small / Standard / Large products.

**Honest constraint: n=2 is too thin for a fitted prior.** This document
therefore designs the *collection framework* first and the *fitted prior*
second. The framework must be in place now so that plats 3–20 contribute
structured data; the prior must not drive ranking until it has enough support
to be more than noise.

---

## 1. Data each scored plat must contribute

Recorded in a new file, `benchmark/product_mix_prior.json`, one record per
scored plat (written by the scoring lane at score time, reviewed by the parent):

```json
{
  "plat_id": "daybreak-v12b-plat1",
  "jurisdiction": "South Jordan",
  "zone": "P-C",
  "developer": "Daybreak Communities (Perigee Consulting)",
  "guideline_source": "Adopted 'Design Guidelines/Development Standards - DAYBREAK VILLAGE 12B PLAT 1' (staff-report packet PLPP202400077)",
  "products": [
    {"name": "Small Lot",    "min_frontage_ft": 30, "max_frontage_ft": 70, "min_depth_ft": 50},
    {"name": "Standard Lot", "min_frontage_ft": 50, "max_frontage_ft": 90, "min_depth_ft": 100},
    {"name": "Large Lot",    "min_frontage_ft": 70, "max_frontage_ft": null, "min_depth_ft": 110}
  ],
  "approved_product_counts": {"Small Lot": 38, "Standard Lot": 17, "Large Lot": 6},
  "approved_total_lots": 61,
  "classification_method": "plat-figure lot dimensions binned by guideline product table (lots 101-125 read 2,100-7,325 sqft; staff report range 2,671-10,867 sqft)",
  "classification_confidence": "medium"
}
```

Field rules:

- `products` come from the plat's own design guidelines or code text when they
  exist (Daybreak P-C). When no product table exists (Murray R-1-6), fall back
  to **area terciles of the approved lots** and set
  `classification_method` accordingly — never invent product names.
- `approved_product_counts` is the ground-truth distribution the prior is fit
  from. Counts, not proportions, are stored so later pooling is exact.
- `classification_confidence` is `high` (recorded plat with per-lot dimensions),
  `medium` (plat figure read + staff-report ranges), or `low` (ranges only).
  Low-confidence records contribute to collection but are down-weighted in
  fitting (weight 0.5) until corroborated.

## 2. Prior structure (hierarchical, pooled)

```
global
└── jurisdiction (e.g. "South Jordan")
    └── zone (e.g. "South Jordan / P-C")
        └── developer (e.g. "South Jordan / P-C / Daybreak Communities")
```

- Each node stores pooled product-count vectors from its scored plats.
- A scheme is scored against the **deepest node with ≥3 supporting plats**;
  shallower nodes are the fallback. With n=2 total, *every* query resolves to
  the global node — which is why the prior must not drive ranking yet (see §5).
- Node probabilities: Dirichlet-smoothed proportions
  `p_i = (c_i + α) / (Σc + kα)`, α=1 (Laplace), k = number of product classes
  in that node's pooled product table. Smoothing keeps unseen classes possible
  but unlikely — a scheme of 100% Small Lots under a mixed prior scores poorly
  but not zero.

## 3. How schemes get likelihood-scored

For a candidate scheme with lot polygons:

1. **Classify** each lot into the node's product classes using the same
   definitions stored in the prior (frontage/depth bins, or area terciles).
   Lots failing every class are counted as `unclassified` — more than 10%
   unclassified lots disqualifies the scheme from mix-ranking (falls back to
   profit ranking with a flag).
2. **Score** the scheme's count vector `c` under the node's multinomial:
   `loglik = Σ c_i · log(p_i)`.
3. **Combine** with economics. Ranking key becomes a blend, not a replacement:

   ```
   score = w_mix · z(loglik) + (1 − w_mix) · z(profit)
   ```

   where `z()` is z-normalization across the scheme set (so the two terms are
   commensurable), and `w_mix` ramps with prior support (see §5). Ties broken
   deterministically by `scheme_id`. No randomness anywhere.

## 4. Exactly which harness ranking step changes

Current chain:

```
benchmark/harness.py::run_one
  → prototype/pipeline.py::run_pipeline_objects → run_pipeline
    → prototype/compare.py::rank(schemes, proformas)   # sorts by (−profit, −lots)
    → harness takes ranked[0] as neron_top_ranked_lots
```

Changes (backwards-compatible; default behavior unchanged when no prior exists):

1. `compare.rank(schemes, proformas, mix_prior=None)` — when `mix_prior` is
   None, current sort is preserved exactly (existing tests keep passing).
2. `pipeline.run_pipeline(..., mix_prior=None)` — new optional kwarg, threaded
   through to `rank`. `run_pipeline_objects` gains the same kwarg.
3. `benchmark/harness.py::run_one` — loads `benchmark/product_mix_prior.json`
   (if present), resolves the deepest supported node for the plat's
   (jurisdiction, zone, developer), and passes it in. Records in `results.json`
   per plat: `ranking_mode` (`profit_only` | `mix_blended`) and `w_mix`.
4. New unit tests: mix classification of lots, Dirichlet smoothing, fallback
   when prior file is absent, determinism of blended ranking.

Nothing in `prototype/geometry.py` changes. This is the taxonomy rule made
concrete: a `ranking`-layer fix must not touch the generator.

## 5. Activation schedule (support-gated)

| Scored plats | `w_mix` | Behavior |
|---|---|---|
| n = 2 (now) | 0.0 | **Collect only.** Scoring lanes write `product_mix_prior.json` records; ranking unchanged. |
| n = 5 | 0.3 | Blended ranking activates; prior still global-only. Re-run all 5 plats; Daybreak-style over-yield must shrink without Tripp-Lane-style under-yield growing. |
| n = 10 | 0.5 | Jurisdiction-level nodes activate (need ≥3 plats per node). Scorecard aim (≥70% within ±15%) is evaluated against blended ranking. |
| n = 20 | 0.7 | Zone/developer nodes activate. Recalibrate smoothing α and bin definitions from residuals. |

Gate rule: `w_mix` advances only if the re-run pass rate does not regress at
the current n. If blended ranking hurts, the prior stays at collection mode and
the failure is taxonomized (usually: product classes mis-specified → `inputs`).

## 6. What success looks like

Re-run on unchanged parents + inputs: Daybreak V12B Plat 1 top-ranked scheme
lands in 55–70 lots; Tripp Lane's envelope is unchanged (its fix is geometric,
and the mix prior must not be allowed to "fix" it by accident — a ranking change
that moves a geometry-bound plat is a red flag, not a win). New scoring lanes
(P-C plats especially) contribute product records as a matter of routine.
