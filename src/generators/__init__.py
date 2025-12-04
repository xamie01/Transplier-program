"""Generator registry: select generator by target language."""
from typing import Any


def get_generator(name: str) -> Any:
    """Get generator module by target language name.
    
    Args:
        name: target language ('python', 'pine', 'pinescript')
        
    Returns:
        generator module with generate(ir: dict) -> str
    """
    name_lower = name.lower()
    
    if name_lower in ['py', 'python']:
        from src.generators import python
        return python
    elif name_lower in ['pine', 'pinescript']:
        from src.generators import pine
        return pine
    else:
        raise ValueError(f"Unknown generator: {name}")
