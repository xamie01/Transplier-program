# Transpiler Program + Fourier Trading Strategy Optimizer

## Project Overview

This workspace combines two main components:

1. **Trading Strategy Transpiler** - Convert strategies between Pine Script, Python, MQL4/5, and Deriv formats
2. **Fourier Strategy Optimizer** - Optimize a Fourier-based trading strategy for profitability on Deriv synthetic indices

## Quick Start: Strategy Optimization

### Goal
Achieve **profit factor > 1.8** with **< 20% drawdown** through cash-based risk/reward tuning.

### TL;DR - Fastest Path to Results

```bash
# 1. Quick parameter sweep (creates param_optimizer_results_*.csv)
python quick_optimization.py

# 2. Analyze which risk/RR configs passed success criteria
python analyze_sweep_results.py

# 3. Pick top 3 configs and validate with rolling test windows
python tools/walk_forward_test.py --symbol R_100 --days 90 --risk-factor 0.5 --rr-ratio 3.0

# 4. Repeat step 3 for R_50, R_75 and compare results
# Then lock in best config across all symbols
```

### Full Documentation
See [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) for complete walkthrough.

---

## Component 1: Fourier Strategy

### Architecture

**Signal Generation** (Fourier-based harmonic prediction):
1. Smooth prices with weighted MA (period=11)
2. Detect dominant cycle period via max/min distance
3. Calculate amplitude, phase, midpoint
4. Project future price using: `midpoint + amplitude × cos(2π × freq × forecast + phase)`
5. Trade when price deviates from prediction in ranging markets

**Risk Model** (Cash-based, not percentage):
- Risk per trade: `risk_cash = stake × risk_factor`
- Stop loss: `entry - risk_price_move`
- Take profit: `entry + (risk_price_move × rr_ratio)`
- Where: `risk_price_move = (risk_cash / stake) × entry_price`

**Position Sizing** (Notional):
- Quantity: `stake / entry_price`
- PnL: `(exit_price - entry_price) × quantity`

**Exit Logic** (Primary + Safety):
- Primary: Prediction cross (mean reversion)
- Safety: Hard stop/take profit at cash-based levels

### Key Features
- ✅ Multi-timeframe confirmation (4h trend gate)
- ✅ ATR-based entry filter
- ✅ Ranging-market detection
- ✅ Notional position sizing for consistent risk

### Files
- Strategy: [src/strategies/fourier_strategy.py](src/strategies/fourier_strategy.py)
- Backtester: [src/backtesting/backtester.py](src/backtesting/backtester.py)
- Data: [src/deriv_api/data_downloader.py](src/deriv_api/data_downloader.py)

---

## Tools for Optimization

### Parameter Optimizer
```bash
python tools/param_optimizer.py \
  --symbol R_100 \
  --interval 3600 \
  --days 60 \
  --stake 30 \
  --risk-factors "0.25,0.5,0.75" \
  --rr-list "2,3,4"
```
- Tests 9 risk/RR combinations
- Saves CSV with metrics: PF, WR, DD, Sharpe, etc.
- Logs top 10 configs

### Walk-Forward Tester
```bash
python tools/walk_forward_test.py \
  --symbol R_100 \
  --interval 3600 \
  --days 90 \
  --train-days 21 \
  --test-days 7 \
  --risk-factor 0.5 \
  --rr-ratio 3.0
```
- Rolling train/test validation (out-of-sample)
- Detects overfitting
- Estimates real-world performance

### Backtest Runner
```bash
python backtest.py \
  --symbol R_100 \
  --interval 3600 \
  --days 30 \
  --stake 30 \
  --risk-factor 0.5 \
  --rr-ratio 3.0
```
- Single backtest run
- Exports trade-by-trade CSV
- Cache-first (reuses downloaded data)

---

## Expected Performance Targets

After optimization, expect:
- **Profit Factor**: > 1.8 (wins 80%+ more than losses)
- **Win Rate**: > 45% (more winning trades than losing)
- **Max Drawdown**: < 20% (controlled worst-case loss)
- **Trade Frequency**: 10-20 trades per 60 days (manageable)

---

## Data & Caching

- **Source**: Deriv WebSocket API (requires auth)
- **Cached in**: `data/{symbol}_candles_{interval}s_{days}d.csv`
- **Cache-first**: Faster reruns, offline testing
- **Auto-download**: If cache missing

---

## Component 2: Strategy Transpiler

*(Documentation to follow in separate section)*

Key files:
- [src/ir/ir.py](src/ir/ir.py) - Intermediate representation
- [src/parsers/](src/parsers/) - Language parsers
- [src/generators/](src/generators/) - Code generators

---

## Project Structure

```
.
├── backtest.py                          # Main backtest runner
├── quick_optimization.py                # One-command sweep
├── analyze_sweep_results.py             # Parse optimizer CSVs
├── aggregate_walkforward_results.py     # Summarize walk-forward
├── run_full_optimization.py             # Batch runner (all symbols)
├── OPTIMIZATION_GUIDE.md                # Complete optimization walkthrough
├── OPTIMIZATION_PLAN_EXECUTION.md       # Implementation checklist
│
├── src/
│   ├── backtesting/
│   │   └── backtester.py               # Notional sizing, PnL tracking
│   ├── deriv_api/
│   │   ├── client.py                   # WS async client
│   │   ├── engine.py                   # Trading engine
│   │   ├── data_downloader.py          # Candle downloader + cache
│   │   └── strategy_interface.py       # Base strategy class
│   ├── strategies/
│   │   └── fourier_strategy.py         # Fourier predictor + risk model
│   ├── ir/                             # Intermediate representation
│   ├── parsers/                        # Language parsers
│   └── generators/                     # Code generators
│
├── tools/
│   ├── param_optimizer.py              # Grid sweep over risk/RR
│   └── walk_forward_test.py            # OOS rolling validation
│
├── data/                               # Cached candles (auto-created)
├── tests/                              # Unit tests
└── requirements.txt                    # Dependencies
```

---

## Getting Started

### 1. Install & Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Quick Optimization
```bash
python quick_optimization.py
```

### 3. Analyze Results
```bash
python analyze_sweep_results.py
```

### 4. Validate with Walk-Forward
```bash
# Pick best config from step 3, then:
python tools/walk_forward_test.py \
  --symbol R_100 \
  --days 90 \
  --risk-factor 0.5 \
  --rr-ratio 3.0
```

### 5. Compare Across Symbols
Repeat step 4 for R_50 and R_75, compare metrics, lock in final config.

---

## Key Innovations

1. **Cash-Based Risk Model**: Fixed dollar risk per trade, not percentage
2. **Notional Sizing**: Consistent risk across price levels
3. **Multi-Symbol Validation**: Robustness across different volatility regimes
4. **Walk-Forward Testing**: Out-of-sample performance estimation

---

## References

- Strategy Papers: [Fourier Analysis in Trading](https://en.wikipedia.org/wiki/Fourier_analysis)
- Deriv API: [WebSocket Documentation](https://api.deriv.com/)
- Backtesting: [Walk-Forward Analysis](https://en.wikipedia.org/wiki/Walk_forward_optimization)

---

## License

[Your License Here]

---

## Next Steps

- [ ] Run optimization and lock in best config
- [ ] Paper trade on Deriv demo for 7-14 days
- [ ] Compare live execution vs backtest results
- [ ] Deploy to live trading (if validated)
- [ ] Monitor and revalidate every 30 days

Good luck! 🚀
