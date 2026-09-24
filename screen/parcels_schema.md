# Parcel Input Schema — Mass Screener Contract

Version: 1. The screener (`screen/screener.py`) reads a **manifest** and runs
each parcel through `prototype.pipeline.run_pipeline`. This document is the
contract between the screener and whoever produces parcel inputs (synthetic
generators today, the GIS loader tomorrow). A GIS loader that emits exactly
what is described here plugs in **with zero code changes**.

## 1. Manifest

A JSON object:

```json
{
  "screen_name": "synthetic-v1",
  "max_schemes": 8,
  "parcels": [
    {
      "parcel_id": "syn-m1-001",
      "parcel_geojson": "synthetic_parcels/syn-m1-001.geojson",
      "zoning_config":  "synthetic_parcels/syn-m1-001.zoning.json",
      "finance_config": "synthetic_parcels/syn-m1-001.finance.json",
      "program":        "synthetic_parcels/syn-m1-001.program.json"
    }
  ]
}
```

- `screen_name` (string, optional): label stamped into `summary.json`.
- `max_schemes` (int, optional, default 8): passed to `run_pipeline`; also
  overridable via `--max-schemes`.
- `parcels` (list, required): one entry per parcel, processed **in order**.
- Every per-parcel field except `parcel_id` may be given in either of two
  forms:
  - **Inline**: a JSON object/array embedded directly in the manifest.
  - **Path**: a string naming a JSON file. Relative paths resolve against
    **the manifest file's directory**; absolute paths are used as-is.

`program` may additionally be `null` (absent). When a program is absent,
every RuleGraph context attribute except `district` (when the zoning config
carries it) is unknown → verdicts come out UNKNOWN, never defaulted to
compliance.

## 2. Parcel GeoJSON

A GeoJSON **Feature** with a **Polygon** geometry in **planar feet**
(same convention as `inputs/demo_parcel.geojson`):

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[0,0],[420,0],[420,320],[0,320],[0,0]]]
  },
  "properties": {
    "parcel_id": "syn-mu11-001",
    "crs": "local-feet",
    "source": "SYNTHETIC fixture for screener testing — not a real parcel"
  }
}
```

Requirements:

| Field | Required | Notes |
|---|---|---|
| `type` | yes | `"Feature"` (a single-Feature `FeatureCollection` or bare `Polygon` is also accepted by the pipeline) |
| `geometry.type` | yes | `"Polygon"` |
| `geometry.coordinates` | yes | Ring(s) of `[x, y]` pairs, **feet**, planar (local frame). First and last coordinate must match (closed ring). |
| `properties.parcel_id` | **yes** | Stable unique ID. Falls back to the input filename if absent, but the screener materializes inputs as `parcel.geojson`, so **always set it**. |
| `properties.crs` | **yes** | `"local-feet"` for planar-feet inputs (any string is accepted and echoed into `report.json`; the geometry engine always treats coordinates as planar feet). |

Polygon must be simple (non-self-intersecting). Holes are not currently
handled by the geometry generator — provide the outer ring only.

### GIS-loader mapping notes

- Reproject the parcel footprint into a local planar frame in **feet**
  (e.g. translate so coordinates are small positive numbers; a state-plane
  or UTM foot-based CRS works if coordinates are in feet).
- Emit one Feature per parcel; set `properties.parcel_id` to the assessor
  parcel number and `properties.crs` to `"local-feet"`.
- Real APN metadata (owner, address, situs) may ride along in `properties`
  — the screener ignores unknown properties.

## 3. Zoning config

JSON object. Required keys (the pipeline refuses to subdivide on missing or
non-positive values — loud failure, not silent admission):

| Key | Type | Meaning |
|---|---|---|
| `min_lot_area_sqft` | number > 0 | Minimum lot area, square feet |
| `min_frontage_ft` | number > 0 | Minimum lot frontage, feet |
| `road_width_ft` | number > 0 | Internal road width, feet |

Recommended optional keys:

| Key | Type | Meaning |
|---|---|---|
| `district` | string | Jurisdiction district code, e.g. `"M-1"`, `"OS"`, `"PL"`, `"MU-11"`. **Feeds the RuleGraph context**: rules whose district differs from this are evaluated as not-applicable. Omit it and every rule evaluates against an unknown district. |
| `zone_label` | string | Human label, e.g. `"M-1 Light Manufacturing (SYNTHETIC)"`. Carried into the CSV. |
| `source` | string | Provenance of these values — **must say SYNTHETIC for fixtures**, or name the real source (jurisdiction GIS layer + code citation) for real parcels. |

Example (synthetic):

```json
{
  "min_frontage_ft": 50,
  "min_lot_area_sqft": 5000,
  "road_width_ft": 55,
  "district": "MU-11",
  "zone_label": "MU-11 Mixed Use (SYNTHETIC)",
  "source": "SYNTHETIC zoning parameters for screener testing. NOT a real jurisdiction value."
}
```

## 4. Finance config

JSON object, same shape as `inputs/finance.json`:

| Key | Type | Meaning |
|---|---|---|
| `sale_price_per_lot` | number | Assumed revenue per finished lot ($) |
| `road_cost_per_lf` | number | Road construction cost per linear foot ($) |
| `soft_costs_fixed` | number | Fixed soft costs per project ($) |
| `contingency_pct` | number | Contingency as a fraction, e.g. `0.1` = 10% |
| `source` | string | Provenance — **SYNTHETIC for fixtures** |

## 5. Building program (optional)

JSON object mapping RuleGraph context attributes to project facts
(full attribute list: `rulegraph/adapter.py` `CONTRACT_ATTRS`). Unknown
keys raise a loud `ValueError` — a typo'd program never silently passes.

```json
{
  "_note": "SYNTHETIC program for screener testing only",
  "district": "MU-11",
  "building_form": "row_house",
  "height_ft": 38
}
```

Attributes not supplied stay `None` → the corresponding rules evaluate
UNKNOWN. A program may also carry a top-level `"schemes"` map
(scheme-id → program dict) for per-scheme overrides; see `adapter.py`.

## 6. Screener outputs

Per parcel: `<out_root>/<parcel_id>/` containing the pipeline's normal
artifacts (`report.json`, `schemes/`, `comparison.csv`) plus
`inputs/` — the exact effective inputs (parcel, zoning, finance, program)
materialized by the screener, so a screen is reproducible from its own
output directory.

Aggregate, at `<out_root>/`:

- `screening_results.csv` — one row per parcel-scheme (`row_kind=scheme`),
  one row per parcel with no schemes (`row_kind=no_schemes`), one row per
  failed parcel (`row_kind=error`). Columns:

  `parcel_id, zone_label, district, row_kind, scheme_id, lots, road_ft,
  revenue, total_cost, profit, margin, rg_verdict, rg_pass, rg_fail,
  rg_unknown, geometry_clean, unknowns_count, error`

  - `rg_verdict`: the scheme's overall RuleGraph verdict
    (`PASS`/`FAIL`/`UNKNOWN`), propagated verbatim from `report.json`.
  - `rg_pass`/`rg_fail`/`rg_unknown`: counts of per-rule outcomes for
    the scheme (out-of-district rules count as PASS/not-applicable per
    `rulegraph/engine.py`).
  - `geometry_clean`: geometric validation only (`true`/`false`); it does
    **not** imply zoning compliance — see `rg_verdict`.
  - `unknowns_count`: number of RuleGraph context attributes with no
    evidence for this parcel (length of `report.json`'s `rulegraph.gaps`).
    UNKNOWNs are propagated, never zeroed.
- `summary.json` + printed summary — parcels in manifest / screened /
  errored / with no schemes; scheme-row count; total lots of the
  top-ranked scheme per parcel; mean/median profit and margin **over scheme
  rows only**; aggregate RuleGraph outcome counts; per-parcel error list.

Determinism: parcels are processed in manifest order, float columns use
fixed-decimal formatting, and there is no randomness anywhere — rerunning
the same manifest yields a byte-identical CSV.
