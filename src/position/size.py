"""Position sizing helper (prototype).

Contains minimal helpers to extract sizing configuration from IR.
"""


def size_from_ir(ir: dict) -> dict:
    """Return the `position_sizing` block from the IR (pass-through).

    Replace with concrete sizing rules and conversions for target platforms.
    """
    return ir.get('position_sizing', {})
