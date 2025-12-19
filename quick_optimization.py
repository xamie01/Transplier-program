#!/usr/bin/env python3
"""
Quick-start optimizer: Run one focused sweep and show best configs for walk-forward
"""
import subprocess
import sys
from pathlib import Path

def quick_sweep():
    """Run a quick sweep on R_100 to establish baseline"""
    print("\n" + "="*80)
    print("FOURIER STRATEGY: QUICK OPTIMIZATION SWEEP")
    print("="*80)
    print("\nPhase 1: Parameter Sweep")
    print("Testing 9 risk/RR combinations on R_100 1h (60 days)")
    print("Metrics: profit_factor (PF), win_rate (WR), max_drawdown (DD)")
    print("="*80)
    
    cmd = [
        sys.executable, "tools/param_optimizer.py",
        "--symbol", "R_100",
        "--interval", "3600",
        "--days", "60",
        "--stake", "30",
        "--risk-factors", "0.25,0.5,0.75",
        "--rr-list", "2,3,4"
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode == 0:
        print("\n" + "="*80)
        print("✓ Sweep Complete!")
        print("="*80)
        print("""
Next steps:
1. Review the CSV output (param_optimizer_results_R_100_*.csv)
2. Identify top 3-5 configs with:
   - PF > 1.8
   - WR > 45%
   - DD < 20%
   - Trades >= 10
3. Run walk-forward validation on top configs:
   
   python tools/walk_forward_test.py \\
     --symbol R_100 \\
     --days 90 \\
     --train-days 21 \\
     --test-days 7 \\
     --risk-factor 0.5 \\
     --rr-ratio 3.0

4. Repeat for R_50 and R_75
5. Compare results and lock in best config
        """)
    else:
        print("\n✗ Sweep failed. Check logs above.")
        sys.exit(1)

if __name__ == '__main__':
    quick_sweep()
