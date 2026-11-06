"""Merge a weekly pull (JSON from tools/pull_shopify.js) into data/raw.json.
Usage: python3 tools/merge_pull.py data/raw.json pull.json
Replaces every day in [since, until] and every month in pull.months, then moves AI sessions that Shopify
files under other channels (Gemini -> Google organic, Copilot -> Microsoft, Meta AI, Duck.ai) into AI."""
import json, sys, subprocess, os
raw, pull = sys.argv[1:3]
d = json.load(open(raw)); p = json.load(open(pull)); K = d['keys']
assert p['keys'] == K, ('key mismatch', p['keys'], K)
since, until = p['since'], p['until']
before = len(d['daily'])
d['daily'] = [r for r in d['daily'] if not (since <= r[0] <= until)] + p['daily']
for k in ('lp', 'prod', 'lpt', 'dev'):
    d[k] = [r for r in d[k] if r[0] not in p['months']] + p[k]
# check: pulled net sales (last non-direct) equals the site total
net = sum(r[2+K.index('ln_net')] for r in p['daily'])
assert abs(net - p['check_net_sales']) < 5, ('net sales mismatch', net, p['check_net_sales'])
json.dump(d, open(raw, 'w'))
tmp = pull + '.dom.json'; json.dump(p['dom'], open(tmp, 'w'))
subprocess.check_call([sys.executable, os.path.join(os.path.dirname(__file__), 'apply_domains.py'), raw, tmp])
print(f'merged {since}..{until}: {len(p["daily"])} day-rows, net sales {net:,.0f} = Shopify {p["check_net_sales"]:,.0f}; months {p["months"]}')
