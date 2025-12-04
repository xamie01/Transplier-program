"""
Entry condition evaluation module.

This module handles evaluation of entry conditions for trading strategies.
"""

from typing import Dict, Any, Optional
import re


class EntryConditionChecker:
    """
    Evaluate entry conditions for trading strategies.
    """
    
    def __init__(self):
        """Initialize the entry condition checker."""
        self.condition_cache = {}
    
    def check_long_entry(self, condition_expr: str, data: Dict[str, Any]) -> bool:
        """
        Check if long entry condition is met.
        
        Args:
            condition_expr: Condition expression to evaluate
            data: Dictionary with indicator values and price data
            
        Returns:
            True if condition is met
        """
        return self.evaluate_condition(condition_expr, data)
    
    def check_short_entry(self, condition_expr: str, data: Dict[str, Any]) -> bool:
        """
        Check if short entry condition is met.
        
        Args:
            condition_expr: Condition expression to evaluate
            data: Dictionary with indicator values and price data
            
        Returns:
            True if condition is met
        """
        return self.evaluate_condition(condition_expr, data)
    
    def evaluate_condition(self, expression: str, data: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression.
        
        Args:
            expression: Condition expression (e.g., "sma_20 > sma_50")
            data: Dictionary with indicator values
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            # Replace indicator names with their values
            expr = expression
            for key, value in data.items():
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(key) + r'\b'
                expr = re.sub(pattern, str(value), expr)
            
            # Handle special functions
            expr = self._handle_special_functions(expr, data)
            
            # Evaluate the expression safely
            result = eval(expr, {"__builtins__": {}}, {})
            return bool(result)
        except Exception as e:
            print(f"Error evaluating condition: {e}")
            return False
    
    def _handle_special_functions(self, expression: str, data: Dict[str, Any]) -> str:
        """
        Handle special trading functions like crossover, crossunder.
        
        Args:
            expression: Expression string
            data: Data dictionary
            
        Returns:
            Modified expression with functions evaluated
        """
        expr = expression
        
        # Handle crossover function: crossover(a, b) -> a > b and prev_a <= prev_b
        crossover_pattern = r'crossover\((\w+),\s*(\w+)\)'
        for match in re.finditer(crossover_pattern, expr):
            var1 = match.group(1)
            var2 = match.group(2)
            
            current_cross = f"({data.get(var1, 0)} > {data.get(var2, 0)})"
            prev_cross = f"({data.get(f'prev_{var1}', 0)} <= {data.get(f'prev_{var2}', 0)})"
            replacement = f"({current_cross} and {prev_cross})"
            
            expr = expr.replace(match.group(0), replacement)
        
        # Handle crossunder function
        crossunder_pattern = r'crossunder\((\w+),\s*(\w+)\)'
        for match in re.finditer(crossunder_pattern, expr):
            var1 = match.group(1)
            var2 = match.group(2)
            
            current_cross = f"({data.get(var1, 0)} < {data.get(var2, 0)})"
            prev_cross = f"({data.get(f'prev_{var1}', 0)} >= {data.get(f'prev_{var2}', 0)})"
            replacement = f"({current_cross} and {prev_cross})"
            
            expr = expr.replace(match.group(0), replacement)
        
        return expr
    
    def validate_condition(self, expression: str) -> bool:
        """
        Validate that a condition expression is well-formed.
        
        Args:
            expression: Condition expression
            
        Returns:
            True if valid
        """
        if not expression or not expression.strip():
            return False
        
        # Check for balanced parentheses
        if expression.count('(') != expression.count(')'):
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = ['import ', '__', 'eval', 'exec', 'compile']
        for pattern in dangerous_patterns:
            if pattern in expression.lower():
                return False
        
        return True
