#!/usr/bin/env python3
"""Quick backtest example"""
import asyncio
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

async def main():
    from src.deriv_api.data_downloader import DerivDataDownloader
    from src.backtesting import Backtester
    from src.strategies import FourierStrategy
    
    print("\n" + "="*70)
    print("Deriv Strategy Backtest - Quick Start")
    print("="*70)
    
    # Download data
    print("\nDownloading R_100 data (7 days, 1-min candles)...")
    downloader = DerivDataDownloader()
    
    try:
        await downloader.connect()
        df = await downloader.download_candles(
            symbol='R_100',
            interval=60,
            days_back=7
        )
    finally:
        await downloader.disconnect()
    
    print(f"\n✓ Downloaded {len(df)} candles")
    print(f"  Date range: {df['datetime'].min()} to {df['datetime'].max()}\n")
    
    # Run backtest
    print("Running backtest with FourierStrategy...")
    print("-" * 70)
    
    strategy = FourierStrategy()
    backtester = Backtester(
        strategy=strategy,
        initial_balance=1000.0,
        stake_per_trade=10.0
    )
    
    result = backtester.run(df)
    
    # Print results
    print("\nBacktest Results:")
    print("-" * 70)
    for key, value in result.to_dict().items():
        print(f"  {key:.<40} {value}")
    
    if result.trades:
        print(f"\nTrade Details (first 10):")
        print("-" * 70)
        for i, trade in enumerate(result.trades[:10]):
            print(f"  {i+1}. {trade.entry_signal:5} @ ${trade.entry_price:8.4f} "
                  f"→ ${trade.exit_price:8.4f} | "
                  f"PnL: ${trade.pnl:7.2f} ({trade.pnl_pct:+6.2f}%)")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
