"""Parser registry: select parser by input language."""
from typing import Any


def get_parser(name_or_ext: str) -> Any:
    """Get parser module by name or file extension.
    
    Args:
        name_or_ext: parser name ('python', 'pine') or file extension ('.py', '.pine')
        
    Returns:
        parser module with parse(code: str) -> dict
    """
    ext = name_or_ext.lower().lstrip('.')
    
    if ext in ['py', 'python']:
        from src.parsers import python
        return python
    elif ext in ['pine', 'pinescript']:
        from src.parsers import pine
        return pine
    else:
        raise ValueError(f"Unknown parser: {name_or_ext}")


def get_parser_for_file(filepath: str) -> Any:
    """Get parser based on file extension."""
    if filepath.endswith('.py'):
        return get_parser('python')
    elif filepath.endswith('.pine'):
        return get_parser('pine')
    else:
        raise ValueError(f"Unknown file type: {filepath}")
