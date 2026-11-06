"""Merge a journey pull (tools/pull_journeys.js output, decoded JSON) into data/journeys.json.
Usage: python3 tools/merge_journeys.py data/journeys.json new_pull.json
Rows are keyed by week (Sunday start). Every week touched by the new pull's date range is replaced.
The pull should start on a Sunday so whole weeks are replaced."""
import json, sys, datetime as dt

base_f, new_f = sys.argv[1:3]
B = json.load(open(base_f)); N = json.load(open(new_f))

def wk(day):
    t = dt.date.fromisoformat(day[:10]); return (t - dt.timedelta(days=(t.weekday()+1) % 7)).isoformat()

assert dt.date.fromisoformat(N['since']).weekday() == 6, 'journey pull must start on a Sunday'
nw = {r[0] for r in N['agg']} | {r[1] for r in N['pat']} | {wk(r[0]) for r in N['ai']}
nw |= {wk(N['since'])}
B['agg'] = [r for r in B['agg'] if r[0] not in nw] + N['agg']
B['pat'] = [r for r in B['pat'] if r[1] not in nw] + N['pat']
B['ai'] = [r for r in B['ai'] if wk(r[0]) not in nw] + N['ai']
B['until'] = max(B['until'], N['until'])
B['orders'] = sum(r[7] for r in B['agg'])
json.dump(B, open(base_f, 'w'), separators=(',', ':'))
print('journeys merged: weeks replaced', sorted(nw)[0], '->', sorted(nw)[-1], '| orders', B['orders'], '| AI-touched', len(B['ai']))
