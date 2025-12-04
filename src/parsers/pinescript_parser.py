"""
Pine Script parser.

Parses TradingView Pine Script strategies and converts them to IR.
"""

import re
from typing import Dict, Any, List
from src.parsers.base_parser import BaseParser, ParserError
from src.ir.schema import (
    StrategyIR, Indicator, Condition, IndicatorType,
    TimeFrame, PositionSizing, RiskManagement
)


class PineScriptParser(BaseParser):
    """Parser for Pine Script trading strategies."""
    
    def __init__(self):
        """Initialize the Pine Script parser."""
        super().__init__()
        self.timeframe_map = {
            '1': TimeFrame.M1,
            '5': TimeFrame.M5,
            '15': TimeFrame.M15,
            '30': TimeFrame.M30,
            '60': TimeFrame.H1,
            '240': TimeFrame.H4,
            'D': TimeFrame.D1,
            'W': TimeFrame.W1,
            'M': TimeFrame.MN1,
        }
    
    def parse(self, source_code: str) -> StrategyIR:
        """
        Parse Pine Script strategy code and convert to IR.
        
        Args:
            source_code: Pine Script source code
            
        Returns:
            StrategyIR object
            
        Raises:
            ParserError: If parsing fails
        """
        if not self.validate_syntax(source_code):
            raise ParserError("Invalid Pine Script syntax")
        
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
        Extract indicators from Pine Script code.
        
        Args:
            source_code: Pine Script source code
            
        Returns:
            List of Indicator objects
        """
        indicators = []
        
        # SMA pattern: sma20 = ta.sma(close, 20) or sma20 = sma(close, 20)
        sma_pattern = r'(\w+)\s*=\s*(?:ta\.)?sma\s*\(\s*(\w+)\s*,\s*(\d+)\s*\)'
        for match in re.finditer(sma_pattern, source_code, re.IGNORECASE):
            name = match.group(1)
            source = match.group(2)
            period = int(match.group(3))
            indicators.append(Indicator(
                type=IndicatorType.SMA,
                name=name,
                parameters={'period': period},
                source=source
            ))
        
        # EMA pattern
        ema_pattern = r'(\w+)\s*=\s*(?:ta\.)?ema\s*\(\s*(\w+)\s*,\s*(\d+)\s*\)'
        for match in re.finditer(ema_pattern, source_code, re.IGNORECASE):
            name = match.group(1)
            source = match.group(2)
            period = int(match.group(3))
            indicators.append(Indicator(
                type=IndicatorType.EMA,
                name=name,
                parameters={'period': period},
                source=source
            ))
        
        # RSI pattern
        rsi_pattern = r'(\w+)\s*=\s*(?:ta\.)?rsi\s*\(\s*(\w+)\s*,\s*(\d+)\s*\)'
        for match in re.finditer(rsi_pattern, source_code, re.IGNORECASE):
            name = match.group(1)
            source = match.group(2)
            period = int(match.group(3))
            indicators.append(Indicator(
                type=IndicatorType.RSI,
                name=name,
                parameters={'period': period},
                source=source
            ))
        
        # MACD pattern
        macd_pattern = r'(\w+)\s*=\s*(?:ta\.)?macd\s*\(\s*(\w+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)'
        for match in re.finditer(macd_pattern, source_code, re.IGNORECASE):
            name = match.group(1)
            source = match.group(2)
            fast = int(match.group(3))
            slow = int(match.group(4))
            signal = int(match.group(5))
            indicators.append(Indicator(
                type=IndicatorType.MACD,
                name=name,
                parameters={'fast': fast, 'slow': slow, 'signal': signal},
                source=source
            ))
        
        return indicators
    
    def extract_conditions(self, source_code: str) -> Dict[str, Any]:
        """
        Extract trading conditions from Pine Script code.
        
        Args:
            source_code: Pine Script source code
            
        Returns:
            Dictionary with entry/exit conditions
        """
        conditions = {}
        
        # Long entry: strategy.entry("Long", strategy.long, when=condition)
        long_entry_pattern = r'strategy\.entry\s*\(\s*["\']Long["\'][^)]+when\s*=\s*([^)]+)\)'
        match = re.search(long_entry_pattern, source_code)
        if match:
            conditions['entry_long'] = Condition(
                expression=match.group(1).strip(),
                description="Long entry condition"
            )
        
        # Short entry
        short_entry_pattern = r'strategy\.entry\s*\(\s*["\']Short["\'][^)]+when\s*=\s*([^)]+)\)'
        match = re.search(short_entry_pattern, source_code)
        if match:
            conditions['entry_short'] = Condition(
                expression=match.group(1).strip(),
                description="Short entry condition"
            )
        
        # Exit (close)
        exit_pattern = r'strategy\.close\s*\([^)]+when\s*=\s*([^)]+)\)'
        match = re.search(exit_pattern, source_code)
        if match:
            expr = match.group(1).strip()
            conditions['exit_long'] = Condition(
                expression=expr,
                description="Exit condition"
            )
            conditions['exit_short'] = Condition(
                expression=expr,
                description="Exit condition"
            )
        
        return conditions
    
    def _extract_strategy_name(self) -> str:
        """Extract strategy name from Pine Script."""
        # Look for strategy() or indicator() call
        strategy_pattern = r'(?:strategy|indicator)\s*\(\s*["\']([^"\']+)["\']'
        match = re.search(strategy_pattern, self.source_code)
        if match:
            return match.group(1)
        return "UnnamedStrategy"
    
    def _extract_description(self) -> str:
        """Extract strategy description from comments."""
        # Look for comment at the beginning
        desc_pattern = r'^//\s*(.+)$'
        match = re.search(desc_pattern, self.source_code, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_timeframe(self) -> TimeFrame:
        """Extract timeframe from Pine Script."""
        # Look for timeframe in strategy() call
        tf_pattern = r'timeframe\s*=\s*["\']([^"\']+)["\']'
        match = re.search(tf_pattern, self.source_code)
        if match:
            tf_str = match.group(1)
            return self.timeframe_map.get(tf_str, TimeFrame.H1)
        return TimeFrame.H1
    
    def _extract_position_sizing(self) -> PositionSizing:
        """Extract position sizing configuration."""
        # Look for default_qty_value
        size_pattern = r'default_qty_value\s*=\s*(\d+\.?\d*)'
        match = re.search(size_pattern, self.source_code)
        if match:
            return PositionSizing(method="fixed", value=float(match.group(1)))
        return PositionSizing()
    
    def _extract_risk_management(self) -> RiskManagement:
        """Extract risk management parameters."""
        risk = RiskManagement()
        
        # Look for stop_loss in strategy.exit()
        sl_pattern = r'stop\s*=\s*([^,\)]+)'
        match = re.search(sl_pattern, self.source_code)
        if match:
            try:
                risk.stop_loss = float(match.group(1).strip())
            except ValueError:
                pass
        
        # Take profit
        tp_pattern = r'limit\s*=\s*([^,\)]+)'
        match = re.search(tp_pattern, self.source_code)
        if match:
            try:
                risk.take_profit = float(match.group(1).strip())
            except ValueError:
                pass
        
        return risk
    
    def validate_syntax(self, source_code: str) -> bool:
        """
        Validate Pine Script syntax.
        
        Args:
            source_code: Pine Script source code
            
        Returns:
            True if syntax appears valid
        """
        # Check for required Pine Script version declaration
        if '//@version=' not in source_code and 'strategy(' not in source_code:
            return False
        return len(source_code.strip()) > 0
