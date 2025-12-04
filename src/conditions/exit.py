"""
Exit condition evaluation module.

This module handles evaluation of exit conditions for trading strategies.
"""

from typing import Dict, Any, Optional


class ExitConditionChecker:
    """
    Evaluate exit conditions for trading strategies.
    """
    
    def __init__(self):
        """Initialize the exit condition checker."""
        self.position_data = {}
    
    def check_exit(self, 
                   condition_expr: Optional[str],
                   data: Dict[str, Any],
                   position_side: str,
                   entry_price: float,
                   current_price: float,
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> bool:
        """
        Check if exit condition is met.
        
        Args:
            condition_expr: Exit condition expression (optional)
            data: Dictionary with indicator values and price data
            position_side: "long" or "short"
            entry_price: Entry price of the position
            current_price: Current market price
            stop_loss: Stop loss level (percentage or price)
            take_profit: Take profit level (percentage or price)
            
        Returns:
            True if position should be exited
        """
        # Check stop loss
        if stop_loss and self._check_stop_loss(position_side, entry_price, current_price, stop_loss):
            return True
        
        # Check take profit
        if take_profit and self._check_take_profit(position_side, entry_price, current_price, take_profit):
            return True
        
        # Check custom condition
        if condition_expr:
            from src.conditions.entry import EntryConditionChecker
            checker = EntryConditionChecker()
            return checker.evaluate_condition(condition_expr, data)
        
        return False
    
    def _check_stop_loss(self, 
                        position_side: str, 
                        entry_price: float, 
                        current_price: float, 
                        stop_loss: float) -> bool:
        """
        Check if stop loss has been hit.
        
        Args:
            position_side: "long" or "short"
            entry_price: Entry price
            current_price: Current price
            stop_loss: Stop loss level (as percentage or absolute value)
            
        Returns:
            True if stop loss hit
        """
        if stop_loss < 0:
            # Assume it's already a negative value for loss
            sl_price = entry_price * (1 + stop_loss / 100)
        elif stop_loss < 1:
            # It's a percentage in decimal form (e.g., 0.02 for 2%)
            sl_price = entry_price * (1 - stop_loss) if position_side == "long" else entry_price * (1 + stop_loss)
        else:
            # It's an absolute price
            sl_price = stop_loss
        
        if position_side == "long":
            return current_price <= sl_price
        else:  # short
            return current_price >= sl_price
    
    def _check_take_profit(self,
                          position_side: str,
                          entry_price: float,
                          current_price: float,
                          take_profit: float) -> bool:
        """
        Check if take profit has been hit.
        
        Args:
            position_side: "long" or "short"
            entry_price: Entry price
            current_price: Current price
            take_profit: Take profit level
            
        Returns:
            True if take profit hit
        """
        if take_profit < 1:
            # It's a percentage in decimal form
            tp_price = entry_price * (1 + take_profit) if position_side == "long" else entry_price * (1 - take_profit)
        else:
            # It's an absolute price
            tp_price = take_profit
        
        if position_side == "long":
            return current_price >= tp_price
        else:  # short
            return current_price <= tp_price
    
    def check_trailing_stop(self,
                           position_side: str,
                           entry_price: float,
                           current_price: float,
                           highest_price: float,
                           lowest_price: float,
                           trailing_stop_pct: float) -> bool:
        """
        Check if trailing stop has been hit.
        
        Args:
            position_side: "long" or "short"
            entry_price: Entry price
            current_price: Current price
            highest_price: Highest price since entry (for long)
            lowest_price: Lowest price since entry (for short)
            trailing_stop_pct: Trailing stop percentage
            
        Returns:
            True if trailing stop hit
        """
        if position_side == "long":
            stop_price = highest_price * (1 - trailing_stop_pct / 100)
            return current_price <= stop_price
        else:  # short
            stop_price = lowest_price * (1 + trailing_stop_pct / 100)
            return current_price >= stop_price
    
    def check_time_exit(self, 
                       entry_time: float, 
                       current_time: float, 
                       max_holding_period: float) -> bool:
        """
        Check if maximum holding period has been exceeded.
        
        Args:
            entry_time: Entry timestamp
            current_time: Current timestamp
            max_holding_period: Maximum holding period (in same units as timestamps)
            
        Returns:
            True if max holding period exceeded
        """
        return (current_time - entry_time) >= max_holding_period
