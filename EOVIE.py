"""
EOVIE Strategy (Simplified for Transpiler Testing)
Name: EOVIE RSI/SMA Crossover
Author: Original Author
Timeframe: 5m
Description: Simplified version for transpiler testing (removes custom_exit and dynamic params)
"""

import talib.abstract as ta
import pandas_ta as pta
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


class EOVIESimplified(IStrategy):
    """Simplified EOVIE strategy for testing transpiler."""
    
    minimal_roi = {"0": 10}
    timeframe = '5m'
    stoploss = -0.18
    startup_candle_count = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Calculate indicators."""
        # SMA and RSI indicators
        dataframe['sma_15'] = ta.SMA(dataframe, timeperiod=15)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['rsi_fast'] = ta.RSI(dataframe, timeperiod=4)
        dataframe['rsi_slow'] = ta.RSI(dataframe, timeperiod=20)
        dataframe['cti'] = pta.cti(dataframe["close"], length=20)
        
        # Stochastic for exit
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe['fastk'] = stoch_fast['fastk']
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Buy signal: RSI conditions and SMA alignment."""
        dataframe.loc[
            (
                (dataframe['rsi_slow'] < dataframe['rsi_slow'].shift(1)) &
                (dataframe['rsi_fast'] < 45) &
                (dataframe['rsi'] > 35) &
                (dataframe['close'] < dataframe['sma_15'] * 0.961) &
                (dataframe['cti'] < -0.58)
            ),
            'enter_long'] = 1
        
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Sell signal: Stochastic FastK cross."""
        dataframe.loc[
            (dataframe['fastk'] > 75),
            'exit_long'] = 1
        
        return dataframe