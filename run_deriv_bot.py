#!/usr/bin/env python3
"""
Deriv Trading Bot Runner

Example usage:
    # Run with default config
    python run_deriv_bot.py
    
    # Run with custom config
    python run_deriv_bot.py --config my_config.yaml
    
    # Override symbol
    python run_deriv_bot.py --symbol VOLATILITY_75_1S
    
    # Override strategy
    python run_deriv_bot.py --strategy EOVIEStrategy
"""
import asyncio
import argparse
import logging
import os
import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.deriv_api import DerivTradingEngine
from src.strategies import FourierStrategy


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_logging(config: dict):
    """Setup logging configuration"""
    log_level = getattr(logging, config.get('logging', {}).get('level', 'INFO'))
    log_file = config.get('logging', {}).get('file', 'trading.log')
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_strategy_class(strategy_name: str):
    """Get strategy class by name"""
    strategies = {
        'FourierStrategy': FourierStrategy,
        # Add more strategies here as you create them
        # 'EOVIEStrategy': EOVIEStrategy,
        # 'CustomStrategy': CustomStrategy,
    }
    
    if strategy_name not in strategies:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(strategies.keys())}")
        
    return strategies[strategy_name]


async def run_bot(config: dict, args):
    """Run the trading bot"""
    # Get API token from env or config
    api_token = os.getenv('DERIV_API_TOKEN') or config['deriv']['api_token']
    if args.demo:
        api_token = None  # force unauth demo mode
    
    # Override config with command line args
    symbol = args.symbol or config['trading']['symbol']
    stake_amount = args.stake or config['trading']['stake_amount']
    strategy_name = args.strategy or config['strategy']['name']
    
    # Get strategy class and instantiate
    StrategyClass = get_strategy_class(strategy_name)
    strategy = StrategyClass(params=config['strategy']['params'])
    
    # Create trading engine
    engine = DerivTradingEngine(
        strategy=strategy,
        symbol=symbol,
        app_id=config['deriv']['app_id'],
        api_token=api_token,
        stake_amount=stake_amount,
        candle_interval=config['trading']['candle_interval'],
        demo=args.demo,
        proposal_min_interval_sec=float(config.get('trading', {}).get('proposal_min_interval_sec', 1.5))
    )
    
    # Start trading
    try:
        await engine.start()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("Bot interrupted by user")
    finally:
        await engine.stop()


def main():
    parser = argparse.ArgumentParser(description='Deriv API Trading Bot')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--symbol', type=str,
                       help='Trading symbol (overrides config)')
    parser.add_argument('--stake', type=float,
                       help='Stake amount (overrides config)')
    parser.add_argument('--strategy', type=str,
                       help='Strategy name (overrides config)')
    parser.add_argument('--demo', action='store_true',
                       help='Run in demo mode (no API token required)')
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Deriv Trading Bot Starting")
    logger.info("=" * 60)
    logger.info(f"Config: {args.config}")
    logger.info(f"Symbol: {args.symbol or config['trading']['symbol']}")
    logger.info(f"Strategy: {args.strategy or config['strategy']['name']}")
    logger.info(f"Demo Mode: {args.demo or not config['deriv']['api_token']}")
    logger.info("=" * 60)
    
    # Run bot
    asyncio.run(run_bot(config, args))


if __name__ == "__main__":
    main()
