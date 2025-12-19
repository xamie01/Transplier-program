#!/usr/bin/env python3
"""
Backtest Runner
Download data and run strategy backtest
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.deriv_api.data_downloader import DerivDataDownloader
from src.backtesting import Backtester
from src.strategies import FourierStrategy


def setup_logging(level: str = 'INFO'):
    """Setup logging"""
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('backtest.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    parser = argparse.ArgumentParser(description='Strategy Backtest Runner')
    parser.add_argument('--symbol', type=str, default='R_100',
                       help='Trading symbol (R_100, R_75, VOLATILITY_75_1S, etc.)')
    parser.add_argument('--interval', type=int, default=60,
                       help='Candle interval in seconds (60=1m, 300=5m, etc.)')
    parser.add_argument('--days', type=int, default=30,
                       help='Days of historical data to download')
    parser.add_argument('--strategy', type=str, default='FourierStrategy',
                       help='Strategy name (FourierStrategy, etc.)')
    parser.add_argument('--initial-balance', type=float, default=1000.0,
                       help='Initial account balance for backtest')
    parser.add_argument('--stake', type=float, default=30.0,
                       help='Stake per trade')
    parser.add_argument('--risk-factor', type=float, default=0.5,
                       help='Cash risk as fraction of stake (e.g., 0.5 = half stake)')
    parser.add_argument('--rr-ratio', type=float, default=3.0,
                       help='Risk-reward ratio for take profit')
    parser.add_argument('--use-htf-filter', action='store_true',
                       help='Enable 4H HTF trend gate (resampled from 1H data)')
    parser.add_argument('--lookback', type=int, default=150,
                       help='Lookback window for dominant period detection')
    parser.add_argument('--forecast', type=int, default=20,
                       help='Forecast horizon (candles) for harmonic projection')
    parser.add_argument('--smooth-period', type=int, default=11,
                       help='Weighted MA smoothing period')
    parser.add_argument('--atr-period', type=int, default=14,
                       help='ATR lookback')
    parser.add_argument('--atr-mult', type=float, default=0.5,
                       help='ATR multiplier for entry threshold')
    parser.add_argument('--csv', type=str, default=None,
                       help='Load data from CSV instead of downloading')
    parser.add_argument('--download-only', action='store_true',
                       help='Only download data, do not run backtest')
    
    args = parser.parse_args()
    
    setup_logging('INFO')
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("Strategy Backtest Runner")
    logger.info("=" * 70)
    
    # Load or download data (cache-first)
    import pandas as pd
    csv_name = f"data/{args.symbol}_candles_{args.interval}s_{args.days}d.csv"

    if args.csv and Path(args.csv).exists():
        logger.info(f"Loading data from {args.csv}")
        df = pd.read_csv(args.csv)
    elif Path(csv_name).exists():
        logger.info(f"Loading cached data from {csv_name}")
        df = pd.read_csv(csv_name)
    else:
        logger.info(f"Downloading data for {args.symbol}...")
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
    
    if args.download_only:
        logger.info("Download complete, exiting")
        return
    
    # Normalize datetime column when loaded from arbitrary CSV
    # Handles: 'datetime' (ISO), 'epoch' (seconds), 'time' (ISO or seconds)
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    elif 'epoch' in df.columns:
        df['datetime'] = pd.to_datetime(df['epoch'], unit='s', errors='coerce')
    elif 'time' in df.columns:
        # Try seconds-based first if numeric; else parse ISO
        try:
            if pd.api.types.is_numeric_dtype(df['time']):
                df['datetime'] = pd.to_datetime(df['time'], unit='s', errors='coerce')
            else:
                df['datetime'] = pd.to_datetime(df['time'], errors='coerce')
        except Exception:
            df['datetime'] = pd.to_datetime(df['time'], errors='coerce')
    else:
        logger.warning("No datetime/epoch/time column found; attempting to infer index")
        if df.index.dtype == 'int64' or df.index.dtype == 'int32':
            df['datetime'] = pd.to_datetime(df.index, unit='s', errors='coerce')
        else:
            df['datetime'] = pd.to_datetime(df.index, errors='coerce')

    # Sort and reset index for clean alignment
    df = df.sort_values('datetime').reset_index(drop=True)
    logger.info(f"\nLoaded {len(df)} candles")
    logger.info(f"  Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    
    # Optional 4H HTF filter: resample close to 4H and forward-fill to 1H index
    mtf_series = None
    if args.use_htf_filter:
        dt_index = pd.DatetimeIndex(df['datetime'])
        resampled = df.set_index(dt_index)['close'].resample('4H').last().ffill()
        mtf_series = resampled.reindex(dt_index, method='ffill').reset_index(drop=True)

    # Get strategy class
    strategies = {
        'FourierStrategy': FourierStrategy,
        # Add more strategies here
    }
    
    if args.strategy not in strategies:
        logger.error(f"Unknown strategy: {args.strategy}")
        logger.info(f"Available: {list(strategies.keys())}")
        return
    
    StrategyClass = strategies[args.strategy]
    
    # Create and run backtest
    strategy = StrategyClass(params={
        'stake': args.stake,
        'risk_cash': args.stake * args.risk_factor,
        'rr_ratio': args.rr_ratio,
        'mtf_enabled': args.use_htf_filter,
        'lookback': args.lookback,
        'forecast': args.forecast,
        'smooth_period': args.smooth_period,
        'atr_period': args.atr_period,
        'atr_multiplier': args.atr_mult,
    })
    backtester = Backtester(
        strategy=strategy,
        initial_balance=args.initial_balance,
        stake_per_trade=args.stake
    )
    
    logger.info("\nRunning backtest...")
    result = backtester.run(df, mtf_series=mtf_series)
    
    # Print summary
    logger.info("\nBacktest Summary:")
    for key, value in result.to_dict().items():
        logger.info(f"  {key}: {value}")
    
    # Optional: export trades
    if result.trades:
        import pandas as pd
        trades_df = pd.DataFrame([
            {
                'entry_time': t.entry_time,
                'entry_price': f"${t.entry_price:.4f}",
                'entry_signal': t.entry_signal,
                'exit_time': t.exit_time,
                'exit_price': f"${t.exit_price:.4f}" if t.exit_price else None,
                'pnl': f"${t.pnl:.2f}" if t.pnl is not None else None,
                'pnl_pct': f"{t.pnl_pct:.2f}%" if t.pnl_pct is not None else None,
                'duration_min': f"{t.duration_seconds/60:.2f}" if t.duration_seconds else None
            }
            for t in result.trades[:20]  # Show first 20
        ])
        
        logger.info("\nFirst 20 Trades:")
        logger.info(trades_df.to_string(index=False))
        
        # Save all trades
        all_trades_df = pd.DataFrame([
            {
                'entry_time': t.entry_time,
                'entry_price': t.entry_price,
                'entry_signal': t.entry_signal,
                'exit_time': t.exit_time,
                'exit_price': t.exit_price,
                'pnl': t.pnl,
                'pnl_pct': t.pnl_pct,
                'duration_sec': t.duration_seconds
            }
            for t in result.trades
        ])
        
        trades_csv = f"backtest_trades_{args.symbol}_{args.strategy}.csv"
        all_trades_df.to_csv(trades_csv, index=False)
        logger.info(f"\nAll {len(result.trades)} trades saved to {trades_csv}")
    
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
