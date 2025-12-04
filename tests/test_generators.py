"""
Tests for code generators.
"""

import pytest
from src.generators.python_generator import PythonGenerator
from src.generators.pinescript_generator import PineScriptGenerator
from src.ir.schema import (
    StrategyIR, Indicator, Condition, IndicatorType,
    TimeFrame, PositionSizing, RiskManagement
)


class TestPythonGenerator:
    """Test Python code generator."""
    
    def test_generate_simple_strategy(self):
        """Test generating a simple Python strategy."""
        indicator = Indicator(
            type=IndicatorType.SMA,
            name="sma_20",
            parameters={'period': 20}
        )
        
        strategy = StrategyIR(
            name="Test Strategy",
            description="A test strategy",
            timeframe=TimeFrame.H1,
            indicators=[indicator],
            entry_long=Condition(expression="sma_20 > 100")
        )
        
        generator = PythonGenerator()
        code = generator.generate(strategy)
        
        assert "Test Strategy" in code
        assert "class" in code
        assert "sma_20" in code
    
    def test_generate_indicators(self):
        """Test generating indicator code."""
        indicators = [
            Indicator(type=IndicatorType.SMA, name="sma_20", parameters={'period': 20}),
            Indicator(type=IndicatorType.EMA, name="ema_50", parameters={'period': 50}),
        ]
        
        strategy = StrategyIR(
            name="Test",
            indicators=indicators,
            entry_long=Condition(expression="true")
        )
        
        generator = PythonGenerator()
        code = generator.generate_indicators(strategy)
        
        assert "sma_20" in code
        assert "rolling" in code
        assert "ema_50" in code
        assert "ewm" in code


class TestPineScriptGenerator:
    """Test Pine Script code generator."""
    
    def test_generate_simple_strategy(self):
        """Test generating a simple Pine Script strategy."""
        indicator = Indicator(
            type=IndicatorType.SMA,
            name="sma20",
            parameters={'period': 20}
        )
        
        strategy = StrategyIR(
            name="Test Strategy",
            indicators=[indicator],
            entry_long=Condition(expression="sma20 > close")
        )
        
        generator = PineScriptGenerator()
        code = generator.generate(strategy)
        
        assert "//@version=5" in code
        assert "strategy(" in code
        assert "sma20" in code
    
    def test_generate_indicators(self):
        """Test generating indicator code."""
        indicators = [
            Indicator(type=IndicatorType.SMA, name="sma20", parameters={'period': 20}),
            Indicator(type=IndicatorType.RSI, name="rsi14", parameters={'period': 14}),
        ]
        
        strategy = StrategyIR(
            name="Test",
            indicators=indicators,
            entry_long=Condition(expression="true")
        )
        
        generator = PineScriptGenerator()
        code = generator.generate_indicators(strategy)
        
        assert "ta.sma" in code
        assert "ta.rsi" in code
        assert "plot" in code
