#!/usr/bin/env python3
"""
Post-sweep analysis: parse results CSVs, filter by criteria, pick top configs for walk-forward
"""
import pandas as pd
import sys
from pathlib import Path
import json

def analyze_sweep_results():
    """Load and analyze param_optimizer CSV files"""
    
    results_files = list(Path('.').glob('param_optimizer_results_*.csv'))
    
    if not results_files:
        print("No optimization result CSVs found. Run param_optimizer.py first.")
        sys.exit(1)
    
    print(f"Found {len(results_files)} result files:")
    for f in results_files:
        print(f"  - {f}")
    
    all_results = {}
    
    for csv_file in results_files:
        print(f"\nAnalyzing {csv_file}...")
        df = pd.read_csv(csv_file)
        
        # Extract symbol from filename
        symbol = csv_file.stem.split('_')[3]  # param_optimizer_results_SYMBOL_timestamp
        
        # Filter by success criteria
        criteria = (
            (df['profit_factor'] > 1.8) &
            (df['win_rate'] > 45.0) &
            (df['max_drawdown'] < 20.0) &
            (df['trades'] >= 10)
        )
        
        passed = df[criteria].sort_values('profit_factor', ascending=False)
        
        print(f"  Total configs: {len(df)}")
        print(f"  Passed filters (PF>1.8, WR>45%, DD<20%, trades>=10): {len(passed)}")
        
        if len(passed) > 0:
            print(f"\n  Top 5 passed configs:")
            top5 = passed.head(5)
            for idx, row in top5.iterrows():
                print(f"    RISKx={row['risk_factor']:.2f} RR={row['rr_ratio']:.1f} | "
                      f"WR={row['win_rate']:.1f}% PnL=${row['total_pnl']:.2f} "
                      f"PF={row['profit_factor']:.2f} DD={row['max_drawdown']:.2f}%")
        
        all_results[symbol] = {
            'total': len(df),
            'passed': len(passed),
            'top5': passed.head(5).to_dict('records') if len(passed) > 0 else [],
            'all': df.to_dict('records')
        }
    
    # Cross-symbol analysis
    print(f"\n{'='*80}")
    print("CROSS-SYMBOL ANALYSIS")
    print(f"{'='*80}")
    
    for symbol, data in all_results.items():
        print(f"\n{symbol}: {data['passed']}/{data['total']} configs passed")
        if data['top5']:
            best = data['top5'][0]
            print(f"  Best: RISKx={best['risk_factor']:.2f} RR={best['rr_ratio']:.1f} "
                  f"PF={best['profit_factor']:.2f}")
    
    # Find common best config
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS FOR WALK-FORWARD VALIDATION")
    print(f"{'='*80}")
    print("\nTest these configs with walk_forward_test.py:")
    print("\nExample command:")
    print("  python tools/walk_forward_test.py \\")
    print("    --symbol R_100 \\")
    print("    --interval 3600 \\")
    print("    --days 90 \\")
    print("    --train-days 21 \\")
    print("    --test-days 7 \\")
    print("    --stake 30 \\")
    print("    --lookback 150 \\")
    print("    --forecast 20 \\")
    print("    --atr-mult 0.5 \\")
    print("    --risk-factor 0.5 \\")
    print("    --rr-ratio 3.0")
    
    # Save analysis
    analysis_file = 'sweep_analysis.json'
    with open(analysis_file, 'w') as f:
        # Convert records to JSON-serializable format
        json_data = {}
        for symbol, data in all_results.items():
            json_data[symbol] = {
                'total': data['total'],
                'passed': data['passed'],
                'top5': [{k: (float(v) if isinstance(v, (int, float)) else v) 
                         for k, v in row.items()} for row in data['top5']]
            }
        json.dump(json_data, f, indent=2)
    
    print(f"\nDetailed analysis saved to {analysis_file}")

if __name__ == '__main__':
    analyze_sweep_results()
