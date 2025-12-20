# Synthetic Index Pressure-Valve Model

## Overview
This model is designed for **Boom and Crash indices** (e.g., Boom 1000, Crash 500). Unlike traditional markets, these are governed by a Pseudo-Random Number Generator (PRNG). This strategy treats the market as a **Stochastic Pressure System**.

## Mathematical Components

### 1. The Jump-Diffusion Model
Price action is modeled using the Merton Jump-Diffusion formula:
$$dS_t = \mu S_t dt + \sigma S_t dW_t + S_t dJ_t$$
We ignore the $\mu$ (drift) and $dW_t$ (noise) for profit, and focus exclusively on $dJ_t$ (the Jump/Spike).

### 2. The Volatility Squeeze (Engineering Parallel)
In mechanical engineering, materials often exhibit a "yield point" after undergoing stress. 
- **The Squeeze:** When Standard Deviation ($\sigma$) drops, the "Potential Energy" of the algorithm accumulates.
- **The Trigger:** We only enter when the market is in a "Squeeze" state, reducing the risk of being caught in long, slow drawdowns.

### 3. Directional Bias
- **Boom Indices:** We only look for **Buys**. The algorithm is designed for sudden upward spikes.
- **Crash Indices:** We only look for **Sells**. The algorithm is designed for sudden downward crashes.

## How to Use
1. **strategy.py**: Import the `SpikeCatcherEngine` into your trading bot.
2. **test_engine.py**: Run this to see how the model behaves in a simulated environment.
3. **Refinement**: As an engineering student, you can adjust the `sigma_window` to change the sensitivity of the pressure detection.

## Risk Warning
This is a mathematical model based on probability densities. While it identifies high-probability zones, the PRNG can stay in an "oversold" or "overbought" state longer than anticipated. Always use strict risk management.
