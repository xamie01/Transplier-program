#!/usr/bin/env python3
import pandas as pd

# Load both CSVs
no_htf = pd.read_csv('results/monthly_no_htf.csv')
htf = pd.read_csv('results/monthly_htf.csv')

print("="*80)
print("BACKTEST COMPARISON: No-HTF Filter vs HTF Filter")
print("="*80)

print("\nNO-HTF FILTER (Base Strategy):")
print(no_htf[['month', 'trades', 'win_rate', 'total_pnl', 'profit_factor']].to_string(index=False))

print("\n\nWITH HTF FILTER (4h Trend Confirmation):")
print(htf[['month', 'trades', 'win_rate', 'total_pnl', 'profit_factor']].to_string(index=False))

print("\n" + "="*80)
print("AGGREGATE STATISTICS")
print("="*80)

no_htf_total_pnl = no_htf['total_pnl'].sum()
htf_total_pnl = htf['total_pnl'].sum()
no_htf_total_trades = no_htf['trades'].sum()
htf_total_trades = htf['trades'].sum()
no_htf_avg_wr = no_htf['win_rate'].mean()
htf_avg_wr = htf['win_rate'].mean()
no_htf_avg_pf = no_htf[no_htf['profit_factor'] < float('inf')]['profit_factor'].mean()
htf_avg_pf = htf[htf['profit_factor'] < float('inf')]['profit_factor'].mean()
no_htf_avg_dd = no_htf['max_drawdown'].mean()
htf_avg_dd = htf['max_drawdown'].mean()

print(f"\n{'Metric':<30} {'No-HTF':>15} {'HTF Filter':>15} {'Winner':>15}")
print("-" * 75)
print(f"{'Total Trades':<30} {no_htf_total_trades:>15.0f} {htf_total_trades:>15.0f} {'HTF' if htf_total_trades > no_htf_total_trades else 'No-HTF':>15}")
print(f"{'Total PnL ($)':<30} {no_htf_total_pnl:>15.2f} {htf_total_pnl:>15.2f} {'HTF ✓' if htf_total_pnl > no_htf_total_pnl else 'No-HTF':>15}")
print(f"{'Avg Win Rate (%)':<30} {no_htf_avg_wr:>15.2f} {htf_avg_wr:>15.2f} {'HTF ✓' if htf_avg_wr > no_htf_avg_wr else 'No-HTF':>15}")
print(f"{'Avg Profit Factor':<30} {no_htf_avg_pf:>15.2f} {htf_avg_pf:>15.2f} {'HTF ✓' if htf_avg_pf > no_htf_avg_pf else 'No-HTF':>15}")
print(f"{'Avg Max Drawdown (%)':<30} {no_htf_avg_dd:>15.2f} {htf_avg_dd:>15.2f} {'HTF ✓' if htf_avg_dd < no_htf_avg_dd else 'No-HTF':>15}")

pnl_diff = htf_total_pnl - no_htf_total_pnl
pnl_pct_change = (pnl_diff / abs(no_htf_total_pnl) * 100) if no_htf_total_pnl != 0 else float('inf')

print(f"\n\nTotal PnL Change:     ${pnl_diff:+.2f} ({pnl_pct_change:+.1f}%)")
print(f"Trade Reduction:      {htf_total_trades} trades vs {no_htf_total_trades} trades ({((htf_total_trades - no_htf_total_trades) / no_htf_total_trades * 100):.1f}%)")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)
if htf_total_pnl >= no_htf_total_pnl and htf_total_trades < no_htf_total_trades:
    print("\n✓ USE HTF FILTER: Better risk-adjusted returns with fewer, higher-quality trades")
    print(f"  - Improves PnL by ${pnl_diff:.2f} while reducing trades by {no_htf_total_trades - htf_total_trades}")
elif htf_total_pnl >= no_htf_total_pnl:
    print("\n✓ OPTIONAL HTF FILTER: Maintains/improves PnL")
else:
    print("\n✗ NO HTF FILTER: Base strategy performs better")

print("\n" + "="*80)