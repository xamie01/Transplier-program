import pathlib
from src.parsers import python as py_parser
from src.generators import pine as pine_generator
from src.parsers import pine as pine_parser
from src.ir import normalize as irnorm


def test_roundtrip_equivalence_eovie():
    """Parse `EOVIE.py` -> IR -> generate Pine -> parse Pine -> IR -> compare equivalence."""
    root = pathlib.Path(__file__).parents[1]
    py_path = root / 'EOVIE.py'
    assert py_path.exists(), "EOVIE.py must be present in repository root for this test"

    code = py_path.read_text()

    # Parse Python strategy into raw IR
    py_ir = py_parser.parse(code)
    py_norm = irnorm.normalize_ir(py_ir)

    # Generate Pine from normalized IR
    pine_code = pine_generator.generate(py_norm)

    # Parse generated Pine back to IR (heuristic)
    pine_ir = pine_parser.parse(pine_code)
    pine_norm = irnorm.normalize_ir(pine_ir)

    # Use the provided equivalence check
    ok = irnorm.ir_equivalent(py_norm, pine_norm)
    if not ok:
        # Dump both normalized IRs to disk for debugging/diffing
        import json
        out_dir = pathlib.Path(__file__).parents[0] / 'debug_outputs'
        out_dir.mkdir(exist_ok=True)
        (out_dir / 'py_norm.json').write_text(json.dumps(py_norm, indent=2))
        (out_dir / 'pine_norm.json').write_text(json.dumps(pine_norm, indent=2))
        # Provide a concise failure message with file locations
        raise AssertionError(
            f"IRs are not equivalent after round-trip. Dumped normalized IRs to {out_dir!s}"
        )
