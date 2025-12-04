"""
Converter module.

This module provides a high-level API for converting trading strategies
between different formats and languages.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from src.transpiler import Transpiler, TranspilerError
from src.ir.schema import StrategyIR
from src.utils.helpers import load_json, load_yaml, save_json, save_yaml


class ConverterError(Exception):
    """Raised when conversion fails."""
    pass


class Converter:
    """
    High-level converter for trading strategies.
    
    This class provides a simple interface for converting strategies
    between different languages and formats.
    """
    
    def __init__(self):
        """Initialize the converter."""
        self.transpiler = Transpiler()
    
    def convert(self,
                source: str,
                from_lang: str,
                to_lang: str,
                output_file: Optional[str] = None) -> str:
        """
        Convert a trading strategy between languages.
        
        Args:
            source: Source code string or path to source file
            from_lang: Source language (python, pinescript, etc.)
            to_lang: Target language
            output_file: Optional output file path
            
        Returns:
            Converted code string
            
        Raises:
            ConverterError: If conversion fails
        """
        try:
            # Check if source is a file path (must not contain newlines and be reasonably short)
            if '\n' not in source and len(source) < 500:
                source_path = Path(source)
                if source_path.exists() and source_path.is_file():
                    with open(source, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                else:
                    source_code = source
            else:
                source_code = source
            
            # Transpile
            result = self.transpiler.transpile(source_code, from_lang, to_lang)
            
            # Save to file if requested
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
            
            return result
            
        except TranspilerError as e:
            raise ConverterError(f"Conversion failed: {e}")
        except Exception as e:
            raise ConverterError(f"Unexpected error during conversion: {e}")
    
    def convert_file(self,
                    input_file: str,
                    from_lang: str,
                    to_lang: str,
                    output_file: Optional[str] = None) -> str:
        """
        Convert a file from one language to another.
        
        Args:
            input_file: Path to input file
            from_lang: Source language
            to_lang: Target language
            output_file: Optional output file path
            
        Returns:
            Path to output file
            
        Raises:
            ConverterError: If conversion fails
        """
        try:
            return self.transpiler.transpile_file(
                input_file, from_lang, to_lang, output_file
            )
        except TranspilerError as e:
            raise ConverterError(f"File conversion failed: {e}")
    
    def convert_to_ir(self,
                     source: str,
                     from_lang: str,
                     output_format: str = 'json') -> Dict[str, Any]:
        """
        Convert source code to intermediate representation.
        
        Args:
            source: Source code string or file path
            from_lang: Source language
            output_format: Format for output ('json' or 'dict')
            
        Returns:
            IR as dictionary
            
        Raises:
            ConverterError: If conversion fails
        """
        try:
            # Check if source is a file (must not contain newlines and be reasonably short)
            if '\n' not in source and len(source) < 500:
                source_path = Path(source)
                if source_path.exists() and source_path.is_file():
                    with open(source, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                else:
                    source_code = source
            else:
                source_code = source
            
            # Parse to IR
            strategy_ir = self.transpiler.parse(source_code, from_lang)
            
            # Return as dictionary
            return strategy_ir.to_dict()
            
        except TranspilerError as e:
            raise ConverterError(f"Conversion to IR failed: {e}")
    
    def convert_from_ir(self,
                       ir_data: Dict[str, Any],
                       to_lang: str) -> str:
        """
        Convert IR to target language.
        
        Args:
            ir_data: IR dictionary
            to_lang: Target language
            
        Returns:
            Generated code
            
        Raises:
            ConverterError: If conversion fails
        """
        try:
            # Convert dict to StrategyIR
            strategy_ir = StrategyIR.from_dict(ir_data)
            
            # Generate code
            return self.transpiler.generate(strategy_ir, to_lang)
            
        except Exception as e:
            raise ConverterError(f"Conversion from IR failed: {e}")
    
    def batch_convert(self,
                     input_files: list,
                     from_lang: str,
                     to_lang: str,
                     output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Convert multiple files.
        
        Args:
            input_files: List of input file paths
            from_lang: Source language
            to_lang: Target language
            output_dir: Optional output directory
            
        Returns:
            Dictionary mapping input files to output files
            
        Raises:
            ConverterError: If any conversion fails
        """
        results = {}
        errors = []
        
        for input_file in input_files:
            try:
                # Determine output path
                if output_dir:
                    from src.utils.helpers import get_file_extension
                    input_path = Path(input_file)
                    ext = get_file_extension(to_lang)
                    output_file = str(Path(output_dir) / f"{input_path.stem}{ext}")
                else:
                    output_file = None
                
                # Convert
                output_path = self.convert_file(
                    input_file, from_lang, to_lang, output_file
                )
                results[input_file] = output_path
                
            except ConverterError as e:
                errors.append(f"{input_file}: {e}")
        
        if errors:
            raise ConverterError(f"Batch conversion had errors: {'; '.join(errors)}")
        
        return results
    
    def validate_strategy(self, source: str, from_lang: str) -> bool:
        """
        Validate a trading strategy.
        
        Args:
            source: Source code or file path
            from_lang: Source language
            
        Returns:
            True if valid
            
        Raises:
            ConverterError: If validation fails
        """
        try:
            # Check if source is a file (must not contain newlines and be reasonably short)
            if '\n' not in source and len(source) < 500:
                source_path = Path(source)
                if source_path.exists() and source_path.is_file():
                    with open(source, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                else:
                    source_code = source
            else:
                source_code = source
            
            # Parse and validate
            strategy_ir = self.transpiler.parse(source_code, from_lang)
            warnings = self.transpiler.validator.validate_strategy(strategy_ir)
            
            if warnings:
                print(f"Validation warnings: {warnings}")
            
            return True
            
        except Exception as e:
            raise ConverterError(f"Validation failed: {e}")
    
    def get_supported_languages(self) -> list:
        """
        Get list of supported languages.
        
        Returns:
            List of supported language names
        """
        return list(set(
            list(self.transpiler.parsers.keys()) + 
            list(self.transpiler.generators.keys())
        ))
