"""
Tests for IR schema.
"""

import pytest
from src.ir.schema import (
    StrategyIR, Indicator, Condition, IndicatorType,
    TimeFrame, PositionSizing, RiskManagement
)
from src.ir.validator import IRValidator, ValidationError


class TestIndicator:
    """Test Indicator class."""
    
    def test_indicator_creation(self):
        """Test creating an indicator."""
        indicator = Indicator(
            type=IndicatorType.SMA,
            name="sma_20",
            parameters={'period': 20}
        )
        
        assert indicator.type == IndicatorType.SMA
        assert indicator.name == "sma_20"
        assert indicator.parameters['period'] == 20
    
    def test_indicator_to_dict(self):
        """Test converting indicator to dictionary."""
        indicator = Indicator(
            type=IndicatorType.EMA,
            name="ema_50",
            parameters={'period': 50}
        )
        
        data = indicator.to_dict()
        assert data['type'] == 'ema'
        assert data['name'] == 'ema_50'
        assert data['parameters']['period'] == 50
    
    def test_indicator_from_dict(self):
        """Test creating indicator from dictionary."""
        data = {
            'type': 'rsi',
            'name': 'rsi_14',
            'parameters': {'period': 14},
            'source': 'close'
        }
        
        indicator = Indicator.from_dict(data)
        assert indicator.type == IndicatorType.RSI
        assert indicator.name == 'rsi_14'


class TestCondition:
    """Test Condition class."""
    
    def test_condition_creation(self):
        """Test creating a condition."""
        condition = Condition(
            expression="sma_20 > sma_50",
            description="SMA crossover"
        )
        
        assert condition.expression == "sma_20 > sma_50"
        assert condition.description == "SMA crossover"
    
    def test_condition_to_dict(self):
        """Test converting condition to dictionary."""
        condition = Condition(
            expression="rsi < 30",
            description="Oversold"
        )
        
        data = condition.to_dict()
        assert data['expression'] == "rsi < 30"
        assert data['description'] == "Oversold"


class TestStrategyIR:
    """Test StrategyIR class."""
    
    def test_strategy_creation(self):
        """Test creating a strategy IR."""
        strategy = StrategyIR(
            name="Test Strategy",
            description="A test strategy"
        )
        
        assert strategy.name == "Test Strategy"
        assert strategy.description == "A test strategy"
    
    def test_strategy_with_indicators(self):
        """Test strategy with indicators."""
        indicator = Indicator(
            type=IndicatorType.SMA,
            name="sma_20",
            parameters={'period': 20}
        )
        
        strategy = StrategyIR(
            name="SMA Strategy",
            indicators=[indicator]
        )
        
        assert len(strategy.indicators) == 1
        assert strategy.indicators[0].name == "sma_20"
    
    def test_strategy_to_dict(self):
        """Test converting strategy to dictionary."""
        strategy = StrategyIR(
            name="Test Strategy",
            timeframe=TimeFrame.H1
        )
        
        data = strategy.to_dict()
        assert data['name'] == "Test Strategy"
        assert data['timeframe'] == "1h"
    
    def test_strategy_from_dict(self):
        """Test creating strategy from dictionary."""
        data = {
            'name': 'Test Strategy',
            'description': 'A test',
            'version': '1.0.0',
            'timeframe': '1h',
            'indicators': [],
            'entry_long': {'expression': 'true', 'description': 'Always'},
            'position_sizing': {'method': 'fixed', 'value': 1.0},
            'risk_management': {}
        }
        
        strategy = StrategyIR.from_dict(data)
        assert strategy.name == "Test Strategy"
        assert strategy.entry_long.expression == "true"


class TestIRValidator:
    """Test IRValidator class."""
    
    def test_validate_valid_strategy(self):
        """Test validating a valid strategy."""
        strategy = StrategyIR(
            name="Valid Strategy",
            entry_long=Condition(expression="sma_20 > sma_50")
        )
        
        warnings = IRValidator.validate_strategy(strategy)
        assert isinstance(warnings, list)
    
    def test_validate_strategy_without_name(self):
        """Test validating strategy without name."""
        strategy = StrategyIR(
            name="",
            entry_long=Condition(expression="true")
        )
        
        with pytest.raises(ValidationError):
            IRValidator.validate_strategy(strategy)
    
    def test_validate_strategy_without_entry(self):
        """Test validating strategy without entry condition."""
        strategy = StrategyIR(name="Test")
        
        with pytest.raises(ValidationError):
            IRValidator.validate_strategy(strategy)
