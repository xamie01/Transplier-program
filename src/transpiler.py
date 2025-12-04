"""
Main Transpiler class.

This module provides the main Transpiler class that orchestrates the conversion
of trading strategies between different programming languages.
"""

from typing import Optional
from pathlib import Path

from src.ir.schema import StrategyIR
from src.ir.validator import IRValidator, ValidationError
from src.parsers.base_parser import BaseParser
from src.parsers.python_parser import PythonParser
from src.parsers.pinescript_parser import PineScriptParser
from src.generators.base_generator import BaseGenerator
from src.generators.python_generator import PythonGenerator
from src.generators.pinescript_generator import PineScriptGenerator
from src.config import get_config
from src.utils.helpers import save_json, save_yaml


class TranspilerError(Exception):
    """Raised when transpilation fails."""
    pass


class Transpiler:
    """
    Main transpiler class for converting trading strategies.
    
    This class handles the complete pipeline:
    1. Parse source code to IR
    2. Validate IR
    3. Generate target code from IR
    """
    
    def __init__(self, config=None):
        """
        Initialize the transpiler.
        
        Args:
            config: Optional configuration object
        """
        self.config = config or get_config()
        self.parsers = {
            'python': PythonParser(),
            'pinescript': PineScriptParser(),
            'pine': PineScriptParser(),
        }
        self.generators = {
            'python': PythonGenerator(),
            'pinescript': PineScriptGenerator(),
            'pine': PineScriptGenerator(),
        }
        self.validator = IRValidator()
    
    def transpile(self, 
                  source_code: str, 
                  source_language: str, 
                  target_language: str,
                  validate: bool = True) -> str:
        """
        Transpile code from source language to target language.
        
        Args:
            source_code: Source code to transpile
            source_language: Source programming language
            target_language: Target programming language
            validate: Whether to validate IR (default: True)
            
        Returns:
            Generated code in target language
            
        Raises:
            TranspilerError: If transpilation fails
        """
        # Step 1: Parse source code to IR
        try:
            strategy_ir = self.parse(source_code, source_language)
        except Exception as e:
            raise TranspilerError(f"Failed to parse {source_language} code: {e}")
        
        # Step 2: Validate IR
        if validate:
            try:
                warnings = self.validator.validate_strategy(strategy_ir)
                if warnings:
                    print(f"Validation warnings: {warnings}")
            except ValidationError as e:
                raise TranspilerError(f"IR validation failed: {e}")
        
        # Step 3: Generate target code
        try:
            target_code = self.generate(strategy_ir, target_language)
        except Exception as e:
            raise TranspilerError(f"Failed to generate {target_language} code: {e}")
        
        return target_code
    
    def parse(self, source_code: str, language: str) -> StrategyIR:
        """
        Parse source code to IR.
        
        Args:
            source_code: Source code to parse
            language: Programming language
            
        Returns:
            StrategyIR object
            
        Raises:
            TranspilerError: If parsing fails
        """
        language_key = language.lower()
        
        if language_key not in self.parsers:
            raise TranspilerError(f"Unsupported source language: {language}")
        
        parser = self.parsers[language_key]
        return parser.parse(source_code)
    
    def generate(self, strategy_ir: StrategyIR, language: str) -> str:
        """
        Generate code from IR.
        
        Args:
            strategy_ir: Strategy intermediate representation
            language: Target programming language
            
        Returns:
            Generated code
            
        Raises:
            TranspilerError: If generation fails
        """
        language_key = language.lower()
        
        if language_key not in self.generators:
            raise TranspilerError(f"Unsupported target language: {language}")
        
        generator = self.generators[language_key]
        return generator.generate(strategy_ir)
    
    def transpile_file(self,
                      input_path: str,
                      source_language: str,
                      target_language: str,
                      output_path: Optional[str] = None) -> str:
        """
        Transpile a file from source to target language.
        
        Args:
            input_path: Path to input file
            source_language: Source programming language
            target_language: Target programming language
            output_path: Optional output path (auto-generated if not provided)
            
        Returns:
            Path to output file
            
        Raises:
            TranspilerError: If transpilation fails
        """
        # Read source file
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception as e:
            raise TranspilerError(f"Failed to read input file: {e}")
        
        # Transpile
        target_code = self.transpile(source_code, source_language, target_language)
        
        # Determine output path
        if output_path is None:
            from src.utils.helpers import get_file_extension
            input_file = Path(input_path)
            ext = get_file_extension(target_language)
            output_path = self.config.get_output_path(f"{input_file.stem}{ext}")
        
        # Write output file
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(target_code)
        except Exception as e:
            raise TranspilerError(f"Failed to write output file: {e}")
        
        return output_path
    
    def export_ir(self, 
                  source_code: str, 
                  source_language: str,
                  output_path: str,
                  format: str = 'json') -> str:
        """
        Export IR to file.
        
        Args:
            source_code: Source code to parse
            source_language: Source programming language
            output_path: Path to output file
            format: Output format ('json' or 'yaml')
            
        Returns:
            Path to output file
            
        Raises:
            TranspilerError: If export fails
        """
        # Parse to IR
        strategy_ir = self.parse(source_code, source_language)
        
        # Convert to dictionary
        ir_dict = strategy_ir.to_dict()
        
        # Save to file
        try:
            if format.lower() == 'json':
                save_json(ir_dict, output_path)
            elif format.lower() in ['yaml', 'yml']:
                save_yaml(ir_dict, output_path)
            else:
                raise TranspilerError(f"Unsupported export format: {format}")
        except Exception as e:
            raise TranspilerError(f"Failed to export IR: {e}")
        
        return output_path
    
    def import_ir(self, ir_path: str, target_language: str) -> str:
        """
        Import IR from file and generate target code.
        
        Args:
            ir_path: Path to IR file (JSON or YAML)
            target_language: Target programming language
            
        Returns:
            Generated code
            
        Raises:
            TranspilerError: If import fails
        """
        from src.utils.helpers import load_json, load_yaml
        
        # Load IR
        try:
            path = Path(ir_path)
            if path.suffix == '.json':
                ir_dict = load_json(ir_path)
            elif path.suffix in ['.yaml', '.yml']:
                ir_dict = load_yaml(ir_path)
            else:
                raise TranspilerError(f"Unsupported IR file format: {path.suffix}")
        except Exception as e:
            raise TranspilerError(f"Failed to load IR file: {e}")
        
        # Convert to StrategyIR
        try:
            strategy_ir = StrategyIR.from_dict(ir_dict)
        except Exception as e:
            raise TranspilerError(f"Failed to parse IR data: {e}")
        
        # Generate code
        return self.generate(strategy_ir, target_language)
    
    def add_parser(self, language: str, parser: BaseParser):
        """
        Add a custom parser for a language.
        
        Args:
            language: Language name
            parser: Parser instance
        """
        self.parsers[language.lower()] = parser
    
    def add_generator(self, language: str, generator: BaseGenerator):
        """
        Add a custom generator for a language.
        
        Args:
            language: Language name
            generator: Generator instance
        """
        self.generators[language.lower()] = generator
