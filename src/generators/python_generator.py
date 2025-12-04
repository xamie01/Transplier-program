"""
Python code generator.

Generates Python trading strategy code from IR.
"""

from src.generators.base_generator import BaseGenerator, GeneratorError
from src.ir.schema import StrategyIR, IndicatorType


class PythonGenerator(BaseGenerator):
    """Generator for Python trading strategies."""
    
    def __init__(self):
        """Initialize the Python generator."""
        super().__init__()
    
    def generate(self, strategy_ir: StrategyIR) -> str:
        """
        Generate Python code from strategy IR.
        
        Args:
            strategy_ir: The strategy IR to convert
            
        Returns:
            Generated Python code
            
        Raises:
            GeneratorError: If generation fails
        """
        self.strategy_ir = strategy_ir
        
        parts = []
        parts.append(self.generate_header(strategy_ir))
        parts.append(self.generate_imports())
        parts.append(self.generate_class_definition(strategy_ir))
        parts.append(self.generate_indicators(strategy_ir))
        parts.append(self.generate_conditions(strategy_ir))
        parts.append(self.generate_execution())
        
        code = "\n\n".join(filter(None, parts))
        return self.format_code(code)
    
    def generate_header(self, strategy_ir: StrategyIR) -> str:
        """Generate Python file header."""
        header = f'''"""
{strategy_ir.name}

{strategy_ir.description}

Strategy Configuration:
- Timeframe: {strategy_ir.timeframe.value}
- Version: {strategy_ir.version}
"""'''
        return header
    
    def generate_imports(self) -> str:
        """Generate import statements."""
        return """from typing import Optional
import pandas as pd
import numpy as np"""
    
    def generate_class_definition(self, strategy_ir: StrategyIR) -> str:
        """Generate class definition."""
        class_name = strategy_ir.name.replace(" ", "").replace("-", "")
        return f"""class {class_name}Strategy:
    \"\"\"
    {strategy_ir.description}
    \"\"\"
    
    def __init__(self):
        self.name = "{strategy_ir.name}"
        self.timeframe = "{strategy_ir.timeframe.value}"
        self.position_size = {strategy_ir.position_sizing.value}
        self.stop_loss = {strategy_ir.risk_management.stop_loss if strategy_ir.risk_management.stop_loss else 'None'}
        self.take_profit = {strategy_ir.risk_management.take_profit if strategy_ir.risk_management.take_profit else 'None'}"""
    
    def generate_indicators(self, strategy_ir: StrategyIR) -> str:
        """Generate indicator calculation code."""
        if not strategy_ir.indicators:
            return ""
        
        code_lines = ["    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:"]
        code_lines.append('        """Calculate technical indicators."""')
        
        for indicator in strategy_ir.indicators:
            if indicator.type == IndicatorType.SMA:
                period = indicator.parameters.get('period', 20)
                code_lines.append(
                    f"        data['{indicator.name}'] = data['{indicator.source}'].rolling(window={period}).mean()"
                )
            elif indicator.type == IndicatorType.EMA:
                period = indicator.parameters.get('period', 20)
                code_lines.append(
                    f"        data['{indicator.name}'] = data['{indicator.source}'].ewm(span={period}, adjust=False).mean()"
                )
            elif indicator.type == IndicatorType.RSI:
                period = indicator.parameters.get('period', 14)
                code_lines.append(f"        # RSI calculation for {indicator.name}")
                code_lines.append(f"        delta = data['{indicator.source}'].diff()")
                code_lines.append(f"        gain = (delta.where(delta > 0, 0)).rolling(window={period}).mean()")
                code_lines.append(f"        loss = (-delta.where(delta < 0, 0)).rolling(window={period}).mean()")
                code_lines.append(f"        rs = gain / loss")
                code_lines.append(f"        data['{indicator.name}'] = 100 - (100 / (1 + rs))")
        
        code_lines.append("        return data")
        return "\n".join(code_lines)
    
    def generate_conditions(self, strategy_ir: StrategyIR) -> str:
        """Generate entry/exit condition code."""
        code_lines = ["    def check_signals(self, data: pd.DataFrame) -> dict:"]
        code_lines.append('        """Check for entry and exit signals."""')
        code_lines.append("        signals = {")
        code_lines.append("            'entry_long': False,")
        code_lines.append("            'entry_short': False,")
        code_lines.append("            'exit_long': False,")
        code_lines.append("            'exit_short': False")
        code_lines.append("        }")
        code_lines.append("")
        code_lines.append("        if len(data) < 2:")
        code_lines.append("            return signals")
        code_lines.append("")
        
        # Entry long
        if strategy_ir.entry_long:
            code_lines.append("        # Entry long condition")
            expr = self._convert_expression(strategy_ir.entry_long.expression)
            code_lines.append(f"        signals['entry_long'] = {expr}")
            code_lines.append("")
        
        # Entry short
        if strategy_ir.entry_short:
            code_lines.append("        # Entry short condition")
            expr = self._convert_expression(strategy_ir.entry_short.expression)
            code_lines.append(f"        signals['entry_short'] = {expr}")
            code_lines.append("")
        
        # Exit conditions
        if strategy_ir.exit_long:
            code_lines.append("        # Exit condition")
            expr = self._convert_expression(strategy_ir.exit_long.expression)
            code_lines.append(f"        signals['exit_long'] = {expr}")
            code_lines.append(f"        signals['exit_short'] = {expr}")
        
        code_lines.append("        return signals")
        return "\n".join(code_lines)
    
    def generate_execution(self) -> str:
        """Generate strategy execution code."""
        return """    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        \"\"\"
        Run the strategy on historical data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicators and signals
        \"\"\"
        data = self.calculate_indicators(data)
        signals = self.check_signals(data)
        
        # Add signals to dataframe
        for key, value in signals.items():
            data[key] = value
        
        return data


if __name__ == "__main__":
    # Example usage
    strategy = Strategy()
    print(f"Strategy: {strategy.name}")
    print(f"Timeframe: {strategy.timeframe}")"""
    
    def _convert_expression(self, expression: str) -> str:
        """
        Convert IR expression to Python.
        
        Args:
            expression: IR expression
            
        Returns:
            Python expression
        """
        # Simple conversion - handle common patterns
        expr = expression.replace("crossover", "self._crossover")
        expr = expr.replace("crossunder", "self._crossunder")
        
        # Handle data access
        expr = expr.replace("close", "data['close'].iloc[-1]")
        expr = expr.replace("open", "data['open'].iloc[-1]")
        expr = expr.replace("high", "data['high'].iloc[-1]")
        expr = expr.replace("low", "data['low'].iloc[-1]")
        
        return expr
