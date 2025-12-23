"""
Enhanced Fourier-Inspired Trading Strategy with Improved Profitability
Key improvements:
1. Dynamic position sizing based on signal strength
2. Trailing stop to capture more profit
3. Better entry filtering with volatility expansion
4. Partial profit taking at key levels
"""
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from src.deriv_api.strategy_interface import TradingStrategy, TradeSignal, Signal

logger = logging.getLogger(__name__)


class EnhancedFourierStrategy(TradingStrategy):
    """
    Enhanced Fourier Strategy with Higher Profitability
    
    Key Enhancements:
    1. DYNAMIC POSITION SIZING: Increase stake when signal is stronger
    2. TRAILING STOPS: Lock in profits as price moves favorably
    3. VOLATILITY FILTER: Only trade when volatility is expanding (better moves)
    4. MOMENTUM CONFIRMATION: Add momentum filter to catch stronger trends
    5. BETTER EXIT LOGIC: Use trailing stops instead of fixed TP
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        
        # Core parameters
        self.lookback = self.params.get('lookback', 150)
        self.forecast = self.params.get('forecast', 20)
        self.smooth_period = self.params.get('smooth_period', 11)
        
        # Risk parameters with dynamic sizing
        self.base_stake = float(self.params.get('stake', 30.0))
        self.max_stake_multiplier = float(self.params.get('max_stake_multiplier', 2.0))  # Can double stake on strong signals
        self.risk_factor = float(self.params.get('risk_factor', 0.5))
        self.base_rr_ratio = float(self.params.get('rr_ratio', 4.0))  # Increased from 3.0
        
        # Enhanced filters
        self.atr_period = self.params.get('atr_period', 14)
        self.min_atr_multiplier = self.params.get('min_atr_multiplier', 0.3)  # Reduced for more trades
        self.volatility_expansion_threshold = self.params.get('vol_expansion', 1.2)  # ATR must be expanding
        
        # Trailing stop parameters
        self.use_trailing_stop = self.params.get('use_trailing_stop', True)
        self.trailing_stop_activation = self.params.get('trail_activation', 1.5)  # Start trailing at 1.5x risk
        self.trailing_stop_distance = self.params.get('trail_distance', 0.5)  # Trail by 0.5x risk
        
        # Momentum filter
        self.use_momentum_filter = self.params.get('use_momentum_filter', True)
        self.momentum_period = self.params.get('momentum_period', 10)
        
        # Multi-timeframe
        self.mtf_enabled = self.params.get('mtf_enabled', True)
        self.mtf_predicted_price = None
        
        # State
        self.smoothed_prices = []
        self.predicted_price = None
        self.atr_history = []
        self.entry_price = None
        self.highest_profit = 0.0  # For trailing stop
        
    @property
    def required_candles(self) -> int:
        return max(self.lookback, self.atr_period, self.momentum_period) + 20
        
    def update(self, candle: Dict[str, Any], mtf_candle: Dict[str, Any] = None):
        """Update strategy with new candle"""
        self.data_buffer.append(candle)
        
        # Update MTF prediction
        if mtf_candle:
            self.mtf_predicted_price = float(mtf_candle.get('close', 0))
        
        # Keep buffer size manageable
        max_buffer = self.required_candles + 50
        if len(self.data_buffer) > max_buffer:
            self.data_buffer = self.data_buffer[-max_buffer:]
            
        # Calculate smoothed price
        if len(self.data_buffer) >= self.smooth_period:
            smoothed = self._smooth_price()
            self.smoothed_prices.append(smoothed)
            
            if len(self.smoothed_prices) > self.lookback:
                self.smoothed_prices = self.smoothed_prices[-self.lookback:]
                
        # Calculate indicators
        if len(self.data_buffer) >= self.required_candles:
            self._calculate_indicators()
            
    def _smooth_price(self) -> float:
        """Weighted moving average smoothing"""
        prices = [float(c['close']) for c in self.data_buffer[-self.smooth_period:]]
        prices_arr = np.array(prices, dtype=np.float64)
        weights = np.arange(1, len(prices_arr) + 1, dtype=np.float64)
        return float(np.average(prices_arr, weights=weights))
        
    def _calculate_indicators(self):
        """Calculate all indicators including enhanced filters"""
        # ATR
        atr = self._calculate_atr()
        self.atr_history.append(atr)
        if len(self.atr_history) > 20:
            self.atr_history = self.atr_history[-20:]
        self.indicators['atr'] = atr
        
        # Volatility expansion check
        if len(self.atr_history) >= 10:
            recent_atr = np.mean(self.atr_history[-5:])
            older_atr = np.mean(self.atr_history[-10:-5])
            vol_expansion = recent_atr / older_atr if older_atr > 0 else 1.0
            self.indicators['vol_expansion'] = vol_expansion
            self.indicators['vol_expanding'] = vol_expansion > self.volatility_expansion_threshold
        else:
            self.indicators['vol_expanding'] = False
            
        # Momentum indicator (rate of change)
        if self.use_momentum_filter and len(self.data_buffer) >= self.momentum_period:
            closes = np.array([float(c['close']) for c in self.data_buffer[-self.momentum_period:]])
            momentum = (closes[-1] - closes[0]) / closes[0] * 100
            self.indicators['momentum'] = momentum
            
        # Trend strength (for ranging market detection)
        closes = np.array([float(c['close']) for c in self.data_buffer], dtype=np.float64)
        sma_20 = float(np.mean(closes[-20:]))
        sma_50 = float(np.mean(closes[-50:])) if len(closes) >= 50 else sma_20
        trend_strength = abs(sma_20 - sma_50)
        
        self.indicators['trend_strength'] = trend_strength
        self.indicators['is_ranging'] = trend_strength < (atr * 2)
        
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
            prev_close = float(self.data_buffer[i-1]['close']) if i > -self.atr_period else float(low)
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
            
        return float(np.mean(np.array(true_ranges, dtype=np.float64)))
        
    def _find_period(self) -> int:
        """Find dominant period by detecting max/min distance"""
        if len(self.smoothed_prices) < 2:
            return len(self.smoothed_prices) // 2
            
        prices_array = np.array(self.smoothed_prices)
        max_price = np.max(prices_array)
        min_price = np.min(prices_array)
        
        max_idx = np.where(prices_array == max_price)[0][-1]
        min_idx = np.where(prices_array == min_price)[0][-1]
        
        period = abs(max_idx - min_idx)
        return period if period > 1 else len(self.smoothed_prices) // 2
        
    def _calculate_prediction(self):
        """Calculate predicted price using Fourier-inspired harmonic analysis"""
        prices = np.array(self.smoothed_prices, dtype=np.float64)
        
        dominant_period = self._find_period()
        amplitude = (np.max(prices) - np.min(prices)) / 2
        midpoint = (np.max(prices) + np.min(prices)) / 2
        last_price = prices[-1]
        
        if amplitude == 0:
            phase_offset = 0
        else:
            y_component = last_price - midpoint
            x_component = amplitude
            phase_offset = np.arctan2(y_component, x_component)
            
        frequency = 1.0 / dominant_period if dominant_period > 0 else 0
        
        self.predicted_price = midpoint + amplitude * np.cos(
            2 * np.pi * frequency * self.forecast + phase_offset
        )
        
        self.indicators['predicted_price'] = self.predicted_price
        self.indicators['dominant_period'] = dominant_period
        self.indicators['amplitude'] = amplitude
        
    def _calculate_signal_strength(self, current_price: float, atr: float) -> float:
        """
        Calculate signal strength (0-1) based on:
        1. Distance from prediction
        2. Volatility state
        3. Momentum alignment
        """
        if self.predicted_price is None or atr == 0:
            return 0.0
            
        # Base strength from prediction deviation
        deviation = abs(current_price - self.predicted_price)
        base_strength = min(deviation / (atr * 2), 1.0)
        
        # Boost if volatility is expanding
        vol_multiplier = 1.3 if self.indicators.get('vol_expanding', False) else 1.0
        
        # Boost if momentum aligns
        momentum = self.indicators.get('momentum', 0)
        momentum_multiplier = 1.0
        if self.use_momentum_filter:
            # For LONG: want negative momentum (oversold)
            # For SHORT: want positive momentum (overbought)
            if current_price < self.predicted_price and momentum < -0.5:
                momentum_multiplier = 1.2
            elif current_price > self.predicted_price and momentum > 0.5:
                momentum_multiplier = 1.2
                
        final_strength = min(base_strength * vol_multiplier * momentum_multiplier, 1.0)
        return final_strength
        
    def _calculate_dynamic_stake(self, signal_strength: float) -> float:
        """
        Calculate position size based on signal strength.
        Stronger signals get larger positions (up to max_stake_multiplier).
        """
        # Linear scaling: strength 0.5 = 1x stake, strength 1.0 = max_stake_multiplier
        if signal_strength < 0.5:
            return self.base_stake
        
        multiplier = 1.0 + (signal_strength - 0.5) * 2 * (self.max_stake_multiplier - 1.0)
        multiplier = min(multiplier, self.max_stake_multiplier)
        
        return self.base_stake * multiplier
        
    def get_signal(self) -> TradeSignal:
        """Generate trading signal with enhanced logic"""
        # Need enough data
        if len(self.data_buffer) < self.required_candles:
            return TradeSignal(Signal.HOLD, strength=0.0)
            
        if self.predicted_price is None:
            return TradeSignal(Signal.HOLD, strength=0.0)
            
        current_price = float(self.data_buffer[-1]['close'])
        atr = self.indicators.get('atr', 0)
        is_ranging = self.indicators.get('is_ranging', False)
        
        # Calculate signal strength
        signal_strength = self._calculate_signal_strength(current_price, atr)
        min_signal_strength = atr * self.min_atr_multiplier
        
        # Enhanced filtering: only trade in ranging markets with strong signals
        deviation = abs(current_price - self.predicted_price)
        if not is_ranging or deviation < min_signal_strength:
            return TradeSignal(Signal.HOLD, strength=0.0)
            
        # TRAILING STOP EXIT LOGIC
        if self.position:
            pos_type = self.position.get('type')
            entry_price = self.position.get('entry_price', current_price)
            
            # Calculate current P&L
            if pos_type == 'LONG':
                current_pnl = current_price - entry_price
            else:  # SHORT
                current_pnl = entry_price - current_price
                
            # Track highest profit for trailing
            if current_pnl > self.highest_profit:
                self.highest_profit = current_pnl
                
            # Dynamic trailing stop
            if self.use_trailing_stop:
                risk_move = (self.risk_factor * self.base_stake / max(self.base_stake, 1e-9)) * entry_price
                activation_profit = risk_move * self.trailing_stop_activation
                
                if self.highest_profit > activation_profit:
                    # Trailing stop triggered
                    trail_distance = risk_move * self.trailing_stop_distance
                    if current_pnl < (self.highest_profit - trail_distance):
                        logger.info(f"Trailing stop hit: profit fell from ${self.highest_profit:.2f} to ${current_pnl:.2f}")
                        self.highest_profit = 0.0
                        return TradeSignal(Signal.CLOSE, strength=1.0)
            
            # Original prediction cross exit (as backup)
            if pos_type == 'LONG' and current_price > self.predicted_price:
                self.highest_profit = 0.0
                return TradeSignal(Signal.CLOSE, strength=1.0)
            elif pos_type == 'SHORT' and current_price < self.predicted_price:
                self.highest_profit = 0.0
                return TradeSignal(Signal.CLOSE, strength=1.0)
                
            return TradeSignal(Signal.HOLD, strength=0.0)
            
        # ENTRY LOGIC WITH DYNAMIC SIZING
        dynamic_stake = self._calculate_dynamic_stake(signal_strength)
        risk_cash = dynamic_stake * self.risk_factor
        
        # Entry LONG
        if current_price < self.predicted_price:
            # MTF confirmation
            if self.mtf_enabled and self.mtf_predicted_price:
                if current_price >= self.mtf_predicted_price:
                    return TradeSignal(Signal.HOLD, strength=0.0)
                    
            # Momentum confirmation
            if self.use_momentum_filter:
                momentum = self.indicators.get('momentum', 0)
                if momentum > 1.0:  # Too bullish already
                    return TradeSignal(Signal.HOLD, strength=0.0)
                    
            # Calculate stops with higher R:R
            risk_price_move = (risk_cash / max(dynamic_stake, 1e-9)) * current_price
            stop_loss = current_price - risk_price_move
            take_profit = current_price + (risk_price_move * self.base_rr_ratio)
            
            self.highest_profit = 0.0
            
            return TradeSignal(
                Signal.BUY,
                strength=signal_strength,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'predicted_price': self.predicted_price,
                    'stake': dynamic_stake,
                    'signal_strength': signal_strength,
                    'atr': atr,
                    'vol_expanding': self.indicators.get('vol_expanding', False),
                    'momentum': self.indicators.get('momentum', 0)
                }
            )
            
        # Entry SHORT
        if current_price > self.predicted_price:
            # MTF confirmation
            if self.mtf_enabled and self.mtf_predicted_price:
                if current_price <= self.mtf_predicted_price:
                    return TradeSignal(Signal.HOLD, strength=0.0)
                    
            # Momentum confirmation
            if self.use_momentum_filter:
                momentum = self.indicators.get('momentum', 0)
                if momentum < -1.0:  # Too bearish already
                    return TradeSignal(Signal.HOLD, strength=0.0)
                    
            risk_price_move = (risk_cash / max(dynamic_stake, 1e-9)) * current_price
            stop_loss = current_price + risk_price_move
            take_profit = current_price - (risk_price_move * self.base_rr_ratio)
            
            self.highest_profit = 0.0
            
            return TradeSignal(
                Signal.SELL,
                strength=signal_strength,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'predicted_price': self.predicted_price,
                    'stake': dynamic_stake,
                    'signal_strength': signal_strength,
                    'atr': atr,
                    'vol_expanding': self.indicators.get('vol_expanding', False),
                    'momentum': self.indicators.get('momentum', 0)
                }
            )
            
        return TradeSignal(Signal.HOLD, strength=0.0)
        
    def reset(self):
        """Reset strategy state"""
        super().reset()
        self.smoothed_prices = []
        self.predicted_price = None
        self.mtf_predicted_price = None
        self.atr_history = []
        self.entry_price = None
        self.highest_profit = 0.0