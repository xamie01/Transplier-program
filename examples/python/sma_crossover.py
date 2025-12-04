"""Example Python trading strategy: SMA Crossover."""

def strategy(df):
    """
    SMA Crossover Strategy
    
    Generates a signal based on a crossover between fast and slow moving averages.
    
    Entry: when the 20-period SMA crosses above the 50-period SMA
    Exit: when the 20-period SMA crosses below the 50-period SMA
    
    Position Size: 10% of account per trade
    """
    
    # Calculate moving averages
    sma_fast = sma(df['close'], 20)
    sma_slow = sma(df['close'], 50)
    
    # Initialize signals
    signals = []
    
    # Generate signals
    for i in range(len(df)):
        if i < 50:  # Need at least 50 bars for slow SMA
            signals.append(0)
            continue
        
        # Check for crossover (entry condition)
        if sma_fast[i-1] <= sma_slow[i-1] and sma_fast[i] > sma_slow[i]:
            signals.append(1)  # BUY
        
        # Check for crossunder (exit condition)
        elif sma_fast[i-1] >= sma_slow[i-1] and sma_fast[i] < sma_slow[i]:
            signals.append(-1)  # SELL
        
        else:
            signals.append(0)  # HOLD
    
    return signals


def sma(prices, period):
    """Calculate simple moving average."""
    return prices.rolling(window=period).mean()


if __name__ == "__main__":
    import pandas as pd
    
    # Example usage
    data = pd.read_csv("example_data.csv")
    signals = strategy(data)
    print(signals)
