"""
Example: Using Deriv Trading Bot with Different Strategies

This shows how to easily swap strategies and symbols
"""
import asyncio
import logging
from src.deriv_api import DerivTradingEngine
from src.strategies import FourierStrategy

logging.basicConfig(level=logging.INFO)


async def main():
    """Example trading bot setup"""
    
    # ============================================
    # Example 1: Fourier Strategy on R_100
    # ============================================
    strategy = FourierStrategy(params={
        'lookback': 50,
        'forecast': 10,
        'smooth_period': 11,
        'stop_loss': 1.0,
        'take_profit': 2.0,
        'atr_period': 14,
        'atr_multiplier': 0.5
    })
    
    engine = DerivTradingEngine(
        strategy=strategy,
        symbol='R_100',
        stake_amount=1.0,
        candle_interval=60  # 1 minute candles
    )
    
    try:
        await engine.start()
        
        # Run for a while (or until Ctrl+C)
        await asyncio.sleep(3600)  # 1 hour
        
    finally:
        await engine.stop()


async def volatility_75_example():
    """
    Example 2: Same strategy, different symbol and parameters
    Optimized for Volatility 75 Index
    """
    strategy = FourierStrategy(params={
        'lookback': 60,  # Higher lookback for V75
        'forecast': 15,
        'smooth_period': 5,  # Less smoothing
        'stop_loss': 1.5,
        'take_profit': 3.0,
        'atr_period': 14,
        'atr_multiplier': 0.2  # Lower threshold for more trades
    })
    
    engine = DerivTradingEngine(
        strategy=strategy,
        symbol='VOLATILITY_75_1S',  # V75 1-second index
        stake_amount=2.0,
        candle_interval=60
    )
    
    await engine.start()
    await asyncio.sleep(3600)
    await engine.stop()


async def multiple_bots_example():
    """
    Example 3: Run multiple strategies simultaneously
    Each in its own task
    """
    # Bot 1: Fourier on R_100
    bot1 = DerivTradingEngine(
        strategy=FourierStrategy(params={'lookback': 50}),
        symbol='R_100',
        stake_amount=1.0
    )
    
    # Bot 2: Fourier on R_50 (different params)
    bot2 = DerivTradingEngine(
        strategy=FourierStrategy(params={'lookback': 30, 'atr_multiplier': 0.3}),
        symbol='R_50',
        stake_amount=1.0
    )
    
    # Start both
    await asyncio.gather(
        bot1.start(),
        bot2.start()
    )
    
    # Run both simultaneously
    try:
        await asyncio.sleep(7200)  # 2 hours
    finally:
        await bot1.stop()
        await bot2.stop()


if __name__ == "__main__":
    # Run basic example
    asyncio.run(main())
    
    # Or try other examples:
    # asyncio.run(volatility_75_example())
    # asyncio.run(multiple_bots_example())
