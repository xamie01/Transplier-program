"""Indicator registry and cross-language mappings."""

# Canonical indicator definitions
INDICATORS = {
    "SMA": {
        "params": ["period"],
        "sources": ["close", "high", "low", "open"],
        "description": "Simple Moving Average",
    },
    "EMA": {
        "params": ["period"],
        "sources": ["close", "high", "low", "open"],
        "description": "Exponential Moving Average",
    },
    "RSI": {
        "params": ["period"],
        "sources": ["close"],
        "description": "Relative Strength Index",
    },
    "MACD": {
        "params": ["fast", "slow", "signal"],
        "sources": ["close"],
        "description": "Moving Average Convergence Divergence",
    },
    "BB": {
        "params": ["period", "dev"],
        "sources": ["close"],
        "description": "Bollinger Bands",
    },
    "ATR": {
        "params": ["period"],
        "sources": ["high", "low", "close"],
        "description": "Average True Range",
    },
}

# Generator templates (how to render indicators in different languages)
GENERATOR_TEMPLATES = {
    "python": {
        "SMA": "ta.sma({source}, {period})",
        "EMA": "ta.ema({source}, {period})",
        "RSI": "ta.rsi({source}, {period})",
        "MACD": "ta.macd({source}, {fast}, {slow}, {signal})",
    },
    "pine": {
        "SMA": "ta.sma({source}, {period})",
        "EMA": "ta.ema({source}, {period})",
        "RSI": "ta.rsi({source}, {period})",
        "MACD": "ta.macd({source}, {fast}, {slow}, {signal})",
    },
}


def get_indicator_template(target_lang: str, indicator_type: str) -> str:
    """Get code template for rendering an indicator in target language.
    
    Args:
        target_lang: 'python', 'pine', etc.
        indicator_type: 'SMA', 'EMA', 'RSI', etc.
        
    Returns:
        template string with {param} placeholders
    """
    target = target_lang.lower()
    ind_type = indicator_type.upper()
    
    if target not in GENERATOR_TEMPLATES:
        raise ValueError(f"No templates for language: {target}")
    
    if ind_type not in GENERATOR_TEMPLATES[target]:
        # Fallback: assume generic format
        return f"{{source}}.{{indicator_type}}.{{period}}"
    
    return GENERATOR_TEMPLATES[target][ind_type]


def is_indicator(name: str) -> bool:
    """Check if name is a known indicator."""
    return name.upper() in INDICATORS


__all__ = ["INDICATORS", "GENERATOR_TEMPLATES", "get_indicator_template", "is_indicator"]

