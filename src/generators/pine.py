"""IR to Pine Script generator."""
from typing import Dict, List, Any


def generate(ir: dict) -> str:
    """Generate Pine Script code from canonical IR.
    
    Args:
        ir: canonical IR dict with keys: meta, indicators, conditions, orders, position_sizing
        
    Returns:
        Pine Script source code (string)
    """
    meta = ir.get('meta', {})
    indicators = ir.get('indicators', [])
    conditions = ir.get('conditions', {})
    orders = ir.get('orders', [])
    position_sizing = ir.get('position_sizing', {})
    
    # Start building Pine Script
    lines = []
    
    # Header
    name = meta.get('name', 'Strategy')
    author = meta.get('author', 'Unknown')
    lines.append(f'//@version=5')
    lines.append(f'strategy("{name}", author="{author}", overlay=true)')
    lines.append('')
    
    # Indicator declarations
    for ind in indicators:
        ind_id = ind.get('id', 'unknown')
        ind_type = ind.get('type', '').upper()
        params = ind.get('params', {})
        source = ind.get('source', 'close')
        
        # Generate indicator variable
        params_str = _params_to_pine(params)
        lines.append(f'{ind_id} = ta.{ind_type.lower()}({source}, {params_str})')
    
    if indicators:
        lines.append('')
    
    # Position sizing
    size_mode = position_sizing.get('mode', 'percent')
    size_value = position_sizing.get('value', 10)
    if size_mode == 'percent':
        size_expr = f'{size_value}'
    else:
        size_expr = f'{int(size_value)}'
    
    lines.append(f'size = {size_expr}')
    lines.append('')
    
    # Entry conditions
    entry_conds = conditions.get('entry_long', [])
    exit_conds = conditions.get('exit_long', [])
    
    for cond in entry_conds:
        expr = cond.get('expr', 'false')
        expr_pine = _convert_expr_to_pine(expr)
        lines.append(f'if {expr_pine}')
        if size_mode == 'percent':
            lines.append(f'    strategy.entry("long", strategy.long, qty=strategy.position_size * size / 100)')
        else:
            lines.append(f'    strategy.entry("long", strategy.long, qty={int(size_value)})')
    
    lines.append('')
    
    for cond in exit_conds:
        expr = cond.get('expr', 'false')
        expr_pine = _convert_expr_to_pine(expr)
        lines.append(f'if {expr_pine}')
        lines.append(f'    strategy.close("long")')
    
    return '\n'.join(lines)


def _params_to_pine(params: Dict[str, Any]) -> str:
    """Convert IR params dict to Pine function call arguments."""
    if not params:
        return ''
    
    parts = []
    # Order: period, fast, slow, signal (common indicators)
    order = ['period', 'fast', 'slow', 'signal']
    for key in order:
        if key in params:
            parts.append(str(params[key]))
    
    # Remaining params
    for key in sorted(params.keys()):
        if key not in order:
            parts.append(str(params[key]))
    
    return ', '.join(parts)


def _convert_expr_to_pine(expr: str) -> str:
    """Convert IR expression format to Pine Script syntax.
    
    Simple conversion of common patterns:
        crossover(ind:s1, ind:s2) -> ta.crossover(s1, s2)
        ind:s1 > ind:s2 -> s1 > s2
    """
    result = expr
    
    # Replace ind:id with just id
    import re
    result = re.sub(r'ind:(\w+)', r'\1', result)
    
    # Replace function names
    result = result.replace('crossover(', 'ta.crossover(')
    result = result.replace('crossunder(', 'ta.crossunder(')
    
    return result
