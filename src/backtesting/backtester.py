"""
Backtester
Replay historical candles through a strategy and measure performance
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
from ..deriv_api.strategy_interface import TradingStrategy, Signal, TradeSignal

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Single trade record"""
    entry_time: float
    entry_price: float
    entry_signal: str
    stake: float
    exit_time: Optional[float] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    duration_seconds: Optional[int] = None
    
    def close(self, exit_time: float, exit_price: float, reason: str):
        """Close the trade and compute PnL using stake as notional"""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = reason
        self.duration_seconds = int(exit_time - self.entry_time)
        if not self.entry_price:
            self.pnl = 0.0
            self.pnl_pct = 0.0
            return

        price_change = exit_price - self.entry_price
        ret_pct = price_change / self.entry_price

        # Notional sizing: quantity = stake / entry_price
        quantity = self.stake / self.entry_price
        if self.entry_signal == 'BUY':
            self.pnl = price_change * quantity
            self.pnl_pct = ret_pct * 100
        else:  # SELL / SHORT
            self.pnl = (-price_change) * quantity
            self.pnl_pct = (-ret_pct) * 100


@dataclass
class BacktestResult:
    """Complete backtest performance metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    total_pnl: float = 0.0
    avg_pnl_per_trade: float = 0.0
    
    max_profit: float = 0.0
    max_loss: float = 0.0
    
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    avg_trade_duration_sec: float = 0.0
    
    # Drawdown
    max_drawdown: float = 0.0
    peak_balance: float = 0.0
    
    # Additional
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': f"{self.win_rate:.2f}%",
            'total_pnl': f"${self.total_pnl:.2f}",
            'avg_pnl_per_trade': f"${self.avg_pnl_per_trade:.2f}",
            'max_profit': f"${self.max_profit:.2f}",
            'max_loss': f"${self.max_loss:.2f}",
            'largest_win': f"${self.largest_win:.2f}",
            'largest_loss': f"${self.largest_loss:.2f}",
            'avg_trade_duration_min': f"{self.avg_trade_duration_sec / 60:.2f}",
            'max_drawdown': f"{self.max_drawdown:.2f}%"
        }


class Backtester:
    """Backtest a strategy on historical data"""
    
    def __init__(self,
                 strategy: TradingStrategy,
                 initial_balance: float = 1000.0,
                 stake_per_trade: float = 10.0):
        """
        Initialize backtester
        
        Args:
            strategy: TradingStrategy instance to test
            initial_balance: Starting account balance
            stake_per_trade: Amount to stake on each trade
        """
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.stake_per_trade = stake_per_trade
        
        self.balance = initial_balance
        self.current_trade: Optional[Trade] = None
        self.closed_trades: List[Trade] = []
        self.equity_curve: List[float] = [initial_balance]
        self.timestamps: List[float] = []
        self.running_pnl: float = 0.0
        
    def run(self, df: pd.DataFrame, mtf_series: Optional[pd.Series] = None) -> BacktestResult:
        """
        Run backtest on DataFrame of candles
        
        Args:
            df: DataFrame with columns: time, open, high, low, close, datetime
            
        Returns:
            BacktestResult with metrics
        """
        logger.info(f"Starting backtest: {len(df)} candles")
        logger.info(f"Strategy: {self.strategy.name}")
        logger.info(f"Initial balance: ${self.initial_balance}")
        logger.info(f"Stake per trade: ${self.stake_per_trade}")
        
        # Reset
        self.strategy.reset()
        self.balance = self.initial_balance
        self.current_trade = None
        self.closed_trades = []
        self.equity_curve = [self.initial_balance]
        self.timestamps = []
        self.running_pnl = 0.0
        
        # Prepare dtype checks for 'time'
        has_time_col = 'time' in df.columns
        time_is_numeric = has_time_col and pd.api.types.is_numeric_dtype(df['time'])

        # Iterate through candles
        for idx, row in df.iterrows():
            # Support either numeric 'time' (epoch), string/TS 'time', or 'datetime'
            if has_time_col:
                if time_is_numeric:
                    epoch = int(row['time'])
                else:
                    epoch = int(pd.to_datetime(row['time']).timestamp())
            else:
                dt = row['datetime']
                epoch = int(pd.to_datetime(dt).timestamp())

            candle = {
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'epoch': epoch,
            }
            
            try:
                # Optional HTF candle (4H close aligned to this row)
                mtf_candle = None
                if mtf_series is not None:
                    mtf_close = mtf_series.iloc[idx]
                    if pd.notna(mtf_close):
                        mtf_candle = {'close': float(mtf_close)}

                # Update strategy
                self.strategy.update(candle, mtf_candle=mtf_candle)
                
                # Get signal
                signal = self.strategy.get_signal()
                
                # Process signal
                if signal.signal == Signal.BUY and not self.current_trade:
                    self._enter_trade(candle, 'BUY', signal)
                    
                elif signal.signal == Signal.SELL and not self.current_trade:
                    self._enter_trade(candle, 'SELL', signal)
                    
                elif signal.signal == Signal.CLOSE and self.current_trade:
                    self._close_trade(candle, 'Signal')
                    
                # Update equity curve using running PnL (balance not mutated during closes)
                self.equity_curve.append(self.initial_balance + self.running_pnl)
                self.timestamps.append(candle['epoch'])
                
            except Exception as e:
                logger.warning(f"Candle {idx} error: {e}")
                continue
        
        # Close any open trade at end
        if self.current_trade:
            last_row = df.iloc[-1]
            if has_time_col:
                if time_is_numeric:
                    last_epoch = int(last_row['time'])
                else:
                    last_epoch = int(pd.to_datetime(last_row['time']).timestamp())
            else:
                last_epoch = int(pd.to_datetime(last_row['datetime']).timestamp())
            self._close_trade({
                'close': float(last_row['close']),
                'epoch': last_epoch,
            }, 'End of backtest')
        
        # Calculate metrics
        return self._calculate_metrics()
    
    def _enter_trade(self, candle: Dict[str, Any], signal_type: str, signal_obj: Optional[TradeSignal] = None):
        """Enter a new trade"""
        entry_price = candle['close']
        self.current_trade = Trade(
            entry_time=candle['epoch'],
            entry_price=entry_price,
            entry_signal=signal_type,
            stake=self.stake_per_trade,
        )
        logger.info(f"ENTRY {signal_type} @ ${entry_price:.4f} | stake=${self.stake_per_trade:.2f}")
        # Reflect position to strategy for proper CLOSE signals
        position = {
            'type': 'LONG' if signal_type == 'BUY' else 'SHORT',
            'entry_price': entry_price,
            'entry_time': candle['epoch'],
        }
        # Optionally carry stop/target from signal metadata
        if signal_obj:
            if getattr(signal_obj, 'stop_loss', None) is not None:
                position['stop_loss'] = signal_obj.stop_loss
            if getattr(signal_obj, 'take_profit', None) is not None:
                position['take_profit'] = signal_obj.take_profit
        self.strategy.set_position(position)
        
        logger.debug(f"ENTRY {signal_type} @ ${entry_price:.4f}")
        
    def _close_trade(self, candle: Dict[str, Any], reason: str):
        """Close current trade"""
        if not self.current_trade:
            return
            
        exit_price = candle['close']
        
        # Close trade record (computes pnl based on stake)
        self.current_trade.close(candle['epoch'], exit_price, reason)
        pnl = self.current_trade.pnl or 0.0
        logger.info(
            f"EXIT {self.current_trade.entry_signal} @ ${exit_price:.4f} | "
            f"PnL=${pnl:.2f} ({self.current_trade.pnl_pct:.2f}%) | reason={reason}"
        )
        self.running_pnl += pnl
        self.closed_trades.append(self.current_trade)
        # Clear strategy position so it can generate new entries
        self.strategy.set_position(None)
        
        self.current_trade = None

    def _calculate_metrics(self) -> BacktestResult:
        result = BacktestResult()
        result.trades = self.closed_trades
        result.total_trades = len(self.closed_trades)
        result.equity_curve = self.equity_curve
        result.timestamps = self.timestamps

        result.winning_trades = sum(1 for t in self.closed_trades if t.pnl and t.pnl > 0)
        result.losing_trades = result.total_trades - result.winning_trades
        result.win_rate = (result.winning_trades / result.total_trades * 100) if result.total_trades else 0.0
        
        pnls = [t.pnl for t in self.closed_trades if t.pnl is not None]
        result.total_pnl = sum(pnls)
        result.avg_pnl_per_trade = result.total_pnl / result.total_trades if result.total_trades > 0 else 0.0
        
        result.max_profit = max(pnls) if pnls else 0.0
        result.max_loss = min(pnls) if pnls else 0.0
        
        wins = [t.pnl for t in self.closed_trades if t.pnl and t.pnl > 0]
        losses = [t.pnl for t in self.closed_trades if t.pnl and t.pnl < 0]
        
        result.largest_win = max(wins) if wins else 0.0
        result.largest_loss = min(losses) if losses else 0.0
        
        durations = [t.duration_seconds for t in self.closed_trades if t.duration_seconds]
        result.avg_trade_duration_sec = sum(durations) / len(durations) if durations else 0.0
        
        # Drawdown
        equity_array = self.equity_curve
        peak = equity_array[0] if equity_array else 0
        max_dd = 0.0
        for equity in equity_array:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100 if peak > 0 else 0
            if drawdown > max_dd:
                max_dd = drawdown
        result.max_drawdown = max_dd

        final_balance = self.initial_balance + result.total_pnl
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Backtest Complete: {self.strategy.name}")
        logger.info(f"{'='*60}")
        logger.info(f"Total Trades: {result.total_trades}")
        logger.info(f"Winners: {result.winning_trades} | Losers: {result.losing_trades}")
        logger.info(f"Win Rate: {result.win_rate:.2f}%")
        logger.info(f"Total PnL: ${result.total_pnl:.2f}")
        logger.info(f"Avg PnL/Trade: ${result.avg_pnl_per_trade:.2f}")
        logger.info(f"Max Profit: ${result.max_profit:.2f}")
        logger.info(f"Max Loss: ${result.max_loss:.2f}")
        logger.info(f"Max Drawdown: {result.max_drawdown:.2f}%")
        logger.info(f"Avg Trade Duration: {result.avg_trade_duration_sec/60:.2f} min")
        logger.info(f"Final Balance: ${final_balance:.2f}")
        logger.info(f"{'='*60}\n")
        
        return result
