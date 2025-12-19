"""
Deriv API WebSocket Client
Handles connection and API calls to Deriv
"""
import asyncio
import json
import websockets
from typing import Dict, Any, Optional, Callable, DefaultDict, List
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class DerivAPIClient:
    """WebSocket client for Deriv API"""
    
    def __init__(self, app_id: str = "1089", api_token: Optional[str] = None):
        """
        Initialize Deriv API client
        
        Args:
            app_id: Deriv app ID (default uses demo)
            api_token: API token for your account (required for real trading)
        """
        self.app_id = app_id
        self.api_token = api_token
        self.ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"
        self.ws = None
        self.authorized = False
        # Pending request correlation by req_id
        self._pending: Dict[int, asyncio.Future] = {}
        self._next_req_id: int = 1
        self._recv_task: Optional[asyncio.Task] = None
        # Streaming callbacks
        self._tick_callbacks: DefaultDict[str, List[Callable]] = defaultdict(list)
        self._candle_callbacks: DefaultDict[str, List[Callable]] = defaultdict(list)
        
    async def connect(self):
        """Establish WebSocket connection"""
        self.ws = await websockets.connect(self.ws_url)
        logger.info(f"Connected to Deriv API: {self.ws_url}")
        
        # Start receiver loop
        self._recv_task = asyncio.create_task(self._receiver())

        # Authorize if token provided
        if self.api_token:
            await self.authorize()
            
    async def authorize(self):
        """Authorize with API token"""
        request = {
            "authorize": self.api_token
        }
        response = await self.send_request(request)
        if 'error' in response:
            raise Exception(f"Authorization failed: {response['error']['message']}")
        self.authorized = True
        logger.info("Successfully authorized")
        return response
        
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request and wait for response via receiver routing"""
        # Assign unique req_id for correlation
        req_id = self._next_req_id
        self._next_req_id += 1
        request = {**request, "req_id": req_id}
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[req_id] = fut
        await self.ws.send(json.dumps(request))
        try:
            response = await asyncio.wait_for(fut, timeout=15)
            return response
        finally:
            self._pending.pop(req_id, None)
        
    async def subscribe_ticks(self, symbol: str, callback: Callable):
        """
        Subscribe to tick stream for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'R_50', 'R_100', 'VOLATILITY_75_1S')
            callback: Function to call with each tick
        """
        request = {
            "ticks": symbol,
            "subscribe": 1
        }
        # Register callback and send subscribe
        self._tick_callbacks[symbol].append(callback)
        await self.send_request(request)
        
    async def subscribe_candles(self, symbol: str, interval: int, callback: Callable):
        """
        Subscribe to candlestick stream
        
        Args:
            symbol: Trading symbol
            interval: Candle interval in seconds (60, 120, 180, 300, 600, 900, 1800, 3600, etc.)
            callback: Function to call with each candle
        """
        request = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": 1000,
            "end": "latest",
            "start": 1,
            "style": "candles",
            "granularity": interval,
            "subscribe": 1
        }
        self._candle_callbacks[symbol].append(callback)
        await self.send_request(request)
        
    async def _receiver(self):
        """Single receiver loop routing messages to pending requests or callbacks"""
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)

                # Route to pending request by req_id if present
                req_id = data.get('req_id')
                if req_id is not None and req_id in self._pending:
                    fut = self._pending.get(req_id)
                    if fut and not fut.done():
                        fut.set_result(data)
                    continue

                # Stream: ticks
                if 'tick' in data:
                    tick = data['tick']
                    symbol = tick.get('symbol')
                    for cb in self._tick_callbacks.get(symbol, []):
                        await cb(tick)
                    continue

                # Stream: initial candles batch
                if 'candles' in data:
                    candles = data['candles']
                    symbol = data.get('echo_req', {}).get('ticks_history')
                    for candle in candles:
                        for cb in self._candle_callbacks.get(symbol, []):
                            await cb(candle)
                    continue

                # Stream: ohlc update
                if 'ohlc' in data:
                    ohlc = data['ohlc']
                    symbol = data.get('echo_req', {}).get('ticks_history') or ohlc.get('symbol')
                    for cb in self._candle_callbacks.get(symbol, []):
                        await cb(ohlc)
                    continue

                if 'error' in data:
                    logger.error(f"Unrouted error: {data['error']}")
        except Exception as e:
            logger.error(f"Receiver error: {e}")
            
    async def buy_contract(self, 
                          symbol: str,
                          contract_type: str,
                          amount: float,
                          duration: int,
                          duration_unit: str = 't',
                          basis: str = 'stake',
                          currency: str = 'USD') -> Dict[str, Any]:
        """
        Buy a contract
        
        Args:
            symbol: Trading symbol (e.g., 'R_100')
            contract_type: 'CALL', 'PUT', etc.
            amount: Stake amount in account currency
            duration: Contract duration
            duration_unit: 's' (seconds), 'm' (minutes), 'h' (hours), 'd' (days), 't' (ticks)
            basis: 'stake' or 'payout'
            
        Returns:
            Contract purchase response
        """
        if not self.authorized:
            raise Exception("Not authorized. Provide API token.")
            
        request = {
            "buy": 1,
            "price": amount,
            "parameters": {
                "contract_type": contract_type,
                "symbol": symbol,
                "duration": duration,
                "duration_unit": duration_unit,
                "basis": basis,
                "amount": amount,
                "currency": currency
            }
        }
        
        response = await self.send_request(request)
        
        if 'error' in response:
            logger.error(f"Buy failed: {response['error']}")
            raise Exception(response['error']['message'])
            
        logger.info(f"Contract purchased: {response.get('buy', {}).get('contract_id')}")
        return response
        
    async def get_proposal(self,
                          symbol: str,
                          contract_type: str,
                          amount: float,
                          duration: int,
                          duration_unit: str = 't',
                          basis: str = 'stake',
                          currency: str = 'USD') -> Dict[str, Any]:
        """
        Get contract proposal (price before buying)
        
        Returns:
            Proposal with expected payout, ask price, etc.
        """
        request = {
            "proposal": 1,
            "amount": amount,
            "basis": basis,
            "contract_type": contract_type,
            "currency": currency,
            "duration": duration,
            "duration_unit": duration_unit,
            "symbol": symbol
        }
        
        response = await self.send_request(request)
        if 'error' in response:
            logger.error(f"Proposal error: {response['error']}")
            
        return response
        
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        if not self.authorized:
            raise Exception("Not authorized")
            
        response = await self.send_request({"balance": 1, "subscribe": 0})
        return response
        
    async def close(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            logger.info("Disconnected from Deriv API")
        if self._recv_task:
            self._recv_task.cancel()
