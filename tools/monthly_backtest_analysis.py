#!/usr/bin/env python3
"""
Monthly Backtest Analyzer
Run strategy on each month of data, collect metrics, visualize performance.

Usage:
  python tools/monthly_backtest_analysis.py --csv data/R_100_1h_1y.csv \
    --lookback 150 --forecast 20 --atr-mult 0.5 --stake 30 --risk-factor 0.5 --rr-ratio 3.0
"""
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategies import FourierStrategy
from src.backtesting import Backtester

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_monthly_backtest(
    csv_path: str,
    lookback: int = 150,
    forecast: int = 20,
    atr_mult: float = 0.5,
    stake: float = 30.0,
    risk_factor: float = 0.5,
    rr_ratio: float = 3.0,
    initial_balance: float = 1000.0,
    use_htf_filter: bool = False,
) -> pd.DataFrame:
    """
    Load CSV, chunk by month, run backtest on each, return monthly metrics.
    
    Returns:
        DataFrame with columns: month, trades, win_rate, total_pnl, avg_pnl_per_trade,
                                 max_profit, max_loss, max_drawdown, profit_factor, balance
    """
    # Load data
    logger.info(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Parse datetime
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    elif 'time' in df.columns:
        try:
            if pd.api.types.is_numeric_dtype(df['time']):
                df['datetime'] = pd.to_datetime(df['time'], unit='s', errors='coerce')
            else:
                df['datetime'] = pd.to_datetime(df['time'], errors='coerce')
        except Exception:
            df['datetime'] = pd.to_datetime(df['time'], errors='coerce')
    else:
        raise ValueError("No datetime/time column found")
    
    df = df.sort_values('datetime').reset_index(drop=True)
    logger.info(f"Loaded {len(df)} candles, date range: {df['datetime'].min()} to {df['datetime'].max()}")
    
    # Extract year-month
    df['year_month'] = df['datetime'].dt.to_period('M')
    
    # Group by month
    monthly_groups = df.groupby('year_month')
    logger.info(f"Found {len(monthly_groups)} months of data")
    
    results = []
    
    for month, month_df in monthly_groups:
        month_str = str(month)
        logger.info(f"\n{'='*60}")
        logger.info(f"Backtesting {month_str} ({len(month_df)} candles)...")
        logger.info(f"{'='*60}")
        
        if len(month_df) < 200:  # Need enough data for indicators
            logger.warning(f"  Skipping {month_str}: only {len(month_df)} candles (need >=200)")
            continue
        
        # Prepare MTF (4h) resampled closes if enabled
        mtf_series = None
        if use_htf_filter:
            # Resample 1h to 4h, then forward-fill to 1h for alignment
            month_df_copy = month_df.copy()
            month_df_copy['datetime'] = pd.to_datetime(month_df_copy['datetime'])
            month_df_copy = month_df_copy.set_index('datetime')
            
            # Resample to 4h
            mtf_resampled = month_df_copy['close'].resample('4H').last()
            
            # Forward-fill back to 1h alignment
            mtf_aligned = mtf_resampled.reindex(month_df_copy.index, method='ffill')
            
            # Convert to list for positional indexing (parallel to month_df rows)
            mtf_series = mtf_aligned.values
        
        # Create strategy and backtester
        strategy = FourierStrategy(params={
            'lookback': lookback,
            'forecast': forecast,
            'atr_multiplier': atr_mult,
            'stake': stake,
            'risk_cash': stake * risk_factor,
            'rr_ratio': rr_ratio,
            'mtf_enabled': use_htf_filter,
        })
        backtester = Backtester(strategy, initial_balance=initial_balance, stake_per_trade=stake)
        
        # Run backtest with MTF series
        result = backtester.run(month_df, mtf_series=mtf_series)
        
        # Calculate profit factor
        pnls = [t.pnl for t in result.trades if t.pnl is not None]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else (float('inf') if total_wins > 0 else 0)
        
        final_balance = initial_balance + result.total_pnl
        
        # Store result
        results.append({
            'month': month_str,
            'trades': result.total_trades,
            'winners': result.winning_trades,
            'losers': result.losing_trades,
            'win_rate': result.win_rate,
            'total_pnl': result.total_pnl,
            'avg_pnl_per_trade': result.avg_pnl_per_trade,
            'max_profit': result.max_profit,
            'max_loss': result.max_loss,
            'max_drawdown': result.max_drawdown,
            'profit_factor': profit_factor,
            'balance': final_balance,
        })
        
        logger.info(f"  {result.total_trades} trades | WR: {result.win_rate:.1f}% | PF: {profit_factor:.2f} | PnL: ${result.total_pnl:.2f} | DD: {result.max_drawdown:.2f}%")
    
    result_df = pd.DataFrame(results)
    return result_df


def visualize_monthly_results(results_df: pd.DataFrame, output_path: str = 'monthly_analysis.png'):
    """Create visualization of monthly metrics."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        logger.warning("matplotlib not installed; skipping visualization")
        return
    
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle('Monthly Strategy Performance', fontsize=16, fontweight='bold')
    
    # Parse month strings to datetime for x-axis
    months = pd.to_datetime(results_df['month'].astype(str))
    
    # 1. PnL per month
    axes[0, 0].bar(months, results_df['total_pnl'], color=['green' if x > 0 else 'red' for x in results_df['total_pnl']])
    axes[0, 0].set_title('Total PnL per Month')
    axes[0, 0].set_ylabel('PnL ($)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Win Rate
    axes[0, 1].plot(months, results_df['win_rate'], marker='o', color='blue', linewidth=2)
    axes[0, 1].axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='50%')
    axes[0, 1].set_title('Win Rate per Month')
    axes[0, 1].set_ylabel('Win Rate (%)')
    axes[0, 1].set_ylim([0, 100])
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend()
    
    # 3. Profit Factor
    axes[1, 0].bar(months, results_df['profit_factor'], color='skyblue')
    axes[1, 0].axhline(y=1.8, color='green', linestyle='--', alpha=0.7, label='Target (1.8)')
    axes[1, 0].axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Breakeven (1.0)')
    axes[1, 0].set_title('Profit Factor per Month')
    axes[1, 0].set_ylabel('Profit Factor')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend()
    
    # 4. Max Drawdown
    axes[1, 1].bar(months, results_df['max_drawdown'], color='salmon')
    axes[1, 1].axhline(y=20, color='orange', linestyle='--', alpha=0.7, label='Target (20%)')
    axes[1, 1].set_title('Max Drawdown per Month')
    axes[1, 1].set_ylabel('Max Drawdown (%)')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend()
    
    # 5. Trade Count
    axes[2, 0].bar(months, results_df['trades'], color='purple')
    axes[2, 0].set_title('Trade Count per Month')
    axes[2, 0].set_ylabel('Trades')
    axes[2, 0].grid(True, alpha=0.3)
    
    # 6. Running Balance
    axes[2, 1].plot(months, results_df['balance'], marker='o', color='darkgreen', linewidth=2, label='Balance')
    axes[2, 1].axhline(y=1000, color='gray', linestyle='--', alpha=0.5, label='Initial')
    axes[2, 1].set_title('Account Balance per Month')
    axes[2, 1].set_ylabel('Balance ($)')
    axes[2, 1].grid(True, alpha=0.3)
    axes[2, 1].legend()
    
    # Format x-axis
    for ax in axes.flat:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"Saved visualization to {output_path}")
    plt.show()


def parse_args():
    p = argparse.ArgumentParser(description='Monthly backtest analysis and visualization')
    p.add_argument('--csv', required=True, help='Path to 1h OHLC CSV')
    p.add_argument('--lookback', type=int, default=150)
    p.add_argument('--forecast', type=int, default=20)
    p.add_argument('--atr-mult', type=float, default=0.5)
    p.add_argument('--stake', type=float, default=30.0)
    p.add_argument('--risk-factor', type=float, default=0.5)
    p.add_argument('--rr-ratio', type=float, default=3.0)
    p.add_argument('--initial-balance', type=float, default=1000.0)
    p.add_argument('--use-htf-filter', action='store_true', help='Enable 4h HTF trend filter')
    p.add_argument('--output', default='monthly_analysis.png', help='Output visualization path')
    p.add_argument('--csv-output', default='monthly_results.csv', help='Output CSV path for metrics')
    return p.parse_args()


def main():
    args = parse_args()
    
    # Run monthly backtests
    results_df = run_monthly_backtest(
        csv_path=args.csv,
        lookback=args.lookback,
        forecast=args.forecast,
        atr_mult=args.atr_mult,
        stake=args.stake,
        risk_factor=args.risk_factor,
        rr_ratio=args.rr_ratio,
        initial_balance=args.initial_balance,
        use_htf_filter=args.use_htf_filter,
    )
    
    # Save results to CSV
    results_df.to_csv(args.csv_output, index=False)
    logger.info(f"\nSaved monthly results to {args.csv_output}")
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("MONTHLY SUMMARY")
    logger.info(f"{'='*60}")
    print(results_df.to_string(index=False))
    
    # Summary stats
    logger.info(f"\n{'='*60}")
    logger.info("AGGREGATE STATS")
    logger.info(f"{'='*60}")
    logger.info(f"Total Months: {len(results_df)}")
    logger.info(f"Total Trades: {results_df['trades'].sum()}")
    logger.info(f"Avg Win Rate: {results_df['win_rate'].mean():.2f}%")
    logger.info(f"Avg PnL/Month: ${results_df['total_pnl'].mean():.2f}")
    logger.info(f"Best Month: {results_df.loc[results_df['total_pnl'].idxmax(), 'month']} (${results_df['total_pnl'].max():.2f})")
    logger.info(f"Worst Month: {results_df.loc[results_df['total_pnl'].idxmin(), 'month']} (${results_df['total_pnl'].min():.2f})")
    logger.info(f"Avg Profit Factor: {results_df['profit_factor'].mean():.2f}")
    logger.info(f"Avg Max Drawdown: {results_df['max_drawdown'].mean():.2f}%")
    logger.info(f"Final Balance: ${results_df['balance'].iloc[-1]:.2f}")
    
    # Visualize
    visualize_monthly_results(results_df, output_path=args.output)
    logger.info(f"\nAnalysis complete!")


if __name__ == '__main__':
    main()
