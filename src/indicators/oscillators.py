"""
Oscillator indicators.

This module provides implementations of various oscillator indicators
like RSI, MACD, Stochastic, etc.
"""

from typing import List, Union, Tuple
import numpy as np


class RSI:
    """Relative Strength Index indicator."""
    
    @staticmethod
    def calculate(data: Union[List[float], np.ndarray], period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index.
        
        Args:
            data: Price data
            period: Period for RSI calculation (default: 14)
            
        Returns:
            Array of RSI values
        """
        data_array = np.array(data)
        rsi = np.full(len(data_array), np.nan)
        
        # Calculate price changes
        deltas = np.diff(data_array)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gain = np.full(len(data_array), np.nan)
        avg_loss = np.full(len(data_array), np.nan)
        
        # First average is simple average
        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])
        
        # Subsequent averages use smoothing
        for i in range(period + 1, len(data_array)):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_single(data: Union[List[float], np.ndarray], period: int = 14) -> float:
        """
        Calculate RSI for the most recent data point.
        
        Args:
            data: Price data
            period: Period for RSI calculation
            
        Returns:
            Single RSI value
        """
        if len(data) < period + 1:
            return np.nan
        
        result = RSI.calculate(data, period)
        return result[-1]


class MACD:
    """Moving Average Convergence Divergence indicator."""
    
    @staticmethod
    def calculate(data: Union[List[float], np.ndarray], 
                 fast_period: int = 12, 
                 slow_period: int = 26, 
                 signal_period: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate MACD indicator.
        
        Args:
            data: Price data
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        from src.indicators.moving_averages import EMA
        
        data_array = np.array(data)
        
        # Calculate fast and slow EMAs
        fast_ema = EMA.calculate(data_array, fast_period)
        slow_ema = EMA.calculate(data_array, slow_period)
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate signal line (EMA of MACD)
        # Remove NaN values for signal calculation
        valid_macd = macd_line[~np.isnan(macd_line)]
        if len(valid_macd) >= signal_period:
            signal_line = np.full(len(data_array), np.nan)
            signal_values = EMA.calculate(valid_macd, signal_period)
            
            # Place signal values back in correct positions
            start_idx = len(data_array) - len(valid_macd)
            signal_line[start_idx:] = signal_values
        else:
            signal_line = np.full(len(data_array), np.nan)
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_single(data: Union[List[float], np.ndarray],
                        fast_period: int = 12,
                        slow_period: int = 26,
                        signal_period: int = 9) -> Tuple[float, float, float]:
        """
        Calculate MACD for the most recent data point.
        
        Args:
            data: Price data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            
        Returns:
            Tuple of (macd_value, signal_value, histogram_value)
        """
        macd_line, signal_line, histogram = MACD.calculate(
            data, fast_period, slow_period, signal_period
        )
        
        return macd_line[-1], signal_line[-1], histogram[-1]


class Stochastic:
    """Stochastic Oscillator indicator."""
    
    @staticmethod
    def calculate(high: Union[List[float], np.ndarray],
                 low: Union[List[float], np.ndarray],
                 close: Union[List[float], np.ndarray],
                 period: int = 14,
                 smooth_k: int = 3,
                 smooth_d: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Look-back period (default: 14)
            smooth_k: K smoothing period (default: 3)
            smooth_d: D smoothing period (default: 3)
            
        Returns:
            Tuple of (%K, %D)
        """
        high_array = np.array(high)
        low_array = np.array(low)
        close_array = np.array(close)
        
        # Calculate raw stochastic
        k_raw = np.full(len(close_array), np.nan)
        
        for i in range(period - 1, len(close_array)):
            highest_high = np.max(high_array[i - period + 1:i + 1])
            lowest_low = np.min(low_array[i - period + 1:i + 1])
            
            if highest_high - lowest_low != 0:
                k_raw[i] = 100 * (close_array[i] - lowest_low) / (highest_high - lowest_low)
            else:
                k_raw[i] = 50  # Neutral value when range is 0
        
        # Smooth %K
        from src.indicators.moving_averages import SMA
        k_smooth = SMA.calculate(k_raw, smooth_k)
        
        # Calculate %D (SMA of %K)
        d = SMA.calculate(k_smooth, smooth_d)
        
        return k_smooth, d
