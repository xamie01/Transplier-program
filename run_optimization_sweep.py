#!/usr/bin/env python3
"""
Optimization sweep runner focusing on risk+RR parameters
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.deriv_api.data_downloader import DerivDataDownloader
from src.backtesting import Backtester
from src.strategies import FourierStrategy
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_sweep():
    """Run focused sweep on R_100 with risk/RR tuning"""
    # Download data
    logger.info("Downloading R_100 1h data (60 days)...")
    downloader = DerivDataDownloader()
    try:
        await downloader.connect()
        df = await downloader.download_candles(
            symbol='R_100',
            interval=3600,
            days_back=60,
            use_cache=True,
            force_refresh=False,
        )
    finally:
        await downloader.disconnect()
    
    logger.info(f"Loaded {len(df)} candles")
    
    # Fixed params (from previous testing)
    lookback = 150
    forecast = 20
    atr_mult = 0.5
    stake = 30.0
    initial_balance = 1000.0
    
    # Vary risk and RR
    risk_factors = [0.25, 0.5, 0.75]
    rr_ratios = [2.0, 3.0, 4.0]
    
    results = []
    total = len(risk_factors) * len(rr_ratios)
    count = 0
    
    logger.info(f"\nTesting {total} risk/RR combinations...")
    logger.info("=" * 80)
    
    for risk_factor in risk_factors:
        for rr_ratio in rr_ratios:
            count += 1
            
            params = {
                'lookback': lookback,
                'forecast': forecast,
                'atr_multiplier': atr_mult,
                'stake': stake,
                'risk_cash': stake * risk_factor,
                'rr_ratio': rr_ratio,
            }
            
            strategy = FourierStrategy(params=params)
            backtester = Backtester(strategy=strategy, initial_balance=initial_balance, stake_per_trade=stake)
            result = backtester.run(df)
            
            # Compute metrics
            if result.trades:
                pnls = [t.pnl for t in result.trades if t.pnl is not None]
                wins_sum = sum(t.pnl for t in result.trades if t.pnl and t.pnl > 0)
                losses_sum = abs(sum(t.pnl for t in result.trades if t.pnl and t.pnl < 0))
                pf = wins_sum / losses_sum if losses_sum > 0 else (float('inf') if wins_sum > 0 else 0)
            else:
                pf = 0
            
            results.append({
                'risk_factor': risk_factor,
                'rr_ratio': rr_ratio,
                'trades': result.total_trades,
                'win_rate': result.win_rate,
                'total_pnl': result.total_pnl,
                'avg_pnl': result.avg_pnl_per_trade,
                'profit_factor': pf,
                'max_drawdown': result.max_drawdown,
                'final_balance': initial_balance + result.total_pnl,
            })
            
            logger.info(
                f"[{count}/{total}] RISKx={risk_factor:.2f} RR={rr_ratio:.1f} | "
                f"Trades={result.total_trades} WR={result.win_rate:.1f}% "
                f"PnL=${result.total_pnl:.2f} PF={pf:.2f} DD={result.max_drawdown:.2f}%"
            )
    
    # Sort by profit factor
    df_results = pd.DataFrame(results).sort_values(by=['profit_factor', 'win_rate'], ascending=[False, False])
    
    logger.info("\n" + "=" * 80)
    logger.info("TOP RESULTS (sorted by Profit Factor)")
    logger.info("=" * 80)
    for idx, row in df_results.iterrows():
        logger.info(
            f"RISKx={row['risk_factor']:.2f} RR={row['rr_ratio']:.1f} | "
            f"WR={row['win_rate']:.1f}% PnL=${row['total_pnl']:.2f} "
            f"PF={row['profit_factor']:.2f} DD={row['max_drawdown']:.2f}%"
        )
    
    # Save
    csv_path = 'sweep_results_R100_1h.csv'
    df_results.to_csv(csv_path, index=False)
    logger.info(f"\nResults saved to {csv_path}")
    
    return df_results

if __name__ == '__main__':
    asyncio.run(run_sweep())
