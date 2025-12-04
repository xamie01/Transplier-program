"""
Intermediate Representation (IR) module for trading strategies.

This module defines the core IR schema that serves as the universal format
for representing trading strategies across different languages.
"""

from src.ir.schema import StrategyIR, Indicator, Condition, OrderType

__all__ = ["StrategyIR", "Indicator", "Condition", "OrderType"]
