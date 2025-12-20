import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategy import SpikeCatcherEngine

def simulate_market(ticks=1000, type='Boom'):
    prices = [1000.0]
    for i in range(ticks):
        # Normal Brownian drift
        drift = (-0.05 if type == 'Boom' else 0.05) + np.random.normal(0, 0.02)
        
        # Poisson Jump (The Spike)
        jump = 0
        prob = 0.001 # 1 in 1000 chance per tick
        if np.random.random() < prob:
            jump = np.random.uniform(20, 40) if type == 'Boom' else -np.random.uniform(20, 40)
            
        prices.append(prices[-1] + drift + jump)
    return pd.DataFrame({'Close': prices})

# Run Test
market_data = simulate_market(ticks=1500, type='Boom')
engine = SpikeCatcherEngine(index_name='Boom 1000')

# Run Analysis
results = engine.generate_signal(market_data)

# Visualization
plt.figure(figsize=(12, 5))
plt.plot(market_data['Close'], label='Market Price', color='blue')
if "BUY" in results['Signal']:
    plt.scatter(len(market_data)-1, market_data['Close'].iloc[-1], color='green', s=100, label='Entry Signal')

plt.title(f"Simulation Test: {results['Index']}")
plt.legend()
plt.show()

print(f"Final Report: {results}")
