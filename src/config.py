"""
Configuration module for Transplier.

This module handles configuration settings for the transpiler.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import os


class Config:
    """Configuration manager for Transplier."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        'output_dir': './output',
        'cache_dir': './cache',
        'default_timeframe': '1h',
        'enable_validation': True,
        'enable_optimization': False,
        'log_level': 'INFO',
        'supported_languages': ['python', 'pinescript', 'mql4', 'mql5', 'javascript'],
        'parser_options': {
            'strict_mode': False,
            'extract_comments': True,
        },
        'generator_options': {
            'add_comments': True,
            'format_code': True,
        }
    }
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration.
        
        Args:
            config_dict: Optional configuration dictionary
        """
        self.config = self.DEFAULT_CONFIG.copy()
        if config_dict:
            self.config.update(config_dict)
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        for key in ['output_dir', 'cache_dir']:
            if key in self.config:
                Path(self.config[key]).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
        
        # Create directory if it's a path setting
        if key in ['output_dir', 'cache_dir']:
            Path(value).mkdir(parents=True, exist_ok=True)
    
    def update(self, config_dict: Dict[str, Any]):
        """
        Update configuration with multiple values.
        
        Args:
            config_dict: Dictionary with configuration updates
        """
        self.config.update(config_dict)
        self._ensure_directories()
    
    def get_output_path(self, filename: str) -> str:
        """
        Get full output path for a file.
        
        Args:
            filename: Output filename
            
        Returns:
            Full path to output file
        """
        output_dir = Path(self.config['output_dir'])
        return str(output_dir / filename)
    
    def get_cache_path(self, filename: str) -> str:
        """
        Get full cache path for a file.
        
        Args:
            filename: Cache filename
            
        Returns:
            Full path to cache file
        """
        cache_dir = Path(self.config['cache_dir'])
        return str(cache_dir / filename)
    
    def is_language_supported(self, language: str) -> bool:
        """
        Check if a language is supported.
        
        Args:
            language: Language name
            
        Returns:
            True if supported
        """
        supported = self.config.get('supported_languages', [])
        return language.lower() in [lang.lower() for lang in supported]
    
    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        """
        Load configuration from file.
        
        Args:
            filepath: Path to configuration file (JSON or YAML)
            
        Returns:
            Config instance
        """
        from src.utils.helpers import load_json, load_yaml
        
        path = Path(filepath)
        if path.suffix in ['.json']:
            config_dict = load_json(filepath)
        elif path.suffix in ['.yaml', '.yml']:
            config_dict = load_yaml(filepath)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")
        
        return cls(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()


# Global configuration instance
_global_config = Config()


def get_config() -> Config:
    """
    Get global configuration instance.
    
    Returns:
        Config instance
    """
    return _global_config


def set_config(config: Config):
    """
    Set global configuration instance.
    
    Args:
        config: Config instance to set as global
    """
    global _global_config
    _global_config = config
