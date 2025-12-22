#!/usr/bin/env python3
"""
Clean CSV data by removing rows with NaN in critical columns
"""
import pandas as pd
import sys

csv_path = 'data/R_100_candles_3600s_365d.csv'

print(f"Loading {csv_path}...")
df = pd.read_csv(csv_path)

print(f"Original shape: {df.shape}")
print(f"Rows with NaN 'time': {df['time'].isna().sum()}")
print(f"Rows with NaN 'datetime': {df['datetime'].isna().sum()}")

# Drop rows where time or datetime is NaN
df_clean = df.dropna(subset=['time', 'datetime'])

print(f"Cleaned shape: {df_clean.shape}")

# Save back
df_clean.to_csv(csv_path, index=False)
print(f"Saved cleaned data to {csv_path}")
