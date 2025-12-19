#!/usr/bin/env python3
"""
Walk-Forward Tester
Run rolling train/test windows to validate strategy robustness on synthetic indices.
"""
import argparse
import asyncio
import logging
import sys
from datetime import timedelta
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.deriv_api.data_downloader import DerivDataDownloader
from src.backtesting import Backtester
from src.strategies import FourierStrategy


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("walk_forward.log"), logging.StreamHandler(sys.stdout)],
    )


def add_epoch_column(df: pd.DataFrame) -> pd.DataFrame:
    if "time" not in df.columns:
        df = df.copy()
        df["time"] = (pd.to_datetime(df["datetime"]).astype(np.int64) // 1_000_000_000).astype(int)
    return df


def make_splits(df: pd.DataFrame, train_days: int, test_days: int) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    splits = []
    df = df.sort_values("datetime")
    start = df["datetime"].min()
    end = df["datetime"].max()
    window_train = timedelta(days=train_days)
    window_test = timedelta(days=test_days)

    cursor = start
    while cursor + window_train + window_test <= end:
        train_end = cursor + window_train
        test_end = train_end + window_test
        train_df = df[(df["datetime"] >= cursor) & (df["datetime"] < train_end)]
        test_df = df[(df["datetime"] >= train_end) & (df["datetime"] < test_end)]
        if len(test_df) == 0 or len(train_df) == 0:
            cursor += window_test
            continue
        splits.append((train_df, test_df))
        cursor += window_test  # roll forward by test window
    return splits


def compute_metrics(trades, initial_balance: float):
    if not trades:
        return {
            "trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_pnl": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
            "final_balance": initial_balance,
        }
    pnls = [t.pnl for t in trades if t.pnl is not None]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    total_pnl = sum(pnls)
    win_rate = (len(wins) / len(pnls)) * 100 if pnls else 0
    avg_pnl = total_pnl / len(pnls) if pnls else 0
    profit_factor = (sum(wins) / abs(sum(losses))) if losses else float("inf") if wins else 0.0
    # Simple drawdown using cumulative equity
    equity = initial_balance
    peak = equity
    max_dd = 0.0
    for p in pnls:
        equity += p
        peak = max(peak, equity)
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
    return {
        "trades": len(pnls),
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "avg_pnl": avg_pnl,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
        "final_balance": initial_balance + total_pnl,
    }


def run_backtest_on_split(train_df: pd.DataFrame, test_df: pd.DataFrame, stake: float, initial_balance: float, params: dict):
    """Prime strategy with tail of train, evaluate trades only in test window."""
    # Prime with last required candles from train
    prime_len = max(params.get("lookback", 150), 200)
    prime_df = pd.concat([train_df.tail(prime_len), test_df], ignore_index=True)

    strategy = FourierStrategy(params=params)
    backtester = Backtester(strategy=strategy, initial_balance=initial_balance, stake_per_trade=stake)
    result = backtester.run(prime_df)

    test_start_epoch = int(test_df["time"].iloc[0])
    filtered_trades = [t for t in result.trades if t.entry_time >= test_start_epoch]
    metrics = compute_metrics(filtered_trades, initial_balance)
    return metrics, filtered_trades


async def main():
    parser = argparse.ArgumentParser(description="Walk-Forward Tester")
    parser.add_argument("--symbol", type=str, default="R_100")
    parser.add_argument("--interval", type=int, default=3600)
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--train-days", type=int, default=14)
    parser.add_argument("--test-days", type=int, default=7)
    parser.add_argument("--stake", type=float, default=30.0)
    parser.add_argument("--initial-balance", type=float, default=1000.0)
    parser.add_argument("--lookback", type=int, default=150)
    parser.add_argument("--forecast", type=int, default=20)
    parser.add_argument("--atr-mult", type=float, default=0.5)
    parser.add_argument("--risk-factor", type=float, default=0.5, help="Cash risk as fraction of stake")
    parser.add_argument("--rr-ratio", type=float, default=3.0, help="Risk-reward ratio for take profit")
    args = parser.parse_args()

    setup_logging("INFO")
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("Walk-Forward Test")
    logger.info("=" * 80)
    logger.info(f"Symbol: {args.symbol} | Interval: {args.interval}s | Days: {args.days}")
    logger.info(
        f"Train {args.train_days}d, Test {args.test_days}d | Stake: ${args.stake} "
        f"Riskx={args.risk_factor} RR={args.rr_ratio}"
    )

    # Download data
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

    df = add_epoch_column(df)
    splits = make_splits(df, train_days=args.train_days, test_days=args.test_days)
    if not splits:
        logger.error("Not enough data to form splits. Increase --days or adjust windows.")
        return

    params = {
        "lookback": args.lookback,
        "forecast": args.forecast,
        "atr_multiplier": args.atr_mult,
        "stake": args.stake,
        "risk_cash": args.stake * args.risk_factor,
        "rr_ratio": args.rr_ratio,
    }

    all_metrics = []
    logger.info(f"Total splits: {len(splits)}")
    for idx, (train_df, test_df) in enumerate(splits, 1):
        metrics, _ = run_backtest_on_split(train_df, test_df, args.stake, args.initial_balance, params)
        all_metrics.append(metrics)
        logger.info(
            f"Split {idx}: trades={metrics['trades']}, WR={metrics['win_rate']:.1f}%, "
            f"PnL=${metrics['total_pnl']:.2f}, PF={metrics['profit_factor']:.2f}, DD={metrics['max_drawdown']:.2f}%"
        )

    # Aggregate
    df_metrics = pd.DataFrame(all_metrics)
    agg = {
        "splits": len(splits),
        "trades": df_metrics["trades"].sum(),
        "avg_win_rate": df_metrics["win_rate"].mean(),
        "total_pnl": df_metrics["total_pnl"].sum(),
        "avg_pnl_per_split": df_metrics["total_pnl"].mean(),
        "median_pnl_per_split": df_metrics["total_pnl"].median(),
        "avg_profit_factor": df_metrics["profit_factor"].replace(np.inf, np.nan).mean(),
        "max_drawdown": df_metrics["max_drawdown"].max(),
        "final_balance": args.initial_balance + df_metrics["total_pnl"].sum(),
    }

    logger.info("\n" + "=" * 80)
    logger.info("WALK-FORWARD SUMMARY")
    logger.info("=" * 80)
    for k, v in agg.items():
        if isinstance(v, float):
            logger.info(f"{k}: {v:.2f}")
        else:
            logger.info(f"{k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
