"""
Python strategy parser.

Parses Python-based trading strategies and converts them to IR.
"""

import re
from typing import Dict, Any, List
from src.parsers.base_parser import BaseParser, ParserError
from src.ir.schema import (
    StrategyIR, Indicator, Condition, IndicatorType,
    TimeFrame, PositionSizing, RiskManagement
)


class PythonParser(BaseParser):
    """Parser for Python trading strategies."""
    
    def __init__(self):
        """Initialize the Python parser."""
        super().__init__()
        self.indicator_map = {
            'sma': IndicatorType.SMA,
            'ema': IndicatorType.EMA,
            'rsi': IndicatorType.RSI,
            'macd': IndicatorType.MACD,
            'bollinger_bands': IndicatorType.BOLLINGER_BANDS,
            'atr': IndicatorType.ATR,
        }
    
    def parse(self, source_code: str) -> StrategyIR:
        """
        Parse Python strategy code and convert to IR.
        
        Args:
            source_code: Python strategy source code
            
        Returns:
            StrategyIR object
            
        Raises:
            ParserError: If parsing fails
        """
        if not self.validate_syntax(source_code):
            raise ParserError("Invalid Python syntax")
        
        self.source_code = source_code
        
        # Extract strategy metadata
        name = self._extract_strategy_name()
        description = self._extract_description()
        timeframe = self._extract_timeframe()
        
        # Extract components
        indicators = self.extract_indicators(source_code)
        conditions = self.extract_conditions(source_code)
        position_sizing = self._extract_position_sizing()
        risk_management = self._extract_risk_management()
        
        # Create IR
        strategy = StrategyIR(
            name=name,
            description=description,
            timeframe=timeframe,
            indicators=indicators,
            entry_long=conditions.get('entry_long'),
            entry_short=conditions.get('entry_short'),
            exit_long=conditions.get('exit_long'),
            exit_short=conditions.get('exit_short'),
            position_sizing=position_sizing,
            risk_management=risk_management
        )
        
        return strategy
    
    def extract_indicators(self, source_code: str) -> List[Indicator]:
        """
        Extract indicators from Python code.
        
        Args:
            source_code: Python source code
            
        Returns:
            List of Indicator objects
        """
        indicators = []
        
        # Simple pattern matching for common indicators
        # Example: sma_20 = ta.SMA(close, 20)
        sma_pattern = r'(\w+)\s*=\s*(?:ta\.)?[Ss][Mm][Aa]\s*\([^,]+,\s*(\d+)\)'
        for match in re.finditer(sma_pattern, source_code):
            name = match.group(1)
            period = int(match.group(2))
            indicators.append(Indicator(
                type=IndicatorType.SMA,
                name=name,
                parameters={'period': period}
            ))
        
        # EMA pattern
        ema_pattern = r'(\w+)\s*=\s*(?:ta\.)?[Ee][Mm][Aa]\s*\([^,]+,\s*(\d+)\)'
        for match in re.finditer(ema_pattern, source_code):
            name = match.group(1)
            period = int(match.group(2))
            indicators.append(Indicator(
                type=IndicatorType.EMA,
                name=name,
                parameters={'period': period}
            ))
        
        # RSI pattern
        rsi_pattern = r'(\w+)\s*=\s*(?:ta\.)?[Rr][Ss][Ii]\s*\([^,]+,\s*(\d+)\)'
        for match in re.finditer(rsi_pattern, source_code):
            name = match.group(1)
            period = int(match.group(2))
            indicators.append(Indicator(
                type=IndicatorType.RSI,
                name=name,
                parameters={'period': period}
            ))
        
        return indicators
    
    def extract_conditions(self, source_code: str) -> Dict[str, Any]:
        """
        Extract trading conditions from Python code.
        
        Args:
            source_code: Python source code
            
        Returns:
            Dictionary with entry/exit conditions
        """
        conditions = {}
        
        # Look for common condition patterns
        # Example: if sma_20 > sma_50:  # Entry long
        long_entry_pattern = r'#\s*[Ee]ntry\s*[Ll]ong[^\n]*\n\s*if\s+([^\n:]+):'
        match = re.search(long_entry_pattern, source_code)
        if match:
            conditions['entry_long'] = Condition(
                expression=match.group(1).strip(),
                description="Long entry condition"
            )
        
        # Short entry
        short_entry_pattern = r'#\s*[Ee]ntry\s*[Ss]hort[^\n]*\n\s*if\s+([^\n:]+):'
        match = re.search(short_entry_pattern, source_code)
        if match:
            conditions['entry_short'] = Condition(
                expression=match.group(1).strip(),
                description="Short entry condition"
            )
        
        # Exit conditions
        exit_pattern = r'#\s*[Ee]xit[^\n]*\n\s*if\s+([^\n:]+):'
        match = re.search(exit_pattern, source_code)
        if match:
            conditions['exit_long'] = Condition(
                expression=match.group(1).strip(),
                description="Exit condition"
            )
        
        return conditions
    
    def _extract_strategy_name(self) -> str:
        """Extract strategy name from code."""
        # Look for class name or NAME variable
        class_pattern = r'class\s+(\w+)Strategy'
        match = re.search(class_pattern, self.source_code)
        if match:
            return match.group(1)
        
        name_pattern = r'STRATEGY_NAME\s*=\s*["\']([^"\']+)["\']'
        match = re.search(name_pattern, self.source_code)
        if match:
            return match.group(1)
        
        return "UnnamedStrategy"
    
    def _extract_description(self) -> str:
        """Extract strategy description from docstring."""
        docstring_pattern = r'"""([^"]+)"""'
        match = re.search(docstring_pattern, self.source_code)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_timeframe(self) -> TimeFrame:
        """Extract timeframe from code."""
        timeframe_pattern = r'TIMEFRAME\s*=\s*["\']([^"\']+)["\']'
        match = re.search(timeframe_pattern, self.source_code)
        if match:
            tf_str = match.group(1)
            try:
                return TimeFrame(tf_str)
            except ValueError:
                pass
        return TimeFrame.H1
    
    def _extract_position_sizing(self) -> PositionSizing:
        """Extract position sizing configuration."""
        # Look for position size configuration
        size_pattern = r'POSITION_SIZE\s*=\s*(\d+\.?\d*)'
        match = re.search(size_pattern, self.source_code)
        if match:
            return PositionSizing(method="fixed", value=float(match.group(1)))
        return PositionSizing()
    
    def _extract_risk_management(self) -> RiskManagement:
        """Extract risk management parameters."""
        risk = RiskManagement()
        
        # Stop loss
        sl_pattern = r'STOP_LOSS\s*=\s*(\d+\.?\d*)'
        match = re.search(sl_pattern, self.source_code)
        if match:
            risk.stop_loss = float(match.group(1))
        
        # Take profit
        tp_pattern = r'TAKE_PROFIT\s*=\s*(\d+\.?\d*)'
        match = re.search(tp_pattern, self.source_code)
        if match:
            risk.take_profit = float(match.group(1))
        
        return risk
