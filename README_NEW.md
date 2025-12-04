# Transplier - Trading Strategy Transpiler

A Python-based transpiler for converting trading strategies between different programming languages and platforms.

## Overview

Transplier allows you to convert trading algorithms between:
- Python
- TradingView Pine Script
- MQL4/MQL5 (coming soon)
- JavaScript (coming soon)
- Deriv Bot (coming soon)

The transpiler uses an Intermediate Representation (IR) format to maintain strategy logic integrity during conversion.

## Features

- 🔄 **Multi-language Support**: Convert between Python and Pine Script (more languages coming)
- 📊 **Common Indicators**: Built-in support for SMA, EMA, RSI, MACD, and more
- 🎯 **Position Sizing**: Multiple sizing methods (fixed, percentage, risk-based, Kelly criterion)
- ✅ **Validation**: Automatic validation of strategy structure and logic
- 🧪 **Well-tested**: Comprehensive test suite with 30+ passing tests
- 📚 **Extensible**: Easy to add support for new languages and indicators

## Installation

```bash
# Clone the repository
git clone https://github.com/xamie01/Transplier-program.git
cd Transplier-program

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

### Basic Usage

```python
from src.transpiler import Transpiler

# Create a transpiler instance
transpiler = Transpiler()

# Python to Pine Script
python_code = '''
STRATEGY_NAME = "SMA Crossover"
sma_20 = ta.SMA(close, 20)
sma_50 = ta.SMA(close, 50)

# Entry long
if sma_20 > sma_50:
    enter_long()
'''

pine_code = transpiler.transpile(python_code, 'python', 'pinescript')
print(pine_code)
```

### Using the High-Level Converter

```python
from src.converter import Converter

converter = Converter()

# Convert a file
output_path = converter.convert_file(
    'my_strategy.py',
    from_lang='python',
    to_lang='pinescript',
    output_file='my_strategy.pine'
)

# Convert to IR format
ir_dict = converter.convert_to_ir(python_code, 'python')

# Validate a strategy
is_valid = converter.validate_strategy(python_code, 'python')
```

## Project Structure

```
Transplier-program/
├── src/
│   ├── ir/              # Intermediate Representation
│   │   ├── schema.py    # IR data structures
│   │   └── validator.py # IR validation
│   ├── parsers/         # Language parsers
│   │   ├── python_parser.py
│   │   └── pinescript_parser.py
│   ├── generators/      # Code generators
│   │   ├── python_generator.py
│   │   └── pinescript_generator.py
│   ├── indicators/      # Technical indicators
│   │   ├── moving_averages.py
│   │   └── oscillators.py
│   ├── position/        # Position sizing
│   │   └── size.py
│   ├── conditions/      # Trading conditions
│   │   ├── entry.py
│   │   └── exit.py
│   ├── transpiler.py    # Main transpiler
│   ├── converter.py     # High-level API
│   └── config.py        # Configuration
├── tests/               # Test suite
├── examples/            # Example strategies
└── docs/                # Documentation
```

## Intermediate Representation (IR)

Transplier uses a JSON/YAML-based IR format to represent trading strategies in a language-agnostic way:

```python
{
    "name": "SMA Crossover",
    "version": "1.0.0",
    "timeframe": "1h",
    "indicators": [
        {
            "type": "sma",
            "name": "sma_20",
            "parameters": {"period": 20},
            "source": "close"
        }
    ],
    "entry_long": {
        "expression": "sma_20 > sma_50",
        "description": "Long entry condition"
    },
    "position_sizing": {
        "method": "fixed",
        "value": 1.0
    },
    "risk_management": {
        "stop_loss": 2.0,
        "take_profit": 4.0
    }
}
```

## Supported Indicators

- **Moving Averages**: SMA, EMA, WMA
- **Oscillators**: RSI, MACD, Stochastic
- **Volatility**: Bollinger Bands, ATR
- **Trend**: ADX, CCI, VWAP

## Position Sizing Methods

- **Fixed**: Fixed number of units
- **Percentage**: Percentage of account value
- **Risk-based**: Based on risk per trade and stop loss
- **Kelly Criterion**: Optimal bet sizing
- **Optimal F**: Ralph Vince's optimal f

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_transpiler.py -v
```

## Examples

See the `examples/` directory for complete strategy implementations:

- `simple_sma_crossover.py` - Python implementation
- `simple_sma_crossover.pine` - Pine Script implementation

## Security Considerations

⚠️ **Important**: The transpiler uses `eval()` for condition evaluation with restricted builtins. Only use with trusted code. Do not evaluate user-provided expressions without proper validation and sandboxing.

## Roadmap

### Phase 1: MVP (Current)
- [x] Python ↔ Pine Script conversion
- [x] Core IR system
- [x] Basic indicators (SMA, EMA, RSI, MACD)
- [x] Position sizing
- [x] Test suite

### Phase 2: Expansion (Next)
- [ ] MQL4/MQL5 support
- [ ] JavaScript support
- [ ] More indicators
- [ ] Risk management features
- [ ] Web interface

### Phase 3: AI Enhancement
- [ ] LLM integration for complex patterns
- [ ] Validation assistant
- [ ] Documentation generation
- [ ] Strategy optimization suggestions

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Adding a New Language

1. Create a parser in `src/parsers/`
2. Create a generator in `src/generators/`
3. Add tests in `tests/`
4. Update documentation

## License

MIT License - see LICENSE file for details

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/xamie01/Transplier-program/issues)
- Documentation: See `docs/` directory

## Acknowledgments

Built to help traders port their strategies across different platforms and languages, enabling cross-platform strategy testing and deployment.

---

**Note**: This project is under active development. The API may change in future versions.
