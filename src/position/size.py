"""
Position sizing module.

This module handles position sizing calculations for trading strategies.
"""

from typing import Dict, Any, Optional
from enum import Enum


class SizingMethod(Enum):
    """Position sizing methods."""
    FIXED = "fixed"
    PERCENT = "percent"
    RISK_BASED = "risk_based"
    KELLY = "kelly"
    OPTIMAL_F = "optimal_f"


class PositionSizer:
    """
    Calculate position sizes for trading strategies.
    
    Supports multiple position sizing methods including fixed size,
    percentage of capital, risk-based sizing, and more advanced methods.
    """
    
    def __init__(self, method: str = "fixed", **kwargs):
        """
        Initialize the position sizer.
        
        Args:
            method: Sizing method (fixed, percent, risk_based, kelly, optimal_f)
            **kwargs: Additional parameters for the sizing method
        """
        self.method = SizingMethod(method)
        self.parameters = kwargs
    
    def calculate_size(self, 
                      account_value: float,
                      entry_price: float,
                      stop_loss: Optional[float] = None,
                      **kwargs) -> float:
        """
        Calculate position size.
        
        Args:
            account_value: Current account value
            entry_price: Entry price for the position
            stop_loss: Stop loss price (required for risk-based sizing)
            **kwargs: Additional parameters
            
        Returns:
            Position size (number of units/contracts)
        """
        if self.method == SizingMethod.FIXED:
            return self._fixed_size(**kwargs)
        elif self.method == SizingMethod.PERCENT:
            return self._percent_size(account_value, entry_price, **kwargs)
        elif self.method == SizingMethod.RISK_BASED:
            return self._risk_based_size(account_value, entry_price, stop_loss, **kwargs)
        elif self.method == SizingMethod.KELLY:
            return self._kelly_size(account_value, entry_price, **kwargs)
        elif self.method == SizingMethod.OPTIMAL_F:
            return self._optimal_f_size(account_value, entry_price, **kwargs)
        else:
            raise ValueError(f"Unknown sizing method: {self.method}")
    
    def _fixed_size(self, **kwargs) -> float:
        """
        Calculate fixed position size.
        
        Returns:
            Fixed number of units
        """
        return self.parameters.get('size', kwargs.get('size', 1.0))
    
    def _percent_size(self, account_value: float, entry_price: float, **kwargs) -> float:
        """
        Calculate position size as percentage of account.
        
        Args:
            account_value: Current account value
            entry_price: Entry price
            
        Returns:
            Number of units based on percentage
        """
        percent = self.parameters.get('percent', kwargs.get('percent', 0.1))
        capital_to_risk = account_value * percent
        return capital_to_risk / entry_price
    
    def _risk_based_size(self, 
                        account_value: float, 
                        entry_price: float, 
                        stop_loss: Optional[float],
                        **kwargs) -> float:
        """
        Calculate position size based on risk per trade.
        
        Args:
            account_value: Current account value
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Number of units based on risk
        """
        if stop_loss is None:
            raise ValueError("Stop loss is required for risk-based sizing")
        
        risk_percent = self.parameters.get('risk_percent', kwargs.get('risk_percent', 0.01))
        capital_to_risk = account_value * risk_percent
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return 0
        
        # Calculate position size
        position_size = capital_to_risk / risk_per_unit
        
        # Apply max position limit if specified
        max_position = self.parameters.get('max_position', kwargs.get('max_position'))
        if max_position:
            position_size = min(position_size, max_position)
        
        return position_size
    
    def _kelly_size(self, account_value: float, entry_price: float, **kwargs) -> float:
        """
        Calculate position size using Kelly Criterion.
        
        Args:
            account_value: Current account value
            entry_price: Entry price
            
        Returns:
            Number of units based on Kelly Criterion
        """
        win_rate = self.parameters.get('win_rate', kwargs.get('win_rate', 0.5))
        win_loss_ratio = self.parameters.get('win_loss_ratio', kwargs.get('win_loss_ratio', 1.5))
        
        # Kelly formula: f = (p * b - q) / b
        # where p = win probability, q = loss probability, b = win/loss ratio
        kelly_fraction = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Apply Kelly fraction conservatively (typically use half-Kelly)
        kelly_multiplier = self.parameters.get('kelly_multiplier', kwargs.get('kelly_multiplier', 0.5))
        kelly_fraction *= kelly_multiplier
        
        # Ensure non-negative
        kelly_fraction = max(0, kelly_fraction)
        
        capital_to_use = account_value * kelly_fraction
        return capital_to_use / entry_price
    
    def _optimal_f_size(self, account_value: float, entry_price: float, **kwargs) -> float:
        """
        Calculate position size using Optimal F.
        
        Args:
            account_value: Current account value
            entry_price: Entry price
            
        Returns:
            Number of units based on Optimal F
        """
        optimal_f = self.parameters.get('optimal_f', kwargs.get('optimal_f', 0.2))
        capital_to_use = account_value * optimal_f
        return capital_to_use / entry_price
    
    def validate_size(self, 
                     position_size: float, 
                     account_value: float, 
                     entry_price: float,
                     max_leverage: float = 1.0) -> float:
        """
        Validate and adjust position size based on constraints.
        
        Args:
            position_size: Calculated position size
            account_value: Current account value
            entry_price: Entry price
            max_leverage: Maximum leverage allowed
            
        Returns:
            Validated position size
        """
        # Check minimum size
        min_size = self.parameters.get('min_size', 0.0)
        if position_size < min_size:
            return 0.0
        
        # Check maximum leverage
        max_position_value = account_value * max_leverage
        max_units = max_position_value / entry_price
        
        return min(position_size, max_units)


class PortfolioSizer:
    """
    Manage position sizing across multiple positions in a portfolio.
    """
    
    def __init__(self, max_positions: int = 10, max_exposure: float = 1.0):
        """
        Initialize portfolio sizer.
        
        Args:
            max_positions: Maximum number of concurrent positions
            max_exposure: Maximum portfolio exposure (e.g., 1.0 = 100%)
        """
        self.max_positions = max_positions
        self.max_exposure = max_exposure
        self.positions: Dict[str, Dict[str, Any]] = {}
    
    def add_position(self, symbol: str, size: float, entry_price: float):
        """Add a position to the portfolio."""
        self.positions[symbol] = {
            'size': size,
            'entry_price': entry_price,
            'value': size * entry_price
        }
    
    def remove_position(self, symbol: str):
        """Remove a position from the portfolio."""
        if symbol in self.positions:
            del self.positions[symbol]
    
    def get_total_exposure(self, account_value: float) -> float:
        """
        Calculate total portfolio exposure.
        
        Args:
            account_value: Current account value
            
        Returns:
            Portfolio exposure as a fraction
        """
        total_value = sum(pos['value'] for pos in self.positions.values())
        return total_value / account_value if account_value > 0 else 0.0
    
    def can_add_position(self, account_value: float, position_value: float) -> bool:
        """
        Check if a new position can be added.
        
        Args:
            account_value: Current account value
            position_value: Value of new position
            
        Returns:
            True if position can be added
        """
        if len(self.positions) >= self.max_positions:
            return False
        
        new_exposure = self.get_total_exposure(account_value) + (position_value / account_value)
        return new_exposure <= self.max_exposure
