"""CLI: python -m prototype / python run.py"""
from __future__ import annotations

import argparse
import json
import os

from . import compare as cmp_mod
from .pipeline import run_pipeline
from . import economics as economics_mod
from . import finance as finance_mod
from . import geometry as geometry_mod
from . import validation as validation_mod


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Land-dev prototype pipeline (deterministic)")
    ap.add_argument("--parcel", default="inputs/demo_parcel.geojson")
    ap.add_argument("--zoning", default="inputs/zoning.json")
    ap.add_argument("--finance", default="inputs/finance.json")
    ap.add_argument("--economics", default=None,
                    help="economics JSON (e.g. inputs/economics_slco_2026.json): "
                         "replaces --finance by mapping documented, per-district "
                         "market figures onto the finance config keys. "
                         "Without this flag, behavior is unchanged.")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--max-schemes", type=int, default=8)
    ap.add_argument("--program", default=None,
                    help="optional building-program JSON for RuleGraph evaluation "
                         "(heights, stories, setbacks, streets, abutments). "
                         "A top-level \"schemes\" map ({scheme_id: {...}}) "
                         "overrides base facts per scheme.")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parcel = args.parcel if os.path.isabs(args.parcel) else os.path.join(base, args.parcel)
    zoning_p = args.zoning if os.path.isabs(args.zoning) else os.path.join(base, args.zoning)
    finance_p = args.finance if os.path.isabs(args.finance) else os.path.join(base, args.finance)
    out = args.out if os.path.isabs(args.out) else os.path.join(base, args.out)
    os.makedirs(out, exist_ok=True)

    if args.economics:
        econ_p = args.economics if os.path.isabs(args.economics) else os.path.join(base, args.economics)
        econ = economics_mod.load_economics(econ_p)
        with open(zoning_p) as f:
            zone_label = json.load(f).get("zone_label", "")
        finance_cfg = economics_mod.finance_config_from_economics(
            econ, zone_label, econ_path=econ_p)
        prov = finance_cfg["economics"]
        print(f"economics: {os.path.basename(econ_p)}  zone_label={zone_label!r}  "
              f"-> district {prov['district_matched']}"
              f"{' (DEFAULT fallback)' if prov['fallback_to_default'] else ''}  "
              f"revenue_confidence={prov['revenue_confidence']}")
        for w in prov["warnings"]:
            print(f"economics WARNING: {w}")
        if args.finance != "inputs/finance.json":
            print("economics: --economics takes precedence over --finance for this run")
        # write the derived config into out/ so the run is fully auditable
        finance_p = os.path.join(out, "derived_finance.json")
        with open(finance_p, "w") as f:
            json.dump(finance_cfg, f, indent=2)

    program = None
    if args.program:
        program_p = args.program if os.path.isabs(args.program) else os.path.join(base, args.program)
        with open(program_p) as f:
            program = json.load(f)

    result = run_pipeline(parcel, zoning_p, finance_p, out, max_schemes=args.max_schemes,
                          building_program=program)
    report = result["report"]
    ranked = result["ranked"]
    proformas = result["proformas"]
    validations = result["validations"]

    print(f"parcel: {report['parcel_id']}  "
          f"{report['parcel_area_acres']} ac ({report['parcel_area_sqft']:,.0f} sqft)")
    print(f"schemes: {len(ranked)}  ->  {out}\n")
    if not ranked:
        print("WARNING: no schemes generated for this parcel — report records "
              "status='no_schemes_generated'. This is not a successful screen.\n")
    print(cmp_mod.comparison_table(ranked, proformas, validations))
    print(f"\nwrote: {out}/report.json, {out}/comparison.csv, {out}/schemes/*.dxf")


if __name__ == "__main__":
    main()
