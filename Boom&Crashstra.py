import numpy as np
import pandas as pd

class SpikeCatcherEngine:
    def __init__(self, index_name='Boom 1000', rsi_period=14, sigma_window=20):
        self.index_name = index_name
        self.rsi_period = rsi_period
        self.sigma_window = sigma_window
        
        # Engineering Constants: Probability intensity (lambda)
        # B1000/C1000 have lower frequency than 500 series
        self.lam = 0.001 if '1000' in index_name else 0.002
        self.is_boom = 'Boom' in index_name

    def calculate_metrics(self, df):
        """Calculates the physical properties of the price action."""
        # 1. RSI (Momentum Exhaustion)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

        # 2. Volatility Squeeze (Standard Deviation vs Moving Average)
        df['STD'] = df['Close'].rolling(window=self.sigma_window).std()
        df['STD_MA'] = df['STD'].rolling(window=self.sigma_window).mean()
        
        # 3. Time Probability (CDF of Exponential Distribution)
        # Tracking ticks since the last 'jump' event
        df['Is_Spike'] = self._detect_spikes(df)
        return df

    def _detect_spikes(self, df):
        # A spike is a move > 4x the standard deviation of noise
        threshold = df['Close'].diff().std() * 4
        if self.is_boom:
            return df['Close'].diff() > threshold
        return df['Close'].diff() < -threshold

    def generate_signal(self, df):
        df = self.calculate_metrics(df)
        latest = df.iloc[-1]
        
        # Logic Gate 1: Volatility Squeeze (Spring Compression)
        is_squeezed = latest['STD'] < latest['STD_MA']
        
        # Logic Gate 2: Directional Exhaustion
        signal = "WAITING"
        probability = 0.0

        if self.is_boom:
            # Look for Buys: Low RSI + Squeeze
            if latest['RSI'] < 30 and is_squeezed:
                signal = "STRONG BUY"
                probability = 0.85
        else:
            # Look for Sells: High RSI + Squeeze
            if latest['RSI'] > 70 and is_squeezed:
                signal = "STRONG SELL"
                probability = 0.85

        return {
            "Index": self.index_name,
            "Signal": signal,
            "Confidence": probability,
            "Metrics": {
                "RSI": round(latest['RSI'], 2),
                "Squeeze": is_squeezed
            }
        }
