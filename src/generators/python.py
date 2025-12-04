"""Prototype generator: IR -> simple Python strategy script."""


def generate(ir: dict) -> str:
    name = ir.get('meta', {}).get('name', 'strategy')
    # expect two SMA indicators in prototype IR
    p1 = ir['indicators'][0]['params']['period']
    p2 = ir['indicators'][1]['params']['period']
    code = f"""# Generated Python strategy: {name}
import pandas as pd

def run(df):
    df = df.copy()
    df['s1'] = df['close'].rolling({p1}).mean()
    df['s2'] = df['close'].rolling({p2}).mean()
    df['signal'] = 0
    df.loc[df['s1'] > df['s2'], 'signal'] = 1
    df.loc[df['s1'] < df['s2'], 'signal'] = -1
    return df

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python strategy.py <csv>')
        sys.exit(1)
    df = pd.read_csv(sys.argv[1])
    out = run(df)
    print(out.tail(5).to_json(orient='records'))
"""
    return code
