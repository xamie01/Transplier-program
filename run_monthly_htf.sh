#!/bin/bash
cd /workspaces/Transplier-program
mkdir -p results
.venv/bin/python tools/monthly_backtest_analysis.py \
  --csv data/R_100_1h_1y.csv \
  --lookback 150 --forecast 20 --atr-mult 0.5 \
  --stake 30 --risk-factor 0.5 --rr-ratio 3.0 \
  --output results/monthly_chart_htf.png \
  --use-htf-filter \
  --csv-output results/monthly_htf_metrics.csv
