"""Round-trip and generator tests."""
import pytest
import json
from pathlib import Path
from src.parsers.python import parse as parse_python
from src.generators.python import generate as generate_python
from src.generators.pine import generate as generate_pine
from src.ir.normalize import normalize_ir, ir_equivalent


SIMPLE_STRATEGY = """
\"\"\"SMA Crossover Example
Name: Simple SMA Crossover
Author: Test
Timeframe: 1h
\"\"\"

def strategy():
    # Fast and slow moving averages
    fast_sma = sma(close, 20)
    slow_sma = sma(close, 50)
    
    # Entry on crossover
    if crossover(fast_sma, slow_sma):
        buy(size=10)
    
    # Exit on crossunder
    if crossunder(fast_sma, slow_sma):
        sell()
"""


def test_python_to_python_roundtrip():
    """Test Python -> IR -> Python code generation."""
    # Parse Python
    ir1 = parse_python(SIMPLE_STRATEGY)
    ir1_norm = normalize_ir(ir1)
    
    # Generate Python
    python_code = generate_python(ir1_norm)
    
    # Should produce valid Python
    assert "def run" in python_code or "import" in python_code
    assert "sma" in python_code.lower()


def test_python_to_pine_generation():
    """Test Python -> IR -> Pine conversion."""
    ir = parse_python(SIMPLE_STRATEGY)
    ir_norm = normalize_ir(ir)
    
    # Generate Pine
    pine_code = generate_pine(ir_norm)
    
    # Should produce Pine syntax
    assert "//@version" in pine_code
    assert "strategy(" in pine_code
    assert "ta." in pine_code or "sma" in pine_code.lower()


def test_ir_equivalence_same_ir():
    """Test that identical IRs are recognized as equivalent."""
    ir = {
        "meta": {"name": "test"},
        "indicators": [
            {"id": "s1", "type": "SMA", "params": {"period": 20}, "source": "close"}
        ],
        "conditions": {"entry_long": [{"expr": "crossover(s1, s2)"}]},
        "orders": [{"type": "market", "side": "long", "size": 10}],
        "position_sizing": {"mode": "percent", "value": 10}
    }
    
    ir_copy = json.loads(json.dumps(ir))  # Deep copy
    
    assert ir_equivalent(ir, ir_copy)


def test_ir_equivalence_different_indicators():
    """Test that different indicators are detected as non-equivalent."""
    ir1 = {
        "meta": {"name": "test"},
        "indicators": [
            {"id": "s1", "type": "SMA", "params": {"period": 20}, "source": "close"}
        ],
        "conditions": {},
        "orders": [],
        "position_sizing": {}
    }
    
    ir2 = {
        "meta": {"name": "test"},
        "indicators": [
            {"id": "s1", "type": "EMA", "params": {"period": 20}, "source": "close"}
        ],
        "conditions": {},
        "orders": [],
        "position_sizing": {}
    }
    
    assert not ir_equivalent(ir1, ir2)


def test_normalization_adds_defaults():
    """Test that normalization fills in missing fields."""
    sparse_ir = {
        "meta": {"name": "test"},
        "indicators": [{"type": "SMA", "params": {"period": 20}}]
    }
    
    normalized = normalize_ir(sparse_ir)
    
    # Check defaults added
    assert "id" in normalized["indicators"][0]
    assert "source" in normalized["indicators"][0]
    assert "conditions" in normalized
    assert "orders" in normalized
    assert "position_sizing" in normalized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
