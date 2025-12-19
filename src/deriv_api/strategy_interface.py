"""
Strategy Interface
All trading strategies must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class Signal(Enum):
    """Trading signals"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"


@dataclass
class TradeSignal:
    """Trade signal with metadata"""
    signal: Signal
    strength: float = 0.0  # Signal strength 0-1
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TradingStrategy(ABC):
    """
    Base class for all trading strategies
    
    Strategies should:
    1. Process incoming market data via update()
    2. Maintain internal state
    3. Generate signals via get_signal()
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy with parameters
        
        Args:
            params: Strategy-specific parameters
        """
        self.params = params or {}
        self.data_buffer = []  # Store recent candles/ticks
        self.indicators = {}   # Computed indicators
        self.position = None   # Current position info
        
    @abstractmethod
    def update(self, candle: Dict[str, Any]):
        """
        Update strategy with new market data
        
        Args:
            candle: OHLCV candle data
                {
                    'open': float,
                    'high': float,
                    'low': float,
                    'close': float,
                    'epoch': int
                }
        """
        pass
        
    @abstractmethod
    def get_signal(self) -> TradeSignal:
        """
        Generate trading signal based on current state
        
        Returns:
            TradeSignal object with action and metadata
        """
        pass
        
    def reset(self):
        """Reset strategy state"""
        self.data_buffer = []
        self.indicators = {}
        self.position = None
        
    def set_position(self, position: Optional[Dict[str, Any]]):
        """Update current position info"""
        self.position = position
        
    @property
    def name(self) -> str:
        """Strategy name"""
        return self.__class__.__name__
        
    @property
    def required_candles(self) -> int:
        """Minimum candles needed before generating signals"""
        return 50  # Override in subclass
