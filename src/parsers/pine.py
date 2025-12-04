#!/usr/bin/env python3
"""Lightweight Pine Script -> IR parser.

This is a pragmatic parser that extracts a subset of information from
generated Pine scripts created by the project's Pine generator. It is
not a full Pine AST parser, but it is sufficient for round-trip
equivalence tests (indicators, simple meta, sizing, and if-conditions).
"""
import re
from pathlib import Path
from typing import Dict, Any, List


def _first_group(m):
    return m.group(1) if m else None


def parse(code: str) -> dict:
    """Parse Pine code heuristically into the project's IR format.

    Args:
        code: Pine Script source

    Returns:
        IR-like dict with keys similar to Python parser output
    """
    meta = {"name": "Untitled Pine", "author": "Unknown", "timeframe": "default"}

    # strategy header: strategy("Name", author="Author" ...)
    m = re.search(r'strategy\s*\(\s*"([^"]+)"(?:\s*,\s*author\s*=\s*"([^"]+)")?', code)
    if m:
        meta["name"] = m.group(1)
        if m.lastindex and m.lastindex >= 2 and m.group(2):
            meta["author"] = m.group(2)

    # Indicators: lines like `ind_0 = ta.sma(dataframe, 15)`
    indicators: List[Dict[str, Any]] = []
    for m in re.finditer(r'(?m)^(ind_\d+)\s*=\s*ta\.(\w+)\s*\(\s*[^,\)]+\s*,\s*([0-9]+)\s*\)', code):
        ind_id = m.group(1)
        ind_type = m.group(2).upper()
        period = int(m.group(3))
        indicators.append({"id": ind_id, "type": ind_type, "params": {"period": period}, "source": "close"})

    # If indicator lines are absent, try to pick up common ta.rsi/ta.sma patterns without ind_ prefix
    if not indicators:
        for m in re.finditer(r'(?m)^\s*(?:\w+)\s*=\s*ta\.(\w+)\s*\(\s*[^,\)]+\s*,\s*([0-9]+)\s*\)', code):
            ind_type = m.group(1).upper()
            period = int(m.group(2))
            indicators.append({"id": f"ind_{len(indicators)}", "type": ind_type, "params": {"period": period}, "source": "close"})

    # Position sizing: size = 10.0  (assumed percent)
    ps = {"mode": "percent", "value": 10}
    m = re.search(r'(?m)^\s*size\s*=\s*([0-9]+(?:\.[0-9]+)?)', code)
    if m:
        try:
            val = float(m.group(1))
            ps = {"mode": "percent", "value": val}
        except Exception:
            pass

    # Conditions: find if blocks followed by strategy.entry or strategy.close
    entry_exprs: List[Dict[str, Any]] = []
    exit_exprs: List[Dict[str, Any]] = []

    # entry pattern: capture the full condition up to the end of the line
    for m in re.finditer(r'if\s*([^\n]+)\s*\n\s*strategy\.entry', code, flags=re.IGNORECASE):
        expr = m.group(1).strip()
        entry_exprs.append({"expr": expr})

    # exit pattern (strategy.close following an if)
    for m in re.finditer(r'if\s*([^\n]+)\s*\n\s*strategy\.close', code, flags=re.IGNORECASE):
        expr = m.group(1).strip()
        exit_exprs.append({"expr": expr})

    # Fallback: look for simple comparisons appearing in the code for exit/entry
    if not entry_exprs and 'enter' in code.lower():
        # capture any parenthesized condition near 'enter' word
        m = re.search(r'\(([^\)]+)\)\s*\n\s*strategy\.entry', code)
        if m:
            entry_exprs.append({"expr": m.group(1).strip()})

    conditions = {
        "entry_long": entry_exprs,
        "exit_long": exit_exprs,
        "entry_short": [],
        "exit_short": []
    }

    orders = [{"type": "market", "side": "long", "size": f"pct:{ps['value']}", "reduce_only": False}]

    return {
        "meta": meta,
        "indicators": indicators,
        "conditions": conditions,
        "orders": orders,
        "position_sizing": ps,
        "timeframes": [meta.get("timeframe", "default")],
        "metadata": {"version": "0.1", "source": "pine_parser"}
    }
