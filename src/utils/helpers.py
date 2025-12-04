"""
Utility helper functions.

This module provides common utility functions for file I/O,
data conversion, and other helper operations.
"""

import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Dictionary with JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], filepath: str, indent: int = 2) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Dictionary to save
        filepath: Path to save file
        indent: JSON indentation level
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_yaml(filepath: str) -> Dict[str, Any]:
    """
    Load YAML file.
    
    Args:
        filepath: Path to YAML file
        
    Returns:
        Dictionary with YAML data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If file is not valid YAML
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict[str, Any], filepath: str) -> None:
    """
    Save data to YAML file.
    
    Args:
        data: Dictionary to save
        filepath: Path to save file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def format_code(code: str, language: str = "python") -> str:
    """
    Format code string.
    
    Args:
        code: Code string to format
        language: Programming language
        
    Returns:
        Formatted code string
    """
    # Basic formatting - remove excessive blank lines
    lines = code.split('\n')
    formatted_lines = []
    blank_count = 0
    
    for line in lines:
        if line.strip():
            formatted_lines.append(line)
            blank_count = 0
        else:
            blank_count += 1
            if blank_count <= 2:  # Allow max 2 consecutive blank lines
                formatted_lines.append(line)
    
    return '\n'.join(formatted_lines).strip() + '\n'


def validate_file_path(filepath: str, extensions: Optional[list] = None) -> bool:
    """
    Validate file path and extension.
    
    Args:
        filepath: Path to validate
        extensions: List of valid extensions (e.g., ['.py', '.pine'])
        
    Returns:
        True if valid
    """
    path = Path(filepath)
    
    if not path.parent.exists():
        return False
    
    if extensions:
        return path.suffix in extensions
    
    return True


def get_file_extension(language: str) -> str:
    """
    Get file extension for a programming language.
    
    Args:
        language: Language name
        
    Returns:
        File extension
    """
    extensions = {
        'python': '.py',
        'pinescript': '.pine',
        'pine': '.pine',
        'mql4': '.mq4',
        'mql5': '.mq5',
        'javascript': '.js',
        'js': '.js',
    }
    return extensions.get(language.lower(), '.txt')


def extract_code_blocks(text: str, language: Optional[str] = None) -> list:
    """
    Extract code blocks from markdown text.
    
    Args:
        text: Markdown text
        language: Optional language filter
        
    Returns:
        List of code blocks
    """
    import re
    
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.finditer(pattern, text, re.DOTALL)
    
    code_blocks = []
    for match in matches:
        block_lang = match.group(1)
        code = match.group(2)
        
        if language is None or (block_lang and block_lang.lower() == language.lower()):
            code_blocks.append({
                'language': block_lang,
                'code': code.strip()
            })
    
    return code_blocks


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        name: String to sanitize
        
    Returns:
        Sanitized filename
    """
    import re
    
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Remove leading/trailing periods and spaces
    sanitized = sanitized.strip('. ')
    
    # Limit length
    max_length = 255
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized or 'unnamed'
