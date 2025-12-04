"""IR normalization and equivalence checking."""
import re
from typing import Any, Dict, List


def _parse_size_token(token: Any) -> Dict[str, Any]:
    """Parse size token like 'pct:10' or numeric values into canonical dict."""
    if isinstance(token, dict):
        return token
    if isinstance(token, (int, float)):
        return {"mode": "fixed", "value": float(token)}
    if isinstance(token, str):
        t = token.strip().lower()
        if t.startswith("pct:") or t.startswith("pct"):
            num = t.split(":", 1)[-1] if ":" in t else t.replace("pct", "")
            try:
                return {"mode": "percent", "value": float(num)}
            except ValueError:
                pass
        try:
            return {"mode": "fixed", "value": float(token)}
        except Exception:
            pass
    return {"mode": "unknown", "value": token}


def _is_number(s: Any) -> bool:
    """Return True if `s` can be parsed as a float (numeric string)."""
    try:
        float(s)
        return True
    except Exception:
        return False


def normalize_ir(ir: dict) -> dict:
    """Produce a canonical IR dictionary with normalized fields.
    
    - Ensures top-level keys exist
    - Normalizes `position_sizing`
    - Normalizes `orders[].size` tokens
    - Ensures indicators have required fields
    """
    out = dict(ir)  # shallow copy
    
    # Ensure top-level keys exist
    out.setdefault("meta", {})
    out.setdefault("indicators", [])
    out.setdefault("conditions", {})
    out.setdefault("orders", [])
    out.setdefault("position_sizing", {})
    out.setdefault("timeframes", [])
    out.setdefault("metadata", {})
    
    # Normalize position sizing
    ps = out["position_sizing"]
    if ps and isinstance(ps, dict):
        mode = ps.get("mode")
        value = ps.get("value", ps.get("size"))
        if mode and isinstance(value, (int, float)):
            out["position_sizing"] = {"mode": mode, "value": float(value)}
        else:
            parsed = _parse_size_token(value if value is not None else ps)
            out["position_sizing"] = parsed
    else:
        out["position_sizing"] = {"mode": "percent", "value": 10.0}
    
    # Normalize indicators
    normalized_inds: List[Dict[str, Any]] = []
    for i, ind in enumerate(out.get("indicators", [])):
        ind2 = dict(ind)
        if not ind2.get("id"):
            ind2["id"] = f"ind_{i}"
        ind2.setdefault("type", "UNKNOWN")
        # Normalize params keys: many libs use 'timeperiod' while our Pine generator uses 'period'
        params = dict(ind2.get("params", {}) or {})
        if "timeperiod" in params and "period" not in params:
            params["period"] = params.pop("timeperiod")
        # Ensure numeric params are canonical types
        for k, v in list(params.items()):
            try:
                if isinstance(v, str) and v.isdigit():
                    params[k] = int(v)
                elif isinstance(v, (int, float)):
                    params[k] = v
                else:
                    # attempt float conversion for numeric strings
                    params[k] = float(v) if isinstance(v, str) and _is_number(v) else v
            except Exception:
                params[k] = v

        ind2["params"] = params

        # Normalize source references: many parsers use 'dataframe' or DataFrame column refs
        src = ind2.get("source", "close")
        if isinstance(src, str) and src.lower().startswith("dataframe"):
            src = "close"
        ind2.setdefault("source", src)
        normalized_inds.append(ind2)
    out["indicators"] = normalized_inds
    
    # Normalize orders
    normalized_orders: List[Dict[str, Any]] = []
    for ord in out.get("orders", []):
        ord2 = dict(ord)
        if "size" in ord2:
            ord2["size_parsed"] = _parse_size_token(ord2["size"])
        ord2.setdefault("type", "market")
        ord2.setdefault("side", "long")
        ord2.setdefault("reduce_only", False)
        normalized_orders.append(ord2)
    out["orders"] = normalized_orders
    
    # Normalize conditions
    conds = out.get("conditions", {})
    for key in ["entry_long", "entry_short", "exit_long", "exit_short"]:
        if key not in conds:
            conds[key] = []
    out["conditions"] = conds
    
    return out


def ir_equivalent(a: dict, b: dict) -> bool:
    """Deterministic check for IR equivalence.
    
    Compares indicators by (id, type, params, source) and conditions by their expressions.
    This is conservative — extend as needed for more complex IR structures.
    
    Args:
        a, b: Two IR dictionaries
        
    Returns:
        True if both IRs describe functionally equivalent strategies
    """
    a_norm = normalize_ir(a)
    b_norm = normalize_ir(b)
    
    # Compare indicators
    def key_ind(x):
        # Produce a canonical representation of an indicator for comparison.
        params = dict(x.get("params", {}) or {})
        # Accept both 'period' and 'timeperiod' as equivalent
        if "timeperiod" in params and "period" not in params:
            params["period"] = params.pop("timeperiod")
        if "period" in params and isinstance(params["period"], float) and params["period"].is_integer():
            params["period"] = int(params["period"])

        # Normalize source names (dataframe.* -> close)
        src = x.get("source", "close")
        try:
            if isinstance(src, str) and src.lower().startswith("dataframe"):
                src = "close"
        except Exception:
            src = str(src)

        # Sort params items for deterministic comparison
        params_items = tuple(sorted(params.items()))
        return (x.get("type"), params_items, src)
    
    ai = sorted([key_ind(i) for i in a_norm.get("indicators", [])])
    bi = sorted([key_ind(i) for i in b_norm.get("indicators", [])])
    if ai != bi:
        return False
    
    # Compare conditions
    def _normalize_expr(expr: str) -> str:
        if not isinstance(expr, str):
            return str(expr)
        # Normalize common crossover/crossunder patterns by collapsing indicator args
        def _collapse_args(m):
            return f"{m.group(1)}(ind,ind)"

        expr = re.sub(r"\b(crossover|crossunder)\s*\([^,]+,[^)]+\)", _collapse_args, expr)
        return expr.strip()

    def flatten_conditions(cond_block: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        exprs = []
        for k in sorted(cond_block.keys()):
            for item in cond_block.get(k, []):
                exprs.append(_normalize_expr(item.get("expr", "")))
        return sorted(exprs)
    
    ac = flatten_conditions(a_norm.get("conditions", {}))
    bc = flatten_conditions(b_norm.get("conditions", {}))
    if ac != bc:
        return False
    
    # Compare position sizing
    ps_a = a_norm.get("position_sizing", {})
    ps_b = b_norm.get("position_sizing", {})
    if ps_a != ps_b:
        return False
    
    return True
