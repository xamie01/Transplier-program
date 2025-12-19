#!/usr/bin/env python3
"""
Batch optimization runner - execute sweeps sequentially with checkpointing
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json

WORKSPACE = Path(__file__).parent
RESULTS_DIR = WORKSPACE / 'optimization_results'
RESULTS_DIR.mkdir(exist_ok=True)

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*80}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}")
    
    result = subprocess.run(cmd, cwd=WORKSPACE)
    success = result.returncode == 0
    
    status = "✓ SUCCESS" if success else "✗ FAILED"
    print(f"\n{status}")
    return success

def main():
    print(f"Transpiler Fourier Strategy Optimization Suite")
    print(f"Workspace: {WORKSPACE}")
    print(f"Results dir: {RESULTS_DIR}")
    
    plan = [
        ("R_100 1h Sweep", [
            sys.executable, "tools/param_optimizer.py",
            "--symbol", "R_100",
            "--interval", "3600",
            "--days", "60",
            "--stake", "30",
            "--risk-factors", "0.25,0.5,0.75",
            "--rr-list", "2,3,4"
        ]),
        ("R_50 1h Sweep", [
            sys.executable, "tools/param_optimizer.py",
            "--symbol", "R_50",
            "--interval", "3600",
            "--days", "60",
            "--stake", "30",
            "--risk-factors", "0.25,0.5,0.75",
            "--rr-list", "2,3,4"
        ]),
        ("R_75 1h Sweep", [
            sys.executable, "tools/param_optimizer.py",
            "--symbol", "R_75",
            "--interval", "3600",
            "--days", "60",
            "--stake", "30",
            "--risk-factors", "0.25,0.5,0.75",
            "--rr-list", "2,3,4"
        ]),
    ]
    
    results = {}
    for desc, cmd in plan:
        success = run_command(cmd, desc)
        results[desc] = success
    
    # Summary
    print(f"\n\n{'='*80}")
    print("OPTIMIZATION RUN SUMMARY")
    print(f"{'='*80}")
    for desc, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {desc}")
    
    # Save summary
    summary_file = RESULTS_DIR / f"run_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'all_passed': all(results.values())
        }, f, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")
    
    if all(results.values()):
        print("\n✓ All sweeps completed successfully!")
        print("\nNext steps:")
        print("1. Review CSV results in current directory (param_optimizer_results_*.csv)")
        print("2. Pick top 5 configs for walk-forward validation")
        print("3. Run walk_forward_test.py with best configs")
        print("4. Compare results and lock in final parameters")
    else:
        print("\n✗ Some sweeps failed. Check logs above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
