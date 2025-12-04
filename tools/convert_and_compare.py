#!/usr/bin/env python3
"""Utility to parse a Python strategy to IR JSON and generate Pine, then compare."""
import json
from pathlib import Path

from src.parsers.python import parse
from src.ir.normalize import normalize_ir
from src.generators.pine import generate

ROOT = Path(__file__).resolve().parents[1]
PY_FILE = ROOT / "EOVIE.py"
OUT_JSON = ROOT / "eovie_ir.json"
OUT_PINE = ROOT / "eovie_generated.pine"


def main():
    code = PY_FILE.read_text()
    ir = parse(code)
    ir_norm = normalize_ir(ir)

    OUT_JSON.write_text(json.dumps(ir_norm, indent=2))

    pine = generate(ir_norm)
    OUT_PINE.write_text(pine)

    # Basic correlation checks
    indicators = ir_norm.get("indicators", [])
    conditions = ir_norm.get("conditions", {})
    meta = ir_norm.get("meta", {})

    checks = []
    checks.append(("indicators_count", len(indicators)))
    checks.append(("has_entry_conditions", bool(conditions.get("entry_long"))))
    checks.append(("has_exit_conditions", bool(conditions.get("exit_long"))))
    checks.append(("meta_timeframe", meta.get("timeframe")))
    checks.append(("meta_name", meta.get("name")))
    checks.append(("pine_lines", len(pine.splitlines())))

    print("Wrote:")
    print(f" - {OUT_JSON}")
    print(f" - {OUT_PINE}")
    print("")
    print("Summary checks:")
    for k, v in checks:
        print(f" - {k}: {v}")

    # Quick heuristic: check that each indicator id appears in pine output
    missing = []
    pine_text = pine
    for ind in indicators:
        ind_id = ind.get("id")
        if ind_id and ind_id not in pine_text:
            missing.append(ind_id)
    print("")
    if missing:
        print("Warning: some indicator ids not found in generated Pine:", missing)
    else:
        print("All indicator ids found in generated Pine (by id search).")


if __name__ == '__main__':
    main()
