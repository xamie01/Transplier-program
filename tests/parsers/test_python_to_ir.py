"""Unit tests for Python strategy parser."""
import pytest
import json
from pathlib import Path
from src.parsers.python import parse
from src.ir.normalize import normalize_ir, ir_equivalent


SIMPLE_SMA_CROSSOVER = """
\"\"\"
Name: SMA Crossover Strategy
Author: Test User
Timeframe: 1h
\"\"\"
import pandas as pd

# Simple SMA crossover strategy
def setup():
    sma_fast = sma(close, 20)
    sma_slow = sma(close, 50)
    
def signals(df):
    # Entry condition: fast SMA crosses above slow SMA
    if crossover(sma_fast, sma_slow):
        buy()
    
    # Exit condition: fast SMA crosses below slow SMA
    if crossunder(sma_fast, sma_slow):
        sell()
"""


def test_parse_sma_crossover():
    """Test parsing a simple SMA crossover strategy."""
    ir = parse(SIMPLE_SMA_CROSSOVER)
    
    # Check that IR has expected structure
    assert "meta" in ir
    assert "indicators" in ir
    assert "conditions" in ir
    
    # Check metadata
    assert ir["meta"]["name"] == "SMA Crossover Strategy"
    assert ir["meta"]["author"] == "Test User"
    
    # Check indicators extracted
    assert len(ir["indicators"]) >= 2
    assert any(ind["type"].upper() == "SMA" for ind in ir["indicators"])
    
    # Check conditions
    assert "entry_long" in ir["conditions"]
    assert "exit_long" in ir["conditions"]


def test_parse_and_normalize():
    """Test that parser output can be normalized."""
    ir = parse(SIMPLE_SMA_CROSSOVER)
    normalized = normalize_ir(ir)
    
    # Check all expected keys exist
    assert "meta" in normalized
    assert "indicators" in normalized
    assert "conditions" in normalized
    assert "orders" in normalized
    assert "position_sizing" in normalized
    
    # Check position_sizing is normalized
    ps = normalized["position_sizing"]
    assert "mode" in ps
    assert "value" in ps
    assert isinstance(ps["value"], (int, float))


def test_golden_file_match():
    """Test that parsing matches the golden reference."""
    golden_path = Path(__file__).parents[2] / "tests" / "golden" / "sma_crossover.json"
    
    if golden_path.exists():
        with open(golden_path) as f:
            expected_ir = json.load(f)
        
        ir = parse(SIMPLE_SMA_CROSSOVER)
        ir_norm = normalize_ir(ir)
        expected_norm = normalize_ir(expected_ir)
        
        # Check equivalence
        assert ir_equivalent(ir_norm, expected_norm), "Parsed IR not equivalent to golden reference"


def test_normalize_size_shorthands():
    """Test that size shorthand is parsed correctly."""
    from src.ir.normalize import normalize_ir
    
    ir = {
        "position_sizing": {"value": "pct:10"},
        "orders": [
            {"type": "market", "side": "long", "size": "pct:5"},
            {"type": "market", "side": "short", "size": 100},
        ]
    }
    
    normalized = normalize_ir(ir)
    
    # Check position sizing
    assert normalized["position_sizing"]["mode"] == "percent"
    assert normalized["position_sizing"]["value"] == 10.0
    
    # Check orders
    assert normalized["orders"][0]["size_parsed"]["mode"] == "percent"
    assert normalized["orders"][0]["size_parsed"]["value"] == 5.0
    assert normalized["orders"][1]["size_parsed"]["mode"] == "fixed"
    assert normalized["orders"][1]["size_parsed"]["value"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
