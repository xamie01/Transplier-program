"""
Transplier: A trading strategy transpiler.

This package converts trading strategies between different programming languages
and trading platforms using an intermediate representation (IR) format.
"""

__version__ = "0.1.0"

from src.transpiler import Transpiler
from src.converter import Converter

__all__ = ["Transpiler", "Converter"]
