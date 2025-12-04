"""
IR Validator module.

Validates intermediate representation of trading strategies to ensure
data integrity and completeness.
"""

from typing import List, Dict, Any
from src.ir.schema import StrategyIR, Indicator, Condition


class ValidationError(Exception):
    """Raised when IR validation fails."""
    pass


class IRValidator:
    """Validates strategy intermediate representation."""
    
    @staticmethod
    def validate_strategy(strategy: StrategyIR) -> List[str]:
        """
        Validate a strategy IR.
        
        Args:
            strategy: The strategy IR to validate
            
        Returns:
            List of validation warnings (empty if valid)
            
        Raises:
            ValidationError: If validation fails with critical errors
        """
        errors = []
        warnings = []
        
        # Check required fields
        if not strategy.name:
            errors.append("Strategy name is required")
        
        # Check that at least one entry condition exists
        if not strategy.entry_long and not strategy.entry_short:
            errors.append("At least one entry condition (long or short) is required")
        
        # Validate indicators
        for idx, indicator in enumerate(strategy.indicators):
            if not indicator.name:
                errors.append(f"Indicator at index {idx} must have a name")
            if not indicator.parameters:
                warnings.append(f"Indicator '{indicator.name}' has no parameters")
        
        # Validate conditions
        if strategy.entry_long:
            IRValidator._validate_condition(strategy.entry_long, "entry_long", errors)
        if strategy.entry_short:
            IRValidator._validate_condition(strategy.entry_short, "entry_short", errors)
        if strategy.exit_long:
            IRValidator._validate_condition(strategy.exit_long, "exit_long", errors)
        if strategy.exit_short:
            IRValidator._validate_condition(strategy.exit_short, "exit_short", errors)
        
        # Validate position sizing
        if strategy.position_sizing.value <= 0:
            errors.append("Position sizing value must be greater than 0")
        
        # Raise exception if critical errors found
        if errors:
            raise ValidationError(f"Validation failed: {'; '.join(errors)}")
        
        return warnings
    
    @staticmethod
    def _validate_condition(condition: Condition, name: str, errors: List[str]) -> None:
        """Validate a single condition."""
        if not condition.expression:
            errors.append(f"Condition '{name}' must have an expression")
    
    @staticmethod
    def validate_dict(data: Dict[str, Any]) -> List[str]:
        """
        Validate a strategy dictionary before converting to IR.
        
        Args:
            data: Dictionary representation of strategy
            
        Returns:
            List of validation warnings
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            strategy = StrategyIR.from_dict(data)
            return IRValidator.validate_strategy(strategy)
        except KeyError as e:
            raise ValidationError(f"Missing required field: {e}")
        except ValueError as e:
            raise ValidationError(f"Invalid value: {e}")
