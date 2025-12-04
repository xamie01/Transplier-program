"""
Simple SMA Crossover Strategy - Python Implementation

This is a basic trend-following strategy that uses two Simple Moving Averages.
Entry: When fast SMA crosses above slow SMA (bullish signal)
Exit: When fast SMA crosses below slow SMA (bearish signal)
"""

STRATEGY_NAME = "SMA Crossover"
TIMEFRAME = "1h"
POSITION_SIZE = 1.0
STOP_LOSS = 2.0  # 2% stop loss
TAKE_PROFIT = 4.0  # 4% take profit


class SMACrossoverStrategy:
    """
    Simple Moving Average Crossover Strategy
    
    Uses 20-period and 50-period SMAs to generate trading signals.
    """
    
    def __init__(self):
        self.name = "SMA Crossover"
        self.timeframe = "1h"
        self.position_size = 1.0
        self.stop_loss = 2.0
        self.take_profit = 4.0
    
    def calculate_indicators(self, data):
        """Calculate technical indicators."""
        # Calculate 20-period SMA
        sma_20 = data['close'].rolling(window=20).mean()
        
        # Calculate 50-period SMA
        sma_50 = data['close'].rolling(window=50).mean()
        
        data['sma_20'] = sma_20
        data['sma_50'] = sma_50
        
        return data
    
    def check_signals(self, data):
        """Check for entry and exit signals."""
        signals = {
            'entry_long': False,
            'entry_short': False,
            'exit_long': False,
            'exit_short': False
        }
        
        if len(data) < 2:
            return signals
        
        # Entry long condition
        # Current: sma_20 > sma_50, Previous: sma_20 <= sma_50 (crossover)
        signals['entry_long'] = (
            data['sma_20'].iloc[-1] > data['sma_50'].iloc[-1] and
            data['sma_20'].iloc[-2] <= data['sma_50'].iloc[-2]
        )
        
        # Exit condition
        # Current: sma_20 < sma_50, Previous: sma_20 >= sma_50 (crossunder)
        signals['exit_long'] = (
            data['sma_20'].iloc[-1] < data['sma_50'].iloc[-1] and
            data['sma_20'].iloc[-2] >= data['sma_50'].iloc[-2]
        )
        signals['exit_short'] = signals['exit_long']
        
        return signals
    
    def run(self, data):
        """
        Run the strategy on historical data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicators and signals
        """
        data = self.calculate_indicators(data)
        signals = self.check_signals(data)
        
        # Add signals to dataframe
        for key, value in signals.items():
            data[key] = value
        
        return data


if __name__ == "__main__":
    # Example usage
    import pandas as pd
    
    strategy = SMACrossoverStrategy()
    print(f"Strategy: {strategy.name}")
    print(f"Timeframe: {strategy.timeframe}")
    print(f"Position Size: {strategy.position_size}")
    print(f"Stop Loss: {strategy.stop_loss}%")
    print(f"Take Profit: {strategy.take_profit}%")
