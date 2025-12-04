#!/usr/bin/env python3
"""Prototype Pine Script -> IR parser (very small heuristic)."""
import json
from pathlib import Path


def parse(code: str) -> dict:
    """Very small heuristic parser: if 'sma' present, return example IR.

    This is a prototype helper to unblock the workflow. Replace with
    a proper lexer/parser when extending.
    """
    if 'sma' in code.lower():
        schema_path = Path(__file__).parents[1] / 'ir' / 'schema.json'
        try:
            return json.load(open(schema_path, 'r'))
        except Exception:
            # Inline fallback IR
            return {
                "meta": {"name": "SMA Crossover", "author": "you", "timeframe": "1h"},
                "indicators": [
                    {"id": "s1", "type": "SMA", "params": {"period": 20}, "source": "close"},
                    {"id": "s2", "type": "SMA", "params": {"period": 50}, "source": "close"}
                ],
                "conditions": {
                    "entry_long": [{"expr": "crossover(ind:s1,ind:s2)"}],
                    "exit_long": [{"expr": "crossunder(ind:s1,ind:s2)"}]
                },
                "orders": [{"type": "market", "side": "long", "size": "pct:10", "reduce_only": False}],
                "position_sizing": {"mode": "percent", "value": 10},
                "timeframes": ["1h"],
                "metadata": {"version": "0.1", "tags": ["sma", "demo"]}
            }
    raise NotImplementedError("Pine parser prototype only handles SMA demo patterns.")
