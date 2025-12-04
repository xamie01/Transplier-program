"""
Moving average indicators.

This module provides implementations of various moving average indicators.
"""

from typing import List, Union
import numpy as np


class SMA:
    """Simple Moving Average indicator."""
    
    @staticmethod
    def calculate(data: Union[List[float], np.ndarray], period: int) -> np.ndarray:
        """
        Calculate Simple Moving Average.
        
        Args:
            data: Price data
            period: Period for the moving average
            
        Returns:
            Array of SMA values
        """
        data_array = np.array(data)
        sma = np.full(len(data_array), np.nan)
        
        for i in range(period - 1, len(data_array)):
            sma[i] = np.mean(data_array[i - period + 1:i + 1])
        
        return sma
    
    @staticmethod
    def calculate_single(data: Union[List[float], np.ndarray], period: int) -> float:
        """
        Calculate SMA for the most recent data point.
        
        Args:
            data: Price data (must have at least 'period' elements)
            period: Period for the moving average
            
        Returns:
            Single SMA value
        """
        if len(data) < period:
            return np.nan
        return np.mean(data[-period:])


class EMA:
    """Exponential Moving Average indicator."""
    
    @staticmethod
    def calculate(data: Union[List[float], np.ndarray], period: int) -> np.ndarray:
        """
        Calculate Exponential Moving Average.
        
        Args:
            data: Price data
            period: Period for the moving average
            
        Returns:
            Array of EMA values
        """
        data_array = np.array(data)
        ema = np.full(len(data_array), np.nan)
        
        # Calculate multiplier
        multiplier = 2 / (period + 1)
        
        # First EMA is SMA
        ema[period - 1] = np.mean(data_array[:period])
        
        # Calculate remaining EMAs
        for i in range(period, len(data_array)):
            ema[i] = (data_array[i] - ema[i - 1]) * multiplier + ema[i - 1]
        
        return ema
    
    @staticmethod
    def calculate_single(data: Union[List[float], np.ndarray], period: int, 
                        previous_ema: float = None) -> float:
        """
        Calculate EMA for the most recent data point.
        
        Args:
            data: Price data
            period: Period for the moving average
            previous_ema: Previous EMA value (if available)
            
        Returns:
            Single EMA value
        """
        if len(data) < period:
            return np.nan
        
        multiplier = 2 / (period + 1)
        
        if previous_ema is None:
            # Calculate initial EMA from SMA
            return np.mean(data[-period:])
        
        return (data[-1] - previous_ema) * multiplier + previous_ema


class WMA:
    """Weighted Moving Average indicator."""
    
    @staticmethod
    def calculate(data: Union[List[float], np.ndarray], period: int) -> np.ndarray:
        """
        Calculate Weighted Moving Average.
        
        Args:
            data: Price data
            period: Period for the moving average
            
        Returns:
            Array of WMA values
        """
        data_array = np.array(data)
        wma = np.full(len(data_array), np.nan)
        
        # Calculate weights
        weights = np.arange(1, period + 1)
        weights_sum = np.sum(weights)
        
        for i in range(period - 1, len(data_array)):
            window = data_array[i - period + 1:i + 1]
            wma[i] = np.sum(window * weights) / weights_sum
        
        return wma
