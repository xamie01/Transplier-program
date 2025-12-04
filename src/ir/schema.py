"""
IR Schema definitions for trading strategies.

This module defines the core data structures that represent trading strategies
in a language-agnostic format.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class IndicatorType(Enum):
    """Supported indicator types."""
    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"
    ATR = "atr"
    STOCHASTIC = "stochastic"
    ADX = "adx"
    CCI = "cci"
    VWAP = "vwap"


class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class PositionSide(Enum):
    """Position side."""
    LONG = "long"
    SHORT = "short"


class TimeFrame(Enum):
    """Supported timeframes."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1M"


@dataclass
class Indicator:
    """Represents a technical indicator."""
    type: IndicatorType
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    source: str = "close"  # Default data source
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert indicator to dictionary."""
        return {
            "type": self.type.value,
            "name": self.name,
            "parameters": self.parameters,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Indicator":
        """Create indicator from dictionary."""
        return cls(
            type=IndicatorType(data["type"]),
            name=data["name"],
            parameters=data.get("parameters", {}),
            source=data.get("source", "close")
        )


@dataclass
class Condition:
    """Represents a trading condition (entry/exit)."""
    expression: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert condition to dictionary."""
        return {
            "expression": self.expression,
            "description": self.description,
            "parameters": self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Condition":
        """Create condition from dictionary."""
        return cls(
            expression=data["expression"],
            description=data.get("description"),
            parameters=data.get("parameters", {})
        )


@dataclass
class PositionSizing:
    """Position sizing configuration."""
    method: str = "fixed"  # fixed, percent, risk_based
    value: float = 1.0
    max_position: Optional[float] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position sizing to dictionary."""
        return {
            "method": self.method,
            "value": self.value,
            "max_position": self.max_position,
            "parameters": self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PositionSizing":
        """Create position sizing from dictionary."""
        return cls(
            method=data.get("method", "fixed"),
            value=data.get("value", 1.0),
            max_position=data.get("max_position"),
            parameters=data.get("parameters", {})
        )


@dataclass
class RiskManagement:
    """Risk management configuration."""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    max_drawdown: Optional[float] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert risk management to dictionary."""
        return {
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "trailing_stop": self.trailing_stop,
            "max_drawdown": self.max_drawdown,
            "parameters": self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskManagement":
        """Create risk management from dictionary."""
        return cls(
            stop_loss=data.get("stop_loss"),
            take_profit=data.get("take_profit"),
            trailing_stop=data.get("trailing_stop"),
            max_drawdown=data.get("max_drawdown"),
            parameters=data.get("parameters", {})
        )


@dataclass
class StrategyIR:
    """
    Intermediate Representation of a trading strategy.
    
    This serves as the universal format for representing strategies
    across different programming languages and trading platforms.
    """
    name: str
    description: str = ""
    version: str = "1.0.0"
    timeframe: TimeFrame = TimeFrame.H1
    indicators: List[Indicator] = field(default_factory=list)
    entry_long: Optional[Condition] = None
    entry_short: Optional[Condition] = None
    exit_long: Optional[Condition] = None
    exit_short: Optional[Condition] = None
    position_sizing: PositionSizing = field(default_factory=PositionSizing)
    risk_management: RiskManagement = field(default_factory=RiskManagement)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy IR to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "timeframe": self.timeframe.value,
            "indicators": [ind.to_dict() for ind in self.indicators],
            "entry_long": self.entry_long.to_dict() if self.entry_long else None,
            "entry_short": self.entry_short.to_dict() if self.entry_short else None,
            "exit_long": self.exit_long.to_dict() if self.exit_long else None,
            "exit_short": self.exit_short.to_dict() if self.exit_short else None,
            "position_sizing": self.position_sizing.to_dict(),
            "risk_management": self.risk_management.to_dict(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyIR":
        """Create strategy IR from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            timeframe=TimeFrame(data.get("timeframe", "1h")),
            indicators=[Indicator.from_dict(ind) for ind in data.get("indicators", [])],
            entry_long=Condition.from_dict(data["entry_long"]) if data.get("entry_long") else None,
            entry_short=Condition.from_dict(data["entry_short"]) if data.get("entry_short") else None,
            exit_long=Condition.from_dict(data["exit_long"]) if data.get("exit_long") else None,
            exit_short=Condition.from_dict(data["exit_short"]) if data.get("exit_short") else None,
            position_sizing=PositionSizing.from_dict(data.get("position_sizing", {})),
            risk_management=RiskManagement.from_dict(data.get("risk_management", {})),
            metadata=data.get("metadata", {})
        )
