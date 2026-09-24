"""Pipeline orchestration: parcel -> schemes -> validation -> pro forma -> DXF."""
from __future__ import annotations

import json
import os
from typing import Dict, List

from shapely.geometry import Polygon

from . import compare as cmp_mod
from . import dxf_export, finance, geometry, validation
from .schema import CheckResult, ProForma, Scheme

_RG_STORE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "rulegraph",
    "verified_rules.json",
)
# Caddy extraction v1+v2: machine-extracted executable params for
# stored-but-not-executable rules (v1: M-1/OS/PL; v2: MU). Applied in-memory
# only, in list order; the canonical store file and its fingerprint are never
# modified.
_RG_OVERLAYS = [
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "rulegraph",
        name,
    )
    for name in ("caddy_params_v1.json", "caddy_params_v2.json")
]
_RG_LOADED = None

# Human-verified §21A.33 use-table pack (M-1/OS/PL rows). Lives outside the
# scratch tree, next to the other zoning evidence.
_USE_PACK = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..",
        "neron-zoning",
        "21A33_candidates_M1_OS_PL.md",
    )
)
# Caddy's human-verified MU use table (322 rows: MU-5/MU-6/MU-11).
_MU_PACK = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "caddy_drop",
    "verified_uses_mu.json",
)
_USE_LOADED = None


def _rulegraph():
    """Lazy-load the verified RuleGraph (keeps prototype importable standalone).

    Fails loudly if the rule store is missing — running zoning evaluation
    without the verified rule set must never silently degrade.
    """
    global _RG_LOADED
    if _RG_LOADED is None:
        if not os.path.exists(_RG_STORE):
            raise FileNotFoundError(
                f"RuleGraph store not found at {_RG_STORE} — "
                "refusing to evaluate without the verified rule set"
            )
        for opath in _RG_OVERLAYS:
            if not os.path.exists(opath):
                raise FileNotFoundError(
                    f"RuleGraph param overlay not found at {opath} — "
                    "refusing to evaluate without the extraction params; a "
                    "missing overlay would silently under-evaluate"
                )
        from rulegraph import RuleGraph
        from rulegraph import adapter as rg_adapter

        _RG_LOADED = (RuleGraph.load(_RG_STORE, overlay_path=_RG_OVERLAYS),
                      rg_adapter)
    return _RG_LOADED


def _usepack():
    """Lazy-load the verified use-allowance packs (keeps prototype importable
    standalone).

    Loads the M-1/OS/PL pack (191 rows) and Caddy's MU pack (322 rows) and
    combines them into one pack (513 rows, fresh fingerprint). Fails loudly
    if either source is missing — evaluating use allowance without the
    human-verified use tables must never silently degrade.
    """
    global _USE_LOADED
    if _USE_LOADED is None:
        if not os.path.exists(_USE_PACK):
            raise FileNotFoundError(
                f"use-allowance pack not found at {_USE_PACK} — "
                "refusing to evaluate without the human-verified use table"
            )
        if not os.path.exists(_MU_PACK):
            raise FileNotFoundError(
                f"MU use-allowance pack not found at {_MU_PACK} — "
                "refusing to evaluate without the human-verified MU use table"
            )
        from useallow import adapter as use_adapter
        from useallow import engine as use_engine
        from useallow import mu_pack
        from useallow import pack as use_pack

        pack_191 = use_pack.load_pack(_USE_PACK)
        pack_322 = mu_pack.load_mu_pack(_MU_PACK)
        combined = use_pack.combine_packs(pack_191, pack_322)
        _USE_LOADED = (
            combined,
            use_adapter,
            use_engine,
            {
                "m1_os_pl": pack_191.fingerprint,
                "mu": pack_322.fingerprint,
            },
        )
    return _USE_LOADED


def _validate_zoning(zoning: Dict) -> None:
    """Fail loudly on missing/non-positive dimensional zoning inputs.

    A missing or negative min_lot_area_sqft would otherwise surface as a raw
    KeyError — or worse, silently admit every lot (negative threshold).
    """
    required = ("min_lot_area_sqft", "min_frontage_ft", "road_width_ft")
    missing = [k for k in required if k not in zoning]
    if missing:
        raise ValueError(
            f"zoning config missing required keys: {', '.join(missing)}"
        )
    for k in required:
        v = float(zoning[k])
        if v <= 0:
            raise ValueError(
                f"zoning config has non-positive {k}: {v} — refusing to subdivide"
            )


def load_inputs(parcel_path: str, zoning_path: str, finance_path: str):
    with open(parcel_path) as f:
        gj = json.load(f)
    if gj.get("type") == "Feature":
        geom = gj["geometry"]
        props = gj.get("properties", {})
    elif gj.get("type") == "FeatureCollection":
        feats = gj["features"]
        if len(feats) != 1:
            raise ValueError(
                f"parcel input is a FeatureCollection with {len(feats)} features; "
                "single-parcel scaffold expects exactly one — refusing to "
                "silently analyze only the first"
            )
        feat = feats[0]
        geom = feat["geometry"]
        props = feat.get("properties", {})
    elif gj.get("type") == "Polygon":
        geom = gj
        props = gj.get("properties", {})
    else:  # raw {"boundary": [...]}
        geom = {"type": "Polygon", "coordinates": [gj["boundary"]]}
        props = gj.get("properties", {})
    boundary = [list(map(float, pt)) for pt in geom["coordinates"][0]]
    parcel_id = props.get("parcel_id", os.path.splitext(os.path.basename(parcel_path))[0])
    with open(zoning_path) as f:
        zoning = json.load(f)
    with open(finance_path) as f:
        finance_cfg = json.load(f)
    return parcel_id, boundary, props, zoning, finance_cfg


def run_pipeline_objects(
    parcel_id: str,
    boundary: List[List[float]],
    props: Dict,
    zoning: Dict,
    finance_cfg: Dict,
    out_dir: str,
    max_schemes: int = 10,
    building_program: Dict | None = None,
) -> Dict:
    _validate_zoning(zoning)
    parcel_poly = geometry.to_polygon(boundary)
    parcel_area = float(parcel_poly.area)

    schemes, gen_diagnostic = geometry.plan_generation(
        boundary, zoning, parcel_id, max_schemes=max_schemes
    )
    rules = validation.default_rules(zoning, parcel_area)

    proformas: Dict[str, ProForma] = {}
    validations: Dict[str, List[CheckResult]] = {}
    for s in schemes:
        validations[s.scheme_id] = validation.validate_scheme(s, boundary, zoning)
        proformas[s.scheme_id] = finance.run_proforma(s, finance_cfg)

    ranked = cmp_mod.rank(schemes, proformas)

    # RuleGraph: verified-rule evaluation over the adapter context. The
    # pipeline supplies geometry; building-program facts come from the
    # optional program (absent -> None -> UNKNOWN, never silent PASS).
    # A program may carry a top-level "schemes" map (scheme id -> program
    # dict); each scheme's override merges over the base program. Without it,
    # one shared context is built and reused for every scheme, exactly as
    # before (byte-identical report output).
    graph, rg_adapter = _rulegraph()
    base_program, scheme_overrides = rg_adapter.split_program(building_program)
    rg_verdicts: Dict[str, Dict] = {}
    rg_provenances: Dict[str, Dict] = {}
    shared_provenance = None

    def _lot_facts(s) -> Dict:
        # Per-scheme lot facts for lot-dimension rules (M-1-01, PL-01) and
        # lot-size-tiered rules (OS-02/OS-04). Geometry-owned facts: always
        # present, never guessed. Added per scheme because lot areas/widths
        # differ across schemes by construction.
        return {
            "scheme_lots": [
                {"lot_id": l.lot_id, "area_sqft": l.area_sqft,
                 "frontage_ft": l.frontage_ft}
                for l in s.lots
            ],
        }

    def _with_lots(s, ctx: Dict) -> Dict:
        merged = dict(ctx)
        merged.update(_lot_facts(s))
        return merged

    if scheme_overrides:
        for s in schemes:
            program = rg_adapter.program_for_scheme(
                base_program, scheme_overrides, s.scheme_id
            )
            rg_context, rg_provenance = rg_adapter.build_context(
                zoning_cfg=zoning, program=program
            )
            rg_provenance = dict(rg_provenance)
            rg_provenance["scheme_lots"] = (
                "known", "subdivision geometry: per-scheme lot polygons")
            rg_verdicts[s.scheme_id] = graph.scheme_verdict(
                _with_lots(s, rg_context))
            rg_provenances[s.scheme_id] = rg_provenance
    else:
        rg_context, shared_provenance = rg_adapter.build_context(
            zoning_cfg=zoning, program=base_program
        )
        shared_provenance = dict(shared_provenance)
        shared_provenance["scheme_lots"] = (
            "known", "subdivision geometry: per-scheme lot polygons")
        for s in schemes:
            rg_verdicts[s.scheme_id] = graph.scheme_verdict(
                _with_lots(s, rg_context))
            rg_provenances[s.scheme_id] = shared_provenance

    # Use allowance: verified §21A.33 use-table rows over the program's
    # "proposed_uses". The shared building program feeds both evaluators —
    # base_program/scheme_overrides from the RuleGraph section are reused
    # verbatim, and each adapter ignores the other's foreign program keys
    # while still rejecting truly unknown ones loudly. Without proposed uses
    # every scheme is UNKNOWN (never silently allowed).
    pack, use_adapter, use_engine, pack_fps = _usepack()
    use_verdicts: Dict[str, Dict] = {}
    proposed_uses_present = False
    if scheme_overrides:
        for s in schemes:
            program = rg_adapter.program_for_scheme(
                base_program, scheme_overrides, s.scheme_id
            )
            ucontext, _uprov = use_adapter.build_use_context(
                zoning_cfg=zoning, program=program
            )
            use_verdicts[s.scheme_id] = use_engine.evaluate_uses(
                ucontext["district"], ucontext["proposed_uses"], pack
            )
            proposed_uses_present = proposed_uses_present or bool(
                ucontext["proposed_uses"]
            )
    else:
        ucontext, _uprov = use_adapter.build_use_context(
            zoning_cfg=zoning, program=base_program
        )
        use_verdict = use_engine.evaluate_uses(
            ucontext["district"], ucontext["proposed_uses"], pack
        )
        for s in schemes:
            use_verdicts[s.scheme_id] = use_verdict
        proposed_uses_present = bool(ucontext["proposed_uses"])

    # outputs
    schemes_dir = os.path.join(out_dir, "schemes")
    os.makedirs(schemes_dir, exist_ok=True)
    dxf_paths = {}
    for s in ranked:
        p = os.path.join(schemes_dir, f"{s.scheme_id}.dxf")
        dxf_export.export_scheme_dxf(s, boundary, p)
        # report stores the path relative to out_dir: absolute machine paths
        # in artifacts break portability and cross-run comparability.
        dxf_paths[s.scheme_id] = os.path.relpath(p, out_dir)
        with open(os.path.join(schemes_dir, f"{s.scheme_id}.proforma.json"), "w") as f:
            json.dump(proformas[s.scheme_id].model_dump(), f, indent=2)

    cmp_mod.write_comparison_csv(
        os.path.join(out_dir, "comparison.csv"), ranked, proformas, validations
    )

    report = {
        "parcel_id": parcel_id,
        "status": "ok" if ranked else "no_schemes_generated",
        # Scheme-generation diagnostic: how the (possibly empty) scheme set
        # was produced and, when empty, why. A no-schemes result is never
        # silent — see geometry.plan_generation().
        "scheme_generation": gen_diagnostic,
        "parcel_area_sqft": round(parcel_area, 1),
        "parcel_area_acres": round(parcel_area / 43560, 2),
        "crs": props.get("crs", "local-feet"),
        "zoning": zoning,
        "finance_assumptions": finance_cfg,
        "rules": [r.model_dump() for r in rules],
        "schemes": [
            {
                "scheme_id": s.scheme_id,
                "lots": len(s.lots),
                "road_ft": round(sum(r.length_ft for r in s.roads), 1),
                "params": s.params,
                "fingerprint": s.fingerprint,
                "proforma": proformas[s.scheme_id].model_dump(),
                "validation": [c.model_dump() for c in validations[s.scheme_id]],
                "clean": validation.scheme_is_clean(validations[s.scheme_id]),
                "rulegraph_verdict": rg_verdicts[s.scheme_id]["verdict"],
                "rulegraph_applicable_rules": rg_verdicts[s.scheme_id][
                    "applicable_count"
                ],
                "rulegraph": rg_verdicts[s.scheme_id]["results"],
                "use_verdict": use_verdicts[s.scheme_id]["verdict"],
                "use_applicable_rows": use_verdicts[s.scheme_id][
                    "applicable_rows"
                ],
                "use_allowance": use_verdicts[s.scheme_id]["per_use"],
                "dxf": dxf_paths[s.scheme_id],
            }
            for s in ranked
        ],
        "ranked_order": [s.scheme_id for s in ranked],
    }
    rg_counts = {"PASS": 0, "FAIL": 0, "UNKNOWN": 0}
    for v in rg_verdicts.values():
        rg_counts[v["verdict"]] += 1
    if scheme_overrides:
        # Per-scheme programs: provenance differs per scheme, so the report
        # carries one provenance map per scheme and gaps span all of them.
        provenance_block = {
            sid: {
                attr: {"state": state, "detail": detail}
                for attr, (state, detail) in prov.items()
            }
            for sid, prov in rg_provenances.items()
        }
        gaps = rg_adapter.summarize_gaps(list(rg_provenances.values()))
    else:
        provenance_block = {
            attr: {"state": state, "detail": detail}
            for attr, (state, detail) in shared_provenance.items()
        }
        gaps = rg_adapter.summarize_gaps([shared_provenance])
    report["rulegraph"] = {
        "store": "rulegraph/verified_rules.json",
        "store_fingerprint": graph.fingerprint,
        "rules_evaluated": len(graph.rules),
        "program_supplied": building_program is not None,
        "scheme_verdicts": rg_counts,
        "gaps": gaps,
        "context_provenance": provenance_block,
        "note": (
            "'clean' reflects geometric validation only. RuleGraph verdicts are "
            "reported separately with a per-scheme applicable-rule count "
            "('rulegraph_applicable_rules'). A scheme is compliance-confirmed "
            "only when its rulegraph verdict is PASS with at least one "
            "applicable verified rule. A PASS with zero applicable rules means "
            "no verified rule in the store covered the parcel's district — "
            "that is 'no applicable verified rules', not a compliance finding."
        ),
    }
    # Key present only when the feature is used, so runs without a per-scheme
    # program stay byte-identical to pre-feature report.json artifacts.
    if scheme_overrides:
        report["rulegraph"]["per_scheme_program"] = True
    use_counts = {"PASS": 0, "CONDITIONAL_PASS": 0, "FAIL": 0,
                  "UNKNOWN": 0, "MANUAL_REVIEW": 0}
    for v in use_verdicts.values():
        use_counts[v["verdict"]] += 1
    report["use_allowance"] = {
        "pack": "neron-zoning/21A33_candidates_M1_OS_PL.md + caddy_drop/verified_uses_mu.json",
        "pack_fingerprint": pack.fingerprint,
        "pack_fingerprints": pack_fps,
        "rows_parsed": len(pack.rows),
        "program_supplied": building_program is not None,
        "proposed_uses_present": proposed_uses_present,
        "scheme_verdicts": use_counts,
        "note": (
            "Use-allowance verdicts are machine-evaluated against the "
            "human-verified §21A.33 use-table packs: 191 M-1/OS/PL rows "
            "(human verdicts by Rohan, 2026-09-23) + 322 MU-5/MU-6/MU-11 rows "
            "(batch-verified by Rohan, 2026-09-23; the machine evaluates, "
            "never verifies). UNKNOWN never means allowed — it means the use "
            "could not be confirmed (no proposed uses supplied, no use rows "
            "for the district, no matching verified row, or an ambiguous row "
            "such as M1-U-28). "
            "MANUAL_REVIEW means a qualifying-provision footnote whose text "
            "was not retrieved needs a human read. FAIL rows are blank-cell "
            "code facts (the §21A.33 legend: blank = not permitted)."
        ),
    }
    # Same conditional-key convention as the rulegraph block above.
    if scheme_overrides:
        report["use_allowance"]["per_scheme_program"] = True
    with open(os.path.join(out_dir, "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    return {
        "report": report,
        "ranked": ranked,
        "proformas": proformas,
        "validations": validations,
    }


def run_pipeline(
    parcel_path: str,
    zoning_path: str,
    finance_path: str,
    out_dir: str,
    max_schemes: int = 10,
    building_program: Dict | str | None = None,
) -> Dict:
    parcel_id, boundary, props, zoning, finance_cfg = load_inputs(
        parcel_path, zoning_path, finance_path
    )
    if isinstance(building_program, str):
        with open(building_program) as f:
            building_program = json.load(f)
    return run_pipeline_objects(
        parcel_id, boundary, props, zoning, finance_cfg, out_dir, max_schemes,
        building_program=building_program,
    )
