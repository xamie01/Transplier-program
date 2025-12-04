"""Position sizing helper with robust parsing and normalization."""
from typing import Any, Dict, List


def _parse_size_token(token: Any) -> Dict[str, Any]:
    """Parse size token like 'pct:10' or numeric values into canonical dict.
    
    Examples:
        "pct:10" -> {"mode": "percent", "value": 10.0}
        10 -> {"mode": "fixed", "value": 10.0}
        "50%" -> {"mode": "percent", "value": 50.0}
    """
    if isinstance(token, dict):
        return token
    if isinstance(token, (int, float)):
        return {"mode": "fixed", "value": float(token)}
    if isinstance(token, str):
        t = token.strip().lower()
        # Handle "pct:10" or "pct10"
        if t.startswith("pct:") or t.startswith("pct"):
            num = t.split(":", 1)[-1] if ":" in t else t.replace("pct", "")
            try:
                return {"mode": "percent", "value": float(num)}
            except ValueError:
                pass
        # Handle "50%"
        if t.endswith("%"):
            try:
                return {"mode": "percent", "value": float(t[:-1])}
            except ValueError:
                pass
        # Try parse as float
        try:
            return {"mode": "fixed", "value": float(token)}
        except Exception:
            pass
    return {"mode": "unknown", "value": token}


def size_from_ir(ir: dict) -> dict:
    """Return normalized `position_sizing` from the IR.
    
    Normalizes common shorthand (e.g. "pct:10") into a canonical dict:
      {"mode": "percent", "value": 10.0}
    
    Args:
        ir: IR dict (expects 'position_sizing' key)
        
    Returns:
        {"mode": <mode>, "value": <value>}
    """
    if not isinstance(ir, dict):
        raise TypeError("ir must be a dict")
    
    ps = ir.get("position_sizing", {})
    if not ps:
        return {"mode": "percent", "value": 10.0}
    
    mode = ps.get("mode")
    value = ps.get("value", ps.get("size"))
    
    if mode is None and isinstance(value, str):
        # Parse shorthand
        parsed = _parse_size_token(value)
        return {"mode": parsed["mode"], "value": parsed["value"]}
    
    if isinstance(value, (str, int, float, dict)):
        parsed = _parse_size_token(value)
        if mode:
            try:
                return {"mode": mode, "value": float(ps.get("value", parsed.get("value")))}
            except Exception:
                return {"mode": mode, "value": parsed.get("value")}
        return parsed
    
    return {"mode": mode or "unknown", "value": value}


def normalize_ir(ir: dict) -> dict:
    """Produce a canonical IR dictionary.
    
    - Ensures top-level keys exist
    - Normalizes `position_sizing`
    - Normalizes `orders[].size` tokens
    
    Args:
        ir: IR dict
        
    Returns:
        Normalized IR dict
    """
    out = dict(ir)
    out.setdefault("meta", {})
    out.setdefault("indicators", [])
    out.setdefault("conditions", {})
    out.setdefault("orders", [])
    out.setdefault("position_sizing", {})
    out.setdefault("timeframes", [])
    out.setdefault("metadata", {})
    
    # Normalize position sizing
    out["position_sizing"] = size_from_ir(out)
    
    # Normalize orders sizes
    normalized_orders: List[Dict[str, Any]] = []
    for o in out.get("orders", []):
        o2 = dict(o)
        if "size" in o2:
            o2["size_parsed"] = _parse_size_token(o2["size"])
        normalized_orders.append(o2)
    out["orders"] = normalized_orders
    
    return out
