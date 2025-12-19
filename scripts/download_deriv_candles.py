#!/usr/bin/env python3
"""
Deriv candles downloader (paginated)
Fetches historical candles in chunks and writes a CSV.

Usage:
  python scripts/download_deriv_candles.py --symbol R_100 --granularity 3600 --days 365 --out data/R_100_1h_1y.csv

Notes:
- Uses Deriv WebSocket API (`ticks_history` with style=candles)
- Paginates by time range (`start`/`end`) to respect per-request limits
- Default chunk is 60 days (~1440 candles per request at 1h)
- Set DERIV_APP_ID in environment for your app id (default 1089)
"""
import os
import sys
import json
import time
import argparse
import asyncio
from datetime import datetime, timezone

import pandas as pd
import websockets

DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089")
WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"


async def fetch_candles(ws, symbol: str, start_epoch: int, end_epoch: int, granularity: int) -> list:
    """Fetch candles for [start_epoch, end_epoch] window.
    Returns a list of candle dicts with epoch, open, high, low, close, etc.
    """
    req = {
        "ticks_history": symbol,
        "style": "candles",
        "granularity": granularity,
        "start": start_epoch,
        "end": end_epoch,
    }
    await ws.send(json.dumps(req))
    msg = await ws.recv()
    resp = json.loads(msg)
    if "error" in resp:
        err = resp["error"]
        raise RuntimeError(f"Deriv API error {err.get('code')}: {err.get('message')}")
    return resp.get("candles", [])


async def download(symbol: str, days: int, granularity: int, outfile: str, chunk_days: int) -> None:
    """Download candles over `days`, chunked by `chunk_days`, save to `outfile`."""
    now = int(time.time())
    start = now - days * 86400
    chunk_sec = max(1, chunk_days) * 86400

    all_candles: list[dict] = []
    got = 0

    async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=20, max_size=8 * 1024 * 1024) as ws:
        t0 = start
        while t0 < now:
            t1 = min(t0 + chunk_sec, now)
            try:
                candles = await fetch_candles(ws, symbol, t0, t1, granularity)
            except Exception as e:
                # Fallback: shrink window if needed, retry once
                try:
                    if (t1 - t0) > 7 * 86400:
                        t1 = t0 + 7 * 86400
                        candles = await fetch_candles(ws, symbol, t0, t1, granularity)
                    else:
                        print(f"Skipping window {t0}..{t1}: {e}", file=sys.stderr)
                        candles = []
                except Exception as e2:
                    print(f"Skipping window {t0}..{t1} after fallback: {e2}", file=sys.stderr)
                    candles = []

            all_candles.extend(candles)
            got += len(candles)

            # Progress log
            pct = (t1 - start) / max(1, (now - start)) * 100
            print(f"[{pct:5.1f}%] {symbol} {datetime.fromtimestamp(t0, tz=timezone.utc)} → {datetime.fromtimestamp(t1, tz=timezone.utc)} | +{len(candles)} (total {got})")

            # Gentle pacing to avoid throttling
            await asyncio.sleep(0.15)
            t0 = t1

    if not all_candles:
        raise SystemExit("No candles returned. Check symbol/granularity or app id.")

    df = pd.DataFrame(all_candles)
    if "epoch" not in df.columns:
        raise SystemExit("Unexpected response: missing 'epoch' in candles.")

    # Types and ordering
    df["epoch"] = df["epoch"].astype(int)
    for col in ("open", "high", "low", "close"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"]).drop_duplicates(subset=["epoch"]).sort_values("epoch")
    df["time"] = pd.to_datetime(df["epoch"], unit="s", utc=True)

    # Save
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    df.to_csv(outfile, index=False)
    print(f"Saved {len(df)} candles to {outfile}")


def parse_args():
    p = argparse.ArgumentParser(description="Download Deriv candles (paginated)")
    p.add_argument("--symbol", required=True, help="e.g. R_100")
    p.add_argument("--days", type=int, default=365, help="Days back to fetch")
    p.add_argument("--granularity", type=int, default=3600, help="Candle interval in seconds (3600 = 1h)")
    p.add_argument("--out", default="data/R_100_1h_1y.csv", help="Output CSV path")
    p.add_argument("--chunk-days", type=int, default=60, help="Days per request chunk (60 is safe)")
    return p.parse_args()


def main():
    args = parse_args()
    asyncio.run(download(args.symbol, args.days, args.granularity, args.out, args.chunk_days))


if __name__ == "__main__":
    main()
