"""
Base parser class for all language parsers.

This module provides the abstract base class that all language-specific
parsers should inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from src.ir.schema import StrategyIR


class ParserError(Exception):
    """Raised when parsing fails."""
    pass


class BaseParser(ABC):
    """
    Abstract base class for strategy parsers.
    
    Each language-specific parser should inherit from this class
    and implement the parse method.
    """
    
    def __init__(self):
        """Initialize the parser."""
        self.source_code = ""
        self.strategy_ir = None
    
    @abstractmethod
    def parse(self, source_code: str) -> StrategyIR:
        """
        Parse source code and convert to IR.
        
        Args:
            source_code: The source code to parse
            
        Returns:
            StrategyIR object representing the strategy
            
        Raises:
            ParserError: If parsing fails
        """
        pass
    
    @abstractmethod
    def extract_indicators(self, source_code: str) -> list:
        """
        Extract indicators from source code.
        
        Args:
            source_code: The source code to analyze
            
        Returns:
            List of Indicator objects
        """
        pass
    
    @abstractmethod
    def extract_conditions(self, source_code: str) -> Dict[str, Any]:
        """
        Extract entry/exit conditions from source code.
        
        Args:
            source_code: The source code to analyze
            
        Returns:
            Dictionary with entry_long, entry_short, exit_long, exit_short
        """
        pass
    
    def validate_syntax(self, source_code: str) -> bool:
        """
        Validate the syntax of source code.
        
        Args:
            source_code: The source code to validate
            
        Returns:
            True if syntax is valid, False otherwise
        """
        # Default implementation - can be overridden
        return len(source_code.strip()) > 0
