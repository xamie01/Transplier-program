"""
Deriv Data Downloader
Fetch historical candle data from Deriv API
"""
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from .client import DerivAPIClient
import os

logger = logging.getLogger(__name__)


class DerivDataDownloader:
    """Download historical candle data from Deriv"""
    
    def __init__(self, app_id: str = "1089", api_token: Optional[str] = None):
        self.client = DerivAPIClient(app_id=app_id, api_token=api_token)
        
    async def connect(self):
        """Connect to Deriv API"""
        await self.client.connect()
        logger.info("Connected to Deriv API")
        
    async def disconnect(self):
        """Disconnect from API"""
        await self.client.close()
        
    SYMBOL_ALIASES: Dict[str, str] = {
        "VOLATILITY_75_1S": "R_75_1S",
        "V75_1S": "R_75_1S",
        "VOL_75_1S": "R_75_1S",
        "R_50": "R_50",
        "R_75": "R_75",
        "R_100": "R_100",
        "R_25": "R_25",
        "R_10": "R_10",
        "R_30": "R_30",
        "R_150": "R_150",
    }

    def _resolve_symbol(self, symbol: str) -> str:
        return self.SYMBOL_ALIASES.get(symbol, symbol)

    def _cache_path(self, symbol: str, interval: int, days_back: int) -> str:
        os.makedirs("data", exist_ok=True)
        return f"data/{symbol}_candles_{interval}s_{days_back}d.csv"

    async def download_candles(self,
                              symbol: str,
                              interval: int,
                              days_back: int = 30,
                              max_count: int = 10000,
                              use_cache: bool = True,
                              force_refresh: bool = False) -> pd.DataFrame:
        """
        Download historical candles from Deriv
        
        Args:
            symbol: Trading symbol (e.g., 'R_100')
            interval: Candle interval in seconds (60, 120, 300, etc.)
            days_back: How many days back to fetch (default 30)
            max_count: Max candles to fetch (API limit)
            
        Returns:
            DataFrame with columns: time, open, high, low, close, volume
        """
        # Cache-first load
        cache_path = self._cache_path(symbol, interval, days_back)
        if use_cache and not force_refresh and os.path.exists(cache_path):
            df = pd.read_csv(cache_path)
            df['datetime'] = pd.to_datetime(df['datetime'])
            logger.info(f"Loaded cached data: {cache_path}")
            logger.info(f"  Loaded {len(df)} candles")
            logger.info(f"  Date range: {df['datetime'].min()} to {df['datetime'].max()}")
            return df

        # Calculate time window
        end_time = datetime.utcnow().timestamp()
        start_time = (datetime.utcnow() - timedelta(days=days_back)).timestamp()
        
        logger.info(f"Downloading {symbol} candles (interval={interval}s, days={days_back})")
        logger.info(f"  From: {datetime.fromtimestamp(start_time)}")
        logger.info(f"  To:   {datetime.fromtimestamp(end_time)}")
        
        # Request historical candles
        api_symbol = self._resolve_symbol(symbol)
        request = {
            "ticks_history": api_symbol,
            "adjust_start_time": 1,
            "count": min(max_count, 10000),  # API limit
            "end": "latest",
            "start": int(start_time),
            "style": "candles",
            "granularity": interval
        }
        
        try:
            response = await self.client.send_request(request)
        except asyncio.TimeoutError:
            raise Exception("Download timed out. Try reducing days or interval.")
        
        if 'error' in response:
            msg = response['error'].get('message', 'Unknown error')
            code = response['error'].get('code')
            hint = "Try one of: R_50, R_75, R_100, R_25, R_75_1S"
            if code == 'InvalidValue' or 'invalid' in msg.lower():
                raise Exception(f"Download error: {msg}. Hint: {hint}")
            raise Exception(f"Download error: {msg}")
            
        candles = response.get('candles', [])
        logger.info(f"  Downloaded {len(candles)} candles")
        
        # Convert to DataFrame
        df_data = []
        for candle in candles:
            df_data.append({
                'time': int(candle.get('epoch', 0)),
                'open': float(candle.get('open', 0)),
                'high': float(candle.get('high', 0)),
                'low': float(candle.get('low', 0)),
                'close': float(candle.get('close', 0))
            })
            
        df = pd.DataFrame(df_data)
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        df = df.sort_values('time').reset_index(drop=True)
        
        logger.info(f"  Date range: {df['datetime'].min()} to {df['datetime'].max()}")

        # Save cache
        df.to_csv(cache_path, index=False)
        logger.info(f"Saved data to {cache_path}")

        return df
        
    async def download_multiple_symbols(self,
                                       symbols: List[str],
                                       interval: int = 300,
                                       days_back: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Download candles for multiple symbols
        
        Returns:
            Dict mapping symbol to DataFrame
        """
        results = {}
        for symbol in symbols:
            try:
                df = await self.download_candles(symbol, interval, days_back)
                results[symbol] = df
            except Exception as e:
                logger.error(f"Failed to download {symbol}: {e}")
                
        return results


async def download_data_example():
    """Example: download candles for backtesting"""
    downloader = DerivDataDownloader()
    
    try:
        await downloader.connect()
        
        # Download R_100 1-minute candles for past 30 days
        df = await downloader.download_candles(
            symbol='R_100',
            interval=60,  # 1 minute
            days_back=30
        )
        
        print(f"\nDownloaded {len(df)} candles")
        print(df.head())
        print(df.tail())
        
        # Save to CSV
        csv_path = 'backtest_data_R100.csv'
        df.to_csv(csv_path, index=False)
        print(f"\nSaved to {csv_path}")
        
    finally:
        await downloader.disconnect()


if __name__ == "__main__":
    asyncio.run(download_data_example())
