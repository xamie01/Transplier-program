"""
Integration tests for the transpiler.
"""

import pytest
from src.transpiler import Transpiler, TranspilerError
from src.converter import Converter


class TestTranspiler:
    """Test Transpiler class."""
    
    def test_transpile_python_to_pinescript(self):
        """Test transpiling Python to Pine Script."""
        python_code = '''
STRATEGY_NAME = "SMA Crossover"
TIMEFRAME = "1h"

sma_20 = ta.SMA(close, 20)
sma_50 = ta.SMA(close, 50)

# Entry long
if sma_20 > sma_50:
    enter_long()
'''
        
        transpiler = Transpiler()
        pine_code = transpiler.transpile(python_code, 'python', 'pinescript')
        
        assert "//@version=5" in pine_code
        assert "strategy" in pine_code
        assert "ta.sma" in pine_code
    
    def test_transpile_pinescript_to_python(self):
        """Test transpiling Pine Script to Python."""
        pine_code = '''
//@version=5
strategy("SMA Strategy", overlay=true)

sma20 = ta.sma(close, 20)
sma50 = ta.sma(close, 50)

longCondition = ta.crossover(sma20, sma50)
if longCondition
    strategy.entry("Long", strategy.long)
'''
        
        transpiler = Transpiler()
        python_code = transpiler.transpile(pine_code, 'pinescript', 'python')
        
        assert "class" in python_code
        assert "def" in python_code
    
    def test_invalid_source_language(self):
        """Test with invalid source language."""
        transpiler = Transpiler()
        
        with pytest.raises(TranspilerError):
            transpiler.transpile("code", "invalid_lang", "python")
    
    def test_invalid_target_language(self):
        """Test with invalid target language."""
        transpiler = Transpiler()
        
        with pytest.raises(TranspilerError):
            transpiler.transpile("STRATEGY_NAME='Test'", "python", "invalid_lang")


class TestConverter:
    """Test Converter class."""
    
    def test_convert_simple_strategy(self):
        """Test converting a simple strategy."""
        code = '''
STRATEGY_NAME = "Test"
sma_20 = ta.SMA(close, 20)
'''
        
        converter = Converter()
        result = converter.convert(code, 'python', 'pinescript')
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_convert_to_ir(self):
        """Test converting to IR."""
        code = '''
STRATEGY_NAME = "Test Strategy"
sma_20 = ta.SMA(close, 20)
'''
        
        converter = Converter()
        ir = converter.convert_to_ir(code, 'python')
        
        assert isinstance(ir, dict)
        assert ir['name'] == "Test Strategy"
        assert len(ir['indicators']) == 1
    
    def test_get_supported_languages(self):
        """Test getting supported languages."""
        converter = Converter()
        languages = converter.get_supported_languages()
        
        assert isinstance(languages, list)
        assert 'python' in languages
        assert 'pinescript' in languages
