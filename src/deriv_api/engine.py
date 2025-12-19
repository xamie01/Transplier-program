"""
Deriv Trading Engine
Orchestrates API client, strategy, and trade execution
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from .client import DerivAPIClient
from .strategy_interface import TradingStrategy, Signal

logger = logging.getLogger(__name__)


class DerivTradingEngine:
    """
    Main trading engine that connects strategy to Deriv API
    """
    
    def __init__(self,
                 strategy: TradingStrategy,
                 symbol: str,
                 app_id: str = "1089",
                 api_token: Optional[str] = None,
                 stake_amount: float = 1.0,
                 candle_interval: int = 60,
                 demo: bool = False,
                 proposal_min_interval_sec: float = 1.5):
        """
        Initialize trading engine
        
        Args:
            strategy: TradingStrategy instance
            symbol: Symbol to trade (e.g., 'R_100', 'VOLATILITY_75_1S')
            app_id: Deriv app ID
            api_token: API token (required for real trading)
            stake_amount: Amount to stake per trade
            candle_interval: Candle interval in seconds (60, 120, 300, etc.)
        """
        self.strategy = strategy
        self.symbol = symbol
        self.stake_amount = stake_amount
        self.candle_interval = candle_interval
        
        self.client = DerivAPIClient(app_id=app_id, api_token=api_token)
        self.current_position = None
        self.trade_history = []
        self.running = False
        self.demo = demo
        self._last_proposal_ts: float = 0.0
        self._proposal_min_interval = proposal_min_interval_sec
        
        # Stats
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
    async def start(self):
        """Start the trading engine"""
        logger.info(f"Starting trading engine for {self.symbol}")
        logger.info(f"Strategy: {self.strategy.name}")
        logger.info(f"Stake: ${self.stake_amount}")
        
        # Connect to Deriv
        await self.client.connect()
        
        # Check balance
        if self.client.authorized:
            balance = await self.client.get_balance()
            logger.info(f"Account balance: {balance.get('balance', {})}")
        
        # Subscribe to candles
        await self.client.subscribe_candles(
            self.symbol,
            self.candle_interval,
            self.on_candle
        )
        
        self.running = True
        logger.info("Trading engine started")
        
    async def stop(self):
        """Stop the trading engine"""
        logger.info("Stopping trading engine...")
        self.running = False
        await self.client.close()
        self.print_stats()
        
    async def on_candle(self, candle: Dict[str, Any]):
        """
        Process incoming candle and execute trading logic
        
        Args:
            candle: Candle data from Deriv API
        """
        if not self.running:
            return
            
        try:
            # Update strategy with new candle
            self.strategy.update(candle)
            
            # Get signal from strategy
            signal = self.strategy.get_signal()
            
            logger.debug(f"Candle: O={candle.get('open')} H={candle.get('high')} "
                        f"L={candle.get('low')} C={candle.get('close')} | "
                        f"Signal: {signal.signal.value} (strength: {signal.strength:.2f})")
            
            # Execute trades based on signal
            await self.execute_signal(signal, candle)
            
        except Exception as e:
            logger.error(f"Error processing candle: {e}", exc_info=True)
            
    async def execute_signal(self, signal, candle: Dict[str, Any]):
        """
        Execute trading signal
        
        Args:
            signal: TradeSignal from strategy
            candle: Current candle data
        """
        # If we have a position and get CLOSE signal
        if self.current_position and signal.signal == Signal.CLOSE:
            logger.info(f"CLOSE signal received - position will close automatically")
            # Deriv contracts close automatically at expiry
            self.current_position = None
            return
            
        # Don't enter new position if already in one
        if self.current_position:
            return
            
        # Execute BUY signal
        if signal.signal == Signal.BUY:
            await self.buy_contract('CALL', signal, candle)
            
        # Execute SELL signal  
        elif signal.signal == Signal.SELL:
            await self.buy_contract('PUT', signal, candle)
            
    async def buy_contract(self, 
                          contract_type: str,
                          signal,
                          candle: Dict[str, Any]):
        """
        Buy a contract
        
        Args:
            contract_type: 'CALL' or 'PUT'
            signal: TradeSignal
            candle: Current candle
        """
        if self.demo or not self.client.authorized:
            logger.info(f"DEMO: {contract_type} would be opened | Stake: ${self.stake_amount} | Signal: {signal.strength:.2f}")
            return
            
        try:
            # Determine duration (5 ticks for quick trades, can be adjusted)
            duration = 5
            duration_unit = 't'
            
            # Throttle proposals to avoid rate limits
            now = asyncio.get_event_loop().time()
            if now - self._last_proposal_ts < self._proposal_min_interval:
                await asyncio.sleep(self._proposal_min_interval - (now - self._last_proposal_ts))
            self._last_proposal_ts = asyncio.get_event_loop().time()

            # Get proposal first
            proposal = await self.client.get_proposal(
                symbol=self.symbol,
                contract_type=contract_type,
                amount=self.stake_amount,
                duration=duration,
                duration_unit=duration_unit
            )
            
            if 'error' in proposal:
                logger.error(f"Proposal error: {proposal['error']}")
                return
                
            payout = proposal.get('proposal', {}).get('payout', 0)
            logger.info(f"Opening {contract_type} | "
                       f"Stake: ${self.stake_amount} | "
                       f"Potential payout: ${payout:.2f} | "
                       f"Signal strength: {signal.strength:.2f}")
            
            # Buy contract
            response = await self.client.buy_contract(
                symbol=self.symbol,
                contract_type=contract_type,
                amount=self.stake_amount,
                duration=duration,
                duration_unit=duration_unit
            )
            
            self.current_position = {
                'contract_id': response.get('buy', {}).get('contract_id'),
                'type': contract_type,
                'stake': self.stake_amount,
                'entry_price': candle.get('close'),
                'timestamp': datetime.now()
            }
            
            self.total_trades += 1
            self.trade_history.append(self.current_position)
            
        except Exception as e:
            logger.error(f"Failed to buy contract: {e}", exc_info=True)
            
    def print_stats(self):
        """Print trading statistics"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        logger.info("=" * 50)
        logger.info(f"Trading Statistics for {self.strategy.name}")
        logger.info("=" * 50)
        logger.info(f"Total Trades: {self.total_trades}")
        logger.info(f"Winning Trades: {self.winning_trades}")
        logger.info(f"Losing Trades: {self.losing_trades}")
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info("=" * 50)
