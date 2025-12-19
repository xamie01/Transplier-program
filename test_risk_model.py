#!/usr/bin/env python3
"""
Quick sync test of new risk model on cached data
"""
import sys
from pathlib import Path
import pandas as pd
import logging

sys.path.insert(0, str(Path(__file__).parent))

from src.backtesting import Backtester
from src.strategies import FourierStrategy

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Try to load cached data
csv_file = 'data/R_100_candles_3600s_60d.csv'
if not Path(csv_file).exists():
    logger.info(f"Cache {csv_file} not found. Run: python backtest.py --symbol R_100 --interval 3600 --days 60 --download-only")
    sys.exit(1)

logger.info(f"Loading {csv_file}...")
df = pd.read_csv(csv_file)
if 'time' not in df.columns:
    df['time'] = (pd.to_datetime(df['datetime']).astype('int64') // 1_000_000_000).astype(int)

logger.info(f"Loaded {len(df)} candles\n")

# Fixed params
stake = 30.0
initial_balance = 1000.0
lookback, forecast, atr_mult = 150, 20, 0.5

# Quick test grid
risk_factors = [0.5]  # Start with mid-range
rr_ratios = [3.0]

results = []
for rf in risk_factors:
    for rr in rr_ratios:
        params = {
            'lookback': lookback,
            'forecast': forecast,
            'atr_multiplier': atr_mult,
            'stake': stake,
            'risk_cash': stake * rf,
            'rr_ratio': rr,
        }
        
        strategy = FourierStrategy(params=params)
        backtester = Backtester(strategy=strategy, initial_balance=initial_balance, stake_per_trade=stake)
        result = backtester.run(df)
        
        if result.trades:
            wins_sum = sum(t.pnl for t in result.trades if t.pnl and t.pnl > 0)
            losses_sum = abs(sum(t.pnl for t in result.trades if t.pnl and t.pnl < 0))
            pf = wins_sum / losses_sum if losses_sum > 0 else (float('inf') if wins_sum > 0 else 0)
        else:
            pf = 0
        
        logger.info(f"RISKx={rf} RR={rr}: Trades={result.total_trades} WR={result.win_rate:.1f}% PnL=${result.total_pnl:.2f} PF={pf:.2f}")

logger.info("\nDone!")
