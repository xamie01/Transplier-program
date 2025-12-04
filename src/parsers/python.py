"""Python strategy parser: extracts IR from Python trading strategy code."""
import ast
from typing import Any, Dict, List, Optional
from src.utils.ast_helpers import (
    get_call_name, literal_value, expr_to_string, find_calls, find_assignments
)


def parse(code: str) -> dict:
    """Parse Python strategy source and produce canonical IR.
    
    Args:
        code: Python source code string
        
    Returns:
        dict with keys: meta, indicators, conditions, orders, position_sizing, timeframes
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Python syntax error: {e}")
    
    # Extract metadata from docstring or comments
    meta = _extract_meta(tree, code)
    
    # Extract indicator calls (SMA, EMA, RSI, etc.)
    indicators, indicator_map = _extract_indicators(tree)
    
    # Extract conditions (entry/exit logic)
    conditions = _extract_conditions(tree, indicator_map)
    
    # Extract orders
    orders = _extract_orders(tree)
    
    # Extract position sizing
    position_sizing = _extract_position_sizing(tree)
    
    # Collect timeframes if mentioned
    timeframes = _extract_timeframes(code)
    
    # Provide mapping of dataframe column names to indicator ids to help
    # downstream translators (and round-trip matching).
    mappings = {
        "column_to_indicator": indicator_map
    }

    return {
        "meta": meta,
        "indicators": indicators,
        "conditions": conditions,
        "orders": orders,
        "position_sizing": position_sizing,
        "timeframes": timeframes,
        "mappings": mappings,
        "metadata": {"version": "0.1", "source": "python_parser"}
    }


def _extract_meta(tree: ast.AST, code: str) -> dict:
    """Extract metadata (name, author, timeframe) from docstring."""
    meta = {
        "name": "Untitled Strategy",
        "author": "Unknown",
        "timeframe": "default"
    }
    
    # Try docstring
    docstring = ast.get_docstring(tree)
    if docstring:
        for line in docstring.split('\n'):
            line_stripped = line.strip()
            low = line_stripped.lower()
            if low.startswith('name:'):
                meta['name'] = line_stripped.split(':', 1)[1].strip()
            elif low.startswith('author:'):
                meta['author'] = line_stripped.split(':', 1)[1].strip()
            elif low.startswith('timeframe:'):
                meta['timeframe'] = line_stripped.split(':', 1)[1].strip()
    
    # Try to find class or function name
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and 'strategy' in node.name.lower():
            meta['name'] = node.name
            break
    
    return meta


def _extract_indicators(tree: ast.AST) -> tuple:
    """Extract all indicator calls and return (list, mapping dict).
    
    Returns:
        (indicators_list, indicator_id_map)
        where indicators_list is IR format and mapping is {var_name -> id}
    """
    indicators: List[Dict[str, Any]] = []
    indicator_map: Dict[str, str] = {}  # variable name -> indicator id
    
    common_indicators = ['sma', 'ema', 'rsi', 'macd', 'bb', 'atr', 'adx']
    calls = find_calls(tree, common_indicators)
    
    ind_counter = 0
    for call in calls:
        func_name = get_call_name(call)
        if not func_name:
            continue
        
        # Normalize function name
        func_name_lower = func_name.lower().split('.')[-1]
        
        # Extract parameters
        params, source = _extract_indicator_params(call, func_name_lower)
        
        ind_id = f"ind_{ind_counter}"
        indicators.append({
            "id": ind_id,
            "type": func_name_lower.upper(),
            "params": params,
            "source": source
        })
        
        # Try to map assignment to this indicator
        # Look for: my_sma = sma(close, 20) or dataframe['sma_15'] = ta.SMA(...)
        for parent in ast.walk(tree):
            if isinstance(parent, ast.Assign):
                if parent.value == call:
                    for target in parent.targets:
                        # simple variable assignment: my_sma = ...
                        if isinstance(target, ast.Name):
                            indicator_map[target.id] = ind_id
                        # subscript assignment: dataframe['sma_15'] = ...
                        elif isinstance(target, ast.Subscript):
                            # extract string key if present
                            try:
                                slice_node = target.slice
                                # Python 3.9+: ast.Constant
                                if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
                                    indicator_map[slice_node.value] = ind_id
                                # older AST: ast.Index
                                elif hasattr(slice_node, 'value') and isinstance(slice_node.value, ast.Constant) and isinstance(slice_node.value.value, str):
                                    indicator_map[slice_node.value.value] = ind_id
                            except Exception:
                                pass
        
        ind_counter += 1
    
    return indicators, indicator_map


def _extract_indicator_params(call: ast.Call, func_name: str) -> tuple:
    """Extract parameters from indicator call.
    
    Returns:
        (params_dict, source_name)
    """
    params = {}
    source = "close"
    
    # Common indicators expect (source, period) or (source, param1, param2, ...)
    if call.args:
        # First arg often the source (close, high, low, etc.)
        first_arg = call.args[0]
        if isinstance(first_arg, ast.Name):
            source = first_arg.id
        
        # Subsequent args are numeric parameters
        for i, arg in enumerate(call.args[1:], 1):
            val = literal_value(arg)
            if val is not None:
                # Name it intelligently
                if func_name in ['sma', 'ema', 'wma']:
                    if i == 1:
                        params['period'] = val
                elif func_name == 'rsi':
                    if i == 1:
                        params['period'] = val
                elif func_name == 'macd':
                    if i == 1:
                        params['fast'] = val
                    elif i == 2:
                        params['slow'] = val
                    elif i == 3:
                        params['signal'] = val
                else:
                    params[f'param{i}'] = val
    
    # Handle keyword arguments
    for kw in call.keywords:
        val = literal_value(kw.value)
        if val is not None:
            params[kw.arg] = val
    
    return params, source


def _extract_conditions(tree: ast.AST, indicator_map: Dict[str, str]) -> dict:
    """Extract entry/exit conditions from if statements and comparisons."""
    conditions = {
        "entry_long": [],
        "exit_long": [],
        "entry_short": [],
        "exit_short": []
    }
    
    class ConditionExtractor(ast.NodeVisitor):
        def visit_If(self, node):
            # Look for patterns like: if sma_cross > 0: buy()
            expr_str = expr_to_string(node.test)
            
            # Heuristic: check if body contains buy/sell/close
            for stmt in node.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    call = stmt.value
                    func_name = get_call_name(call)
                    if func_name and func_name.lower() in ['buy', 'entry', 'long']:
                        conditions["entry_long"].append({"expr": expr_str})
                    elif func_name and func_name.lower() in ['sell', 'close', 'exit', 'short']:
                        conditions["exit_long"].append({"expr": expr_str})
            
            self.generic_visit(node)
    
    ConditionExtractor().visit(tree)
    
    # If no conditions found, try to infer from simple comparisons
    # Also look for dataframe.loc[ (cond), 'enter_long'] = 1 style assignments
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    # pattern: dataframe.loc[(<cond>), 'enter_long'] = 1
                    try:
                        if isinstance(target.value, ast.Attribute) and getattr(target.value, 'attr', '') == 'loc':
                            slice_node = target.slice
                            # tuple slice: (cond_expr, 'col_name')
                            if isinstance(slice_node, ast.Tuple) and len(slice_node.elts) >= 2:
                                cond_node = slice_node.elts[0]
                                col_node = slice_node.elts[1]
                                col_name = None
                                if isinstance(col_node, ast.Constant) and isinstance(col_node.value, str):
                                    col_name = col_node.value
                                elif hasattr(col_node, 's'):
                                    col_name = getattr(col_node, 's', None)
                                if col_name:
                                    expr_str = expr_to_string(cond_node)
                                    if col_name.lower() in ['enter_long', 'entry_long', 'enter', 'buy', 'long']:
                                        conditions['entry_long'].append({'expr': expr_str})
                                    elif col_name.lower() in ['exit_long', 'exit', 'sell', 'close', 'short']:
                                        conditions['exit_long'].append({'expr': expr_str})
                    except Exception:
                        pass

    if not any(conditions.values()):
        # Look for any crossover/crossunder patterns
        calls = find_calls(tree, ['crossover', 'crossunder', 'crosses'])
        for call in calls:
            expr_str = expr_to_string(call)
            func_name = get_call_name(call)
            if func_name and 'crossover' in func_name.lower():
                conditions["entry_long"].append({"expr": expr_str})
            elif func_name and 'crossunder' in func_name.lower():
                conditions["exit_long"].append({"expr": expr_str})
    
    return conditions


def _extract_orders(tree: ast.AST) -> list:
    """Extract order definitions from function calls or class definitions."""
    orders = []
    
    # Look for order-related calls: buy, sell, market_order, etc.
    order_funcs = ['buy', 'sell', 'order', 'market_order', 'limit_order', 'entry', 'close']
    calls = find_calls(tree, order_funcs)
    
    for call in calls:
        func_name = get_call_name(call)
        if not func_name:
            continue
        
        func_name_lower = func_name.lower()
        order_type = "market"
        side = "long"
        size = "pct:10"
        
        # Infer side from function name
        if 'sell' in func_name_lower or 'short' in func_name_lower:
            side = "short"
        elif 'buy' in func_name_lower or 'entry' in func_name_lower:
            side = "long"
        elif 'close' in func_name_lower:
            side = "close"
        
        # Extract size from arguments
        for arg in call.args:
            val = literal_value(arg)
            if isinstance(val, (int, float)):
                size = val
                break
        
        for kw in call.keywords:
            if kw.arg in ['size', 'quantity', 'qty']:
                val = literal_value(kw.value)
                if val is not None:
                    size = val
        
        orders.append({
            "type": order_type,
            "side": side,
            "size": size,
            "reduce_only": False
        })
    
    # If no orders found, use default
    if not orders:
        orders = [{"type": "market", "side": "long", "size": "pct:10", "reduce_only": False}]
    
    return orders


def _extract_position_sizing(tree: ast.AST) -> dict:
    """Extract position sizing configuration."""
    sizing = {"mode": "percent", "value": 10}
    
    # Look for assignments like: risk_percent = 5, position_size = 100
    assignments = find_assignments(tree, ['risk_percent', 'position_size', 'trade_size'])
    
    for assign in assignments:
        val = literal_value(assign.value)
        if val is not None:
            for target in assign.targets:
                if isinstance(target, ast.Name):
                    if 'percent' in target.id.lower():
                        sizing = {"mode": "percent", "value": float(val)}
                    else:
                        sizing = {"mode": "fixed", "value": float(val)}
    
    return sizing


def _extract_timeframes(code: str) -> list:
    """Extract timeframe hints from code (simple string matching)."""
    timeframes = []
    timeframe_strings = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', 'daily', 'weekly']
    code_lower = code.lower()
    
    for tf in timeframe_strings:
        if tf in code_lower:
            timeframes.append(tf)
    
    if not timeframes:
        timeframes = ['default']
    
    return list(set(timeframes))  # deduplicate
