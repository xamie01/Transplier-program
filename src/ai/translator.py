"""AI Translator scaffold for translating conditions between languages.

This module provides a pluggable `Translator` interface used by the
CLI when the `--with-ai` flag is enabled. The default implementation
is a lightweight heuristic that replaces DataFrame column references
with indicator identifiers using the IR `mappings` emitted by the
Python parser. Replace or extend `Translator` to call an LLM or other
service to handle complex expression translation.
"""
from typing import Dict, Any
import re
import copy


class Translator:
    """Simple translator scaffold.

    Methods:
        translate_condition(expr, ir, target_lang): translate a single condition expression.
        translate_ir_conditions(ir, target_lang): translate all conditions in an IR and return a new IR.
    """

    def __init__(self, backend: str = "stub"):
        self.backend = backend

    def translate_condition(self, expr: str, ir: Dict[str, Any], target_lang: str) -> str:
        """Translate one condition expression.

        Default behavior: replace occurrences of `dataframe['col']` (and similar)
        with indicator placeholder tokens `ind:<id>` using `ir['mappings']['column_to_indicator']`.
        """
        if not expr or not isinstance(expr, str):
            return expr

        # If mappings exist, replace dataframe['col'] with the mapped ind id
        mappings = ir.get("mappings", {}).get("column_to_indicator", {})

        def repl(m):
            col = m.group(1) or m.group(2)
            if not col:
                return m.group(0)
            mapped = mappings.get(col)
            if mapped:
                return f"ind:{mapped}"
            # If no mapping, fall back to the column name
            return col

        # Match dataframe['col'] or dataframe["col"] or simple col references
        pattern = re.compile(r"dataframe\[['\"]([^'\"]+)['\"]\]|dataframe\[([^\]]+)\]")
        expr2 = pattern.sub(repl, expr)

        # Further heuristics: convert `.shift(1)` to `.shift(1)` token or remove if target language doesn't support it.
        # For now we keep it verbatim; an advanced translator would convert semantics using an LLM.
        return expr2

    def translate_ir_conditions(self, ir: Dict[str, Any], target_lang: str) -> Dict[str, Any]:
        """Return a copy of `ir` with conditions translated for `target_lang`.

        The returned IR is a shallow copy with translated expressions placed
        in the `conditions` blocks. This function does not modify the original IR.
        """
        out = copy.deepcopy(ir)
        conds = out.get("conditions", {})
        for block_name, items in conds.items():
            for item in items:
                if "expr" in item:
                    item["expr_translated"] = self.translate_condition(item["expr"], out, target_lang)
        return out


def get_default_translator():
    """Return a default Translator instance (can be replaced with an LLM-backed one)."""
    return Translator()
