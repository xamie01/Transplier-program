"""
Base generator class for all code generators.

This module provides the abstract base class that all language-specific
code generators should inherit from.
"""

from abc import ABC, abstractmethod
from src.ir.schema import StrategyIR


class GeneratorError(Exception):
    """Raised when code generation fails."""
    pass


class BaseGenerator(ABC):
    """
    Abstract base class for code generators.
    
    Each language-specific generator should inherit from this class
    and implement the generate method.
    """
    
    def __init__(self):
        """Initialize the generator."""
        self.strategy_ir = None
        self.generated_code = ""
    
    @abstractmethod
    def generate(self, strategy_ir: StrategyIR) -> str:
        """
        Generate code from strategy IR.
        
        Args:
            strategy_ir: The strategy IR to convert
            
        Returns:
            Generated source code as string
            
        Raises:
            GeneratorError: If generation fails
        """
        pass
    
    @abstractmethod
    def generate_indicators(self, strategy_ir: StrategyIR) -> str:
        """
        Generate indicator declarations.
        
        Args:
            strategy_ir: The strategy IR
            
        Returns:
            Code string for indicator declarations
        """
        pass
    
    @abstractmethod
    def generate_conditions(self, strategy_ir: StrategyIR) -> str:
        """
        Generate entry/exit condition code.
        
        Args:
            strategy_ir: The strategy IR
            
        Returns:
            Code string for conditions
        """
        pass
    
    @abstractmethod
    def generate_header(self, strategy_ir: StrategyIR) -> str:
        """
        Generate file header/metadata.
        
        Args:
            strategy_ir: The strategy IR
            
        Returns:
            Code string for header
        """
        pass
    
    def format_code(self, code: str) -> str:
        """
        Format the generated code.
        
        Args:
            code: Raw generated code
            
        Returns:
            Formatted code
        """
        # Default implementation - can be overridden
        return code.strip() + "\n"
