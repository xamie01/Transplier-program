"""
Pine Script code generator.

Generates TradingView Pine Script code from IR.
"""

from src.generators.base_generator import BaseGenerator, GeneratorError
from src.ir.schema import StrategyIR, IndicatorType


class PineScriptGenerator(BaseGenerator):
    """Generator for Pine Script trading strategies."""
    
    def __init__(self):
        """Initialize the Pine Script generator."""
        super().__init__()
    
    def generate(self, strategy_ir: StrategyIR) -> str:
        """
        Generate Pine Script code from strategy IR.
        
        Args:
            strategy_ir: The strategy IR to convert
            
        Returns:
            Generated Pine Script code
            
        Raises:
            GeneratorError: If generation fails
        """
        self.strategy_ir = strategy_ir
        
        parts = []
        parts.append(self.generate_header(strategy_ir))
        parts.append(self.generate_strategy_declaration(strategy_ir))
        parts.append(self.generate_indicators(strategy_ir))
        parts.append(self.generate_conditions(strategy_ir))
        
        code = "\n\n".join(filter(None, parts))
        return self.format_code(code)
    
    def generate_header(self, strategy_ir: StrategyIR) -> str:
        """Generate Pine Script file header."""
        header = f'''// {strategy_ir.name}
// {strategy_ir.description}
// Version: {strategy_ir.version}

//@version=5'''
        return header
    
    def generate_strategy_declaration(self, strategy_ir: StrategyIR) -> str:
        """Generate strategy() declaration."""
        return f'''strategy("{strategy_ir.name}", 
         overlay=true,
         default_qty_type=strategy.fixed,
         default_qty_value={strategy_ir.position_sizing.value})'''
    
    def generate_indicators(self, strategy_ir: StrategyIR) -> str:
        """Generate indicator declarations."""
        if not strategy_ir.indicators:
            return ""
        
        code_lines = ["// Indicators"]
        
        for indicator in strategy_ir.indicators:
            if indicator.type == IndicatorType.SMA:
                period = indicator.parameters.get('period', 20)
                code_lines.append(
                    f"{indicator.name} = ta.sma({indicator.source}, {period})"
                )
            elif indicator.type == IndicatorType.EMA:
                period = indicator.parameters.get('period', 20)
                code_lines.append(
                    f"{indicator.name} = ta.ema({indicator.source}, {period})"
                )
            elif indicator.type == IndicatorType.RSI:
                period = indicator.parameters.get('period', 14)
                code_lines.append(
                    f"{indicator.name} = ta.rsi({indicator.source}, {period})"
                )
            elif indicator.type == IndicatorType.MACD:
                fast = indicator.parameters.get('fast', 12)
                slow = indicator.parameters.get('slow', 26)
                signal = indicator.parameters.get('signal', 9)
                code_lines.append(
                    f"[{indicator.name}, signalLine, histogram] = ta.macd({indicator.source}, {fast}, {slow}, {signal})"
                )
        
        # Add plots
        code_lines.append("")
        code_lines.append("// Plot indicators")
        for indicator in strategy_ir.indicators:
            if indicator.type != IndicatorType.RSI:  # RSI usually plotted in separate pane
                code_lines.append(f'plot({indicator.name}, title="{indicator.name}", color=color.blue)')
        
        return "\n".join(code_lines)
    
    def generate_conditions(self, strategy_ir: StrategyIR) -> str:
        """Generate entry/exit condition code."""
        code_lines = ["// Trading conditions"]
        
        # Entry long
        if strategy_ir.entry_long:
            expr = self._convert_expression(strategy_ir.entry_long.expression)
            code_lines.append(f"longCondition = {expr}")
            
            # Build entry command
            stop_loss = ""
            take_profit = ""
            if strategy_ir.risk_management.stop_loss:
                stop_loss = f", stop=strategy.position_avg_price * (1 - {strategy_ir.risk_management.stop_loss}/100)"
            if strategy_ir.risk_management.take_profit:
                take_profit = f", limit=strategy.position_avg_price * (1 + {strategy_ir.risk_management.take_profit}/100)"
            
            code_lines.append(f'if longCondition')
            code_lines.append(f'    strategy.entry("Long", strategy.long)')
            if stop_loss or take_profit:
                code_lines.append(f'    strategy.exit("Exit Long", "Long"{stop_loss}{take_profit})')
            code_lines.append("")
        
        # Entry short
        if strategy_ir.entry_short:
            expr = self._convert_expression(strategy_ir.entry_short.expression)
            code_lines.append(f"shortCondition = {expr}")
            
            stop_loss = ""
            take_profit = ""
            if strategy_ir.risk_management.stop_loss:
                stop_loss = f", stop=strategy.position_avg_price * (1 + {strategy_ir.risk_management.stop_loss}/100)"
            if strategy_ir.risk_management.take_profit:
                take_profit = f", limit=strategy.position_avg_price * (1 - {strategy_ir.risk_management.take_profit}/100)"
            
            code_lines.append(f'if shortCondition')
            code_lines.append(f'    strategy.entry("Short", strategy.short)')
            if stop_loss or take_profit:
                code_lines.append(f'    strategy.exit("Exit Short", "Short"{stop_loss}{take_profit})')
            code_lines.append("")
        
        # Exit conditions
        if strategy_ir.exit_long:
            expr = self._convert_expression(strategy_ir.exit_long.expression)
            code_lines.append(f"exitCondition = {expr}")
            code_lines.append(f'if exitCondition')
            code_lines.append(f'    strategy.close_all()')
        
        return "\n".join(code_lines)
    
    def _convert_expression(self, expression: str) -> str:
        """
        Convert IR expression to Pine Script.
        
        Args:
            expression: IR expression
            
        Returns:
            Pine Script expression
        """
        # Simple conversion - handle common patterns
        expr = expression
        
        # Crossover/crossunder functions
        expr = expr.replace("crossover(", "ta.crossover(")
        expr = expr.replace("crossunder(", "ta.crossunder(")
        
        # Logical operators
        expr = expr.replace(" and ", " and ")
        expr = expr.replace(" or ", " or ")
        expr = expr.replace(" not ", " not ")
        
        return expr
