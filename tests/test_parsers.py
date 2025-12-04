"""
Tests for parsers.
"""

import pytest
from src.parsers.python_parser import PythonParser
from src.parsers.pinescript_parser import PineScriptParser
from src.ir.schema import IndicatorType


class TestPythonParser:
    """Test Python parser."""
    
    def test_parse_simple_strategy(self):
        """Test parsing a simple Python strategy."""
        code = '''
STRATEGY_NAME = "SMA Crossover"
TIMEFRAME = "1h"

# Calculate indicators
sma_20 = ta.SMA(close, 20)
sma_50 = ta.SMA(close, 50)

# Entry long
if sma_20 > sma_50:
    enter_long()
'''
        
        parser = PythonParser()
        strategy = parser.parse(code)
        
        assert strategy.name == "SMA Crossover"
        assert len(strategy.indicators) == 2
    
    def test_extract_sma_indicators(self):
        """Test extracting SMA indicators."""
        code = '''
sma_20 = ta.SMA(close, 20)
sma_50 = ta.SMA(close, 50)
'''
        
        parser = PythonParser()
        indicators = parser.extract_indicators(code)
        
        assert len(indicators) == 2
        assert indicators[0].type == IndicatorType.SMA
        assert indicators[0].parameters['period'] == 20
    
    def test_extract_ema_indicators(self):
        """Test extracting EMA indicators."""
        code = 'ema_12 = ta.EMA(close, 12)'
        
        parser = PythonParser()
        indicators = parser.extract_indicators(code)
        
        assert len(indicators) == 1
        assert indicators[0].type == IndicatorType.EMA
    
    def test_extract_conditions(self):
        """Test extracting conditions."""
        code = '''
# Entry long
if sma_20 > sma_50:
    enter_long()
'''
        
        parser = PythonParser()
        conditions = parser.extract_conditions(code)
        
        assert 'entry_long' in conditions
        assert 'sma_20 > sma_50' in conditions['entry_long'].expression


class TestPineScriptParser:
    """Test Pine Script parser."""
    
    def test_parse_simple_strategy(self):
        """Test parsing a simple Pine Script strategy."""
        code = '''
//@version=5
strategy("SMA Crossover", overlay=true)

// Indicators
sma20 = ta.sma(close, 20)
sma50 = ta.sma(close, 50)

// Entry
longCondition = ta.crossover(sma20, sma50)
if longCondition
    strategy.entry("Long", strategy.long)
'''
        
        parser = PineScriptParser()
        strategy = parser.parse(code)
        
        assert strategy.name == "SMA Crossover"
        assert len(strategy.indicators) == 2
    
    def test_extract_indicators(self):
        """Test extracting indicators from Pine Script."""
        code = '''
sma20 = ta.sma(close, 20)
ema50 = ta.ema(close, 50)
rsi14 = ta.rsi(close, 14)
'''
        
        parser = PineScriptParser()
        indicators = parser.extract_indicators(code)
        
        assert len(indicators) == 3
        assert indicators[0].type == IndicatorType.SMA
        assert indicators[1].type == IndicatorType.EMA
        assert indicators[2].type == IndicatorType.RSI
    
    def test_validate_syntax(self):
        """Test Pine Script syntax validation."""
        valid_code = '//@version=5\nstrategy("Test", overlay=true)'
        invalid_code = 'some random text'
        
        parser = PineScriptParser()
        
        assert parser.validate_syntax(valid_code) is True
        assert parser.validate_syntax(invalid_code) is False
