"""
Fourier-Inspired Trading Strategy
Converted from Pine Script to Python for Deriv API trading

Original: fourir.pine
Uses period detection and harmonic analysis to predict price movements
"""
import numpy as np
from typing import Dict, Any, List
import logging
from ..deriv_api.strategy_interface import TradingStrategy, TradeSignal, Signal

logger = logging.getLogger(__name__)


class FourierStrategy(TradingStrategy):
    """
    Fourier-based strategy using period detection and harmonic analysis
    
    Strategy Logic:
    1. Smooth prices with weighted moving average
    2. Detect dominant period by finding max/min distance
    3. Calculate amplitude, midpoint, phase
    4. Predict future price using sine wave projection
    5. Enter when price deviates from prediction in ranging markets
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        
        # Strategy parameters (optimized for synthetic indices)
        self.lookback = self.params.get('lookback', 150)
        self.forecast = self.params.get('forecast', 20)
        self.smooth_period = self.params.get('smooth_period', 11)
        # Risk model: fixed cash risk based on stake, not percentages
        self.stake = float(self.params.get('stake', 30.0))
        self.risk_cash = float(self.params.get('risk_cash', self.stake * 0.5))
        self.rr_ratio = float(self.params.get('rr_ratio', 3.0))
        self.atr_period = self.params.get('atr_period', 14)
        self.atr_multiplier = self.params.get('atr_multiplier', 0.5)
        
        # Multi-timeframe (4h confirmation)
        self.mtf_enabled = self.params.get('mtf_enabled', False)
        self.mtf_predicted_price = None  # 4h prediction for trend confirmation
        
        # State
        self.smoothed_prices = []
        self.predicted_price = None
        self.entry_price = None
        
    @property
    def required_candles(self) -> int:
        return max(self.lookback, self.atr_period) + 20
        
    def update(self, candle: Dict[str, Any], mtf_candle: Dict[str, Any] = None):
        """Update strategy with new candle (and optional 4h candle for MTF confirmation)"""
        # Add to buffer
        self.data_buffer.append(candle)
        
        # Update 4h prediction if provided
        if mtf_candle:
            mtf_close = float(mtf_candle.get('close', 0))
            self.mtf_predicted_price = mtf_close
        
        # Keep only required candles
        max_buffer = self.required_candles + 50
        if len(self.data_buffer) > max_buffer:
            self.data_buffer = self.data_buffer[-max_buffer:]
            
        # Calculate smoothed price
        if len(self.data_buffer) >= self.smooth_period:
            smoothed = self._smooth_price()
            self.smoothed_prices.append(smoothed)
            
            # Keep smoothed prices at lookback size
            if len(self.smoothed_prices) > self.lookback:
                self.smoothed_prices = self.smoothed_prices[-self.lookback:]
                
        # Calculate indicators when enough data
        if len(self.data_buffer) >= self.required_candles:
            self._calculate_indicators()
            
    def _smooth_price(self) -> float:
        """Weighted moving average smoothing"""
        prices = [float(c['close']) for c in self.data_buffer[-self.smooth_period:]]
        prices_arr = np.array(prices, dtype=np.float64)
        weights = np.arange(1, len(prices_arr) + 1, dtype=np.float64)
        return float(np.average(prices_arr, weights=weights))
        
    def _calculate_indicators(self):
        """Calculate all indicators"""
        # ATR
        self.indicators['atr'] = self._calculate_atr()
        
        # Trend strength (SMA difference)
        closes = np.array([float(c['close']) for c in self.data_buffer], dtype=np.float64)
        sma_20 = float(np.mean(closes[-20:]))
        sma_50 = float(np.mean(closes[-50:])) if len(closes) >= 50 else sma_20
        trend_strength = abs(sma_20 - sma_50)
        
        self.indicators['trend_strength'] = trend_strength
        self.indicators['is_ranging'] = trend_strength < (self.indicators['atr'] * 2)
        
        # Fourier prediction
        if len(self.smoothed_prices) >= self.lookback:
            self._calculate_prediction()
            
    def _calculate_atr(self) -> float:
        """Calculate Average True Range"""
        if len(self.data_buffer) < self.atr_period:
            return 0.0
            
        true_ranges = []
        for i in range(-self.atr_period, 0):
            high = float(self.data_buffer[i]['high'])
            low = float(self.data_buffer[i]['low'])
            prev_close = float(self.data_buffer[i-1]['close']) if i > 0 else float(low)
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
            
        return float(np.mean(np.array(true_ranges, dtype=np.float64)))
        
    def _find_period(self) -> int:
        """Find dominant period by detecting max/min distance"""
        if len(self.smoothed_prices) < 2:
            return len(self.smoothed_prices) // 2
            
        prices_array = np.array(self.smoothed_prices)
        max_price = np.max(prices_array)
        min_price = np.min(prices_array)
        
        # Find indices of max and min
        max_idx = np.where(prices_array == max_price)[0][-1]  # Last occurrence
        min_idx = np.where(prices_array == min_price)[0][-1]
        
        period = abs(max_idx - min_idx)
        return period if period > 1 else len(self.smoothed_prices) // 2
        
    def _calculate_prediction(self):
        """Calculate predicted price using Fourier-inspired harmonic analysis"""
        prices = np.array(self.smoothed_prices, dtype=np.float64)
        
        # Find dominant period
        dominant_period = self._find_period()
        
        # Calculate amplitude and midpoint
        amplitude = (np.max(prices) - np.min(prices)) / 2
        midpoint = (np.max(prices) + np.min(prices)) / 2
        last_price = prices[-1]
        
        # Phase calculation
        if amplitude == 0:
            phase_offset = 0
        else:
            y_component = last_price - midpoint
            x_component = amplitude
            phase_offset = np.arctan2(y_component, x_component)
            
        # Frequency
        frequency = 1.0 / dominant_period if dominant_period > 0 else 0
        
        # Predict future price
        self.predicted_price = midpoint + amplitude * np.cos(
            2 * np.pi * frequency * self.forecast + phase_offset
        )
        
        self.indicators['predicted_price'] = self.predicted_price
        self.indicators['dominant_period'] = dominant_period
        self.indicators['amplitude'] = amplitude
        
    def get_signal(self) -> TradeSignal:
        """Generate trading signal"""
        # Need enough data
        if len(self.data_buffer) < self.required_candles:
            return TradeSignal(Signal.HOLD, strength=0.0)
            
        # Need prediction
        if self.predicted_price is None:
            return TradeSignal(Signal.HOLD, strength=0.0)
            
        current_price = float(self.data_buffer[-1]['close'])
        atr = self.indicators.get('atr', 0)
        is_ranging = self.indicators.get('is_ranging', False)
        
        # Signal strength based on distance from prediction
        signal_strength = abs(current_price - self.predicted_price)
        min_signal_strength = atr * self.atr_multiplier

        # Only trade in ranging markets with strong enough signal
        if not is_ranging or signal_strength < min_signal_strength:
            return TradeSignal(Signal.HOLD, strength=0.0)

        # Close position: Exit on prediction cross (cycle complete - mean reversion signal)
        # SL/TP calculated for risk limits but don't trigger exits
        if self.position:
            pos_type = self.position.get('type')

            if pos_type == 'LONG':
                # Prediction cross - cycle complete (mean reversion)
                if current_price > self.predicted_price:
                    return TradeSignal(Signal.CLOSE, strength=1.0)
                return TradeSignal(Signal.HOLD, strength=0.0)

            if pos_type == 'SHORT':
                # Prediction cross - cycle complete (mean reversion)
                if current_price < self.predicted_price:
                    return TradeSignal(Signal.CLOSE, strength=1.0)
                return TradeSignal(Signal.HOLD, strength=0.0)

        # Entry LONG: price below prediction + optional 4h uptrend confirmation
        if current_price < self.predicted_price:
            if self.mtf_enabled and self.mtf_predicted_price:
                if current_price >= self.mtf_predicted_price:
                    return TradeSignal(Signal.HOLD, strength=0.0)  # No 4h confirmation

            # Fixed cash risk: convert desired cash loss to price distance using notional sizing
            risk_price_move = (self.risk_cash / max(self.stake, 1e-9)) * current_price
            stop_loss = current_price - risk_price_move
            take_profit = current_price + (risk_price_move * self.rr_ratio)
            strength = min(signal_strength / (atr * 2), 1.0)
            return TradeSignal(
                Signal.BUY,
                strength=strength,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'predicted_price': self.predicted_price,
                    'current_price': current_price,
                    'period': self.indicators.get('dominant_period'),
                    'amplitude': self.indicators.get('amplitude'),
                    'atr': atr,
                    'mtf_confirmed': True
                }
            )

        # Entry SHORT: price above prediction + optional 4h downtrend confirmation
        if current_price > self.predicted_price:
            if self.mtf_enabled and self.mtf_predicted_price:
                if current_price <= self.mtf_predicted_price:
                    return TradeSignal(Signal.HOLD, strength=0.0)  # No 4h confirmation

            risk_price_move = (self.risk_cash / max(self.stake, 1e-9)) * current_price
            stop_loss = current_price + risk_price_move
            take_profit = current_price - (risk_price_move * self.rr_ratio)
            strength = min(signal_strength / (atr * 2), 1.0)
            return TradeSignal(
                Signal.SELL,
                strength=strength,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'predicted_price': self.predicted_price,
                    'current_price': current_price,
                    'period': self.indicators.get('dominant_period'),
                    'amplitude': self.indicators.get('amplitude'),
                    'atr': atr,
                    'mtf_confirmed': True
                }
            )

        return TradeSignal(Signal.HOLD, strength=0.0)
    
    def reset(self):
        """Reset strategy state for new backtest or session"""
        super().reset()
        self.smoothed_prices = []
        self.predicted_price = None
        self.mtf_predicted_price = None
        self.entry_price = None
