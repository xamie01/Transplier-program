#!/usr/bin/env python3
"""
Parameter Optimizer
Sweep strategy parameters across a grid and identify best performers
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path
from itertools import product
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.deriv_api.data_downloader import DerivDataDownloader
from src.backtesting import Backtester
from src.strategies import FourierStrategy


def setup_logging(level: str = 'INFO'):
    """Setup logging"""
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('param_optimizer.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def optimize_parameters():
    parser = argparse.ArgumentParser(description='Fourier Strategy Parameter Optimizer')
    parser.add_argument('--symbol', type=str, default='R_100',
                       help='Trading symbol (R_100, R_75, etc.)')
    parser.add_argument('--interval', type=int, default=3600,
                       help='Candle interval in seconds (3600=1h)')
    parser.add_argument('--days', type=int, default=14,
                       help='Days of historical data')
    parser.add_argument('--stake', type=float, default=30.0,
                       help='Stake per trade')
    parser.add_argument('--risk-factors', type=str, default='0.5',
                       help='Comma-separated cash risk factors relative to stake (e.g., 0.25,0.5,0.75)')
    parser.add_argument('--rr-list', type=str, default='3',
                       help='Comma-separated risk-reward ratios to test (e.g., 2,3,4)')
    parser.add_argument('--initial-balance', type=float, default=1000.0,
                       help='Initial account balance')
    
    args = parser.parse_args()
    
    setup_logging('INFO')
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("Fourier Strategy Parameter Optimizer")
    logger.info("=" * 80)
    
    # Download or load data
    logger.info(f"Loading data for {args.symbol}...")
    downloader = DerivDataDownloader()
    try:
        await downloader.connect()
        df = await downloader.download_candles(
            symbol=args.symbol,
            interval=args.interval,
            days_back=args.days,
            use_cache=True,
            force_refresh=False,
        )
    finally:
        await downloader.disconnect()
    
    logger.info(f"Loaded {len(df)} candles")
    logger.info(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    
    # Parameter grid
    lookbacks = [20, 50, 100, 150]
    forecasts = [5, 10, 20]
    atr_multipliers = [0.2, 0.5, 1.0, 1.5]
    risk_factors = [float(x) for x in args.risk_factors.split(',') if x]
    rr_list = [float(x) for x in args.rr_list.split(',') if x]
    
    results = []
    total_combos = len(lookbacks) * len(forecasts) * len(atr_multipliers) * len(risk_factors) * len(rr_list)
    combo_num = 0
    
    logger.info(f"\nStarting sweep: {total_combos} parameter combinations")
    logger.info("=" * 80)
    
    for lookback, forecast, atr_mult, risk_factor, rr_ratio in product(lookbacks, forecasts, atr_multipliers, risk_factors, rr_list):
        combo_num += 1
        
        # Create strategy with these params
        params = {
            'lookback': lookback,
            'forecast': forecast,
            'atr_multiplier': atr_mult,
            'stake': args.stake,
            'risk_cash': args.stake * risk_factor,
            'rr_ratio': rr_ratio,
        }
        strategy = FourierStrategy(params=params)
        
        # Run backtest
        backtester = Backtester(
            strategy=strategy,
            initial_balance=args.initial_balance,
            stake_per_trade=args.stake,
        )
        
        result = backtester.run(df)
        
        # Compute Sharpe ratio (simple: mean PnL / std PnL)
        if result.trades:
            pnls = [t.pnl for t in result.trades if t.pnl is not None]
            sharpe = (sum(pnls) / len(pnls)) / (pd.Series(pnls).std() + 1e-6) if len(pnls) > 1 else 0
        else:
            sharpe = 0
        
        # Compute profit factor (wins / abs(losses))
        wins_sum = sum(t.pnl for t in result.trades if t.pnl and t.pnl > 0)
        losses_sum = abs(sum(t.pnl for t in result.trades if t.pnl and t.pnl < 0))
        profit_factor = wins_sum / losses_sum if losses_sum > 0 else 0
        
        # Store result
        result_dict = {
            'lookback': lookback,
            'forecast': forecast,
            'atr_multiplier': atr_mult,
            'trades': result.total_trades,
            'win_rate': result.win_rate,
            'total_pnl': result.total_pnl,
            'avg_pnl': result.avg_pnl_per_trade,
            'max_profit': result.max_profit,
            'max_loss': result.max_loss,
            'sharpe': sharpe,
            'profit_factor': profit_factor,
            'max_drawdown': result.max_drawdown,
            'final_balance': args.initial_balance + result.total_pnl,
            'risk_factor': risk_factor,
            'rr_ratio': rr_ratio,
        }
        results.append(result_dict)
        
        # Log progress
        if combo_num % max(1, total_combos // 10) == 0 or combo_num == 1:
            logger.info(
                f"[{combo_num}/{total_combos}] LB={lookback} FC={forecast} "
                f"ATR={atr_mult} RISKx={risk_factor} RR={rr_ratio} | WR={result.win_rate:.1f}% "
                f"PnL=${result.total_pnl:.2f} Sharpe={sharpe:.2f}"
            )
    
    # Convert to DataFrame and sort
    results_df = pd.DataFrame(results)
    
    # Sort by profit factor (quality wins) then win rate, then PnL
    results_df = results_df.sort_values(
        by=['profit_factor', 'win_rate', 'total_pnl'],
        ascending=[False, False, False]
    ).reset_index(drop=True)
    
    # Save results
    csv_path = f'param_optimizer_results_{args.symbol}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    results_df.to_csv(csv_path, index=False)
    logger.info(f"\nResults saved to {csv_path}")
    
    # Print top 10
    logger.info("\n" + "=" * 80)
    logger.info("TOP 10 PARAMETER COMBINATIONS (by Profit Factor)")
    logger.info("=" * 80)
    top_10 = results_df.head(10)
    for idx, row in top_10.iterrows():
        logger.info(
            f"{idx+1}. LB={int(row['lookback'])} FC={int(row['forecast'])} "
            f"ATR={row['atr_multiplier']:.1f} RISKx={row['risk_factor']:.2f} RR={row['rr_ratio']:.1f} | "
            f"WR={row['win_rate']:.1f}% PnL=${row['total_pnl']:.2f} "
            f"PF={row['profit_factor']:.2f} Sharpe={row['sharpe']:.2f}"
        )
    
    # Recommend best combo
    best = results_df.iloc[0]
    logger.info("\n" + "=" * 80)
    logger.info("RECOMMENDED PARAMETERS")
    logger.info("=" * 80)
    logger.info(f"lookback={int(best['lookback'])}")
    logger.info(f"forecast={int(best['forecast'])}")
    logger.info(f"atr_multiplier={best['atr_multiplier']:.1f}")
    logger.info(f"risk_factor={best['risk_factor']:.2f} (risk_cash={args.stake * best['risk_factor']:.2f})")
    logger.info(f"rr_ratio={best['rr_ratio']:.1f}")
    logger.info(f"Expected: WR={best['win_rate']:.1f}% PnL=${best['total_pnl']:.2f} PF={best['profit_factor']:.2f}")
    logger.info("=" * 80)
    
    return results_df


if __name__ == "__main__":
    asyncio.run(optimize_parameters())
