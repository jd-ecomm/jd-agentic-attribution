"""Build the JD Agentic Traffic dashboard payload + page.
Usage: python3 tools/build.py data/raw.json data/searchable.json data/market.json template.html out.html
raw.json comes from the Shopify pull (see RUNBOOK.md)."""
import json, sys, collections, datetime as dt

raw, sv, mk, tpl, out = sys.argv[1:6]
LTF = sys.argv[6] if len(sys.argv) > 6 else 'data/landing_types.json'
JRF = sys.argv[7] if len(sys.argv) > 7 else 'data/journeys.json'
d = json.load(open(raw)); K = d['keys']
SV = json.load(open(sv)); MK = json.load(open(mk))
AI_SEGS = ['ai_chatgpt','ai_perplexity','ai_copilot','ai_gemini','ai_claude','ai_other']
KEEP = ['ai']+AI_SEGS+['organic_search','paid_search','direct','paid_social','email_sms','site']

def wk(day):
    t = dt.date.fromisoformat(day); return (t - dt.timedelta(days=(t.weekday()+1) % 7)).isoformat()

days = sorted({r[0] for r in d['daily']})
last_day = days[-1]
# last complete Sun-Sat week
ld = dt.date.fromisoformat(last_day)
last_sat = ld - dt.timedelta(days=(ld.weekday()-5) % 7)
LW_END = last_sat.isoformat()

W = collections.defaultdict(lambda: [0.0]*len(K))
D = collections.defaultdict(lambda: [0.0]*len(K))
for r in d['daily']:
    day, s, *v = r
    groups = [s, 'site'] + (['ai'] if s.startswith('ai_') else [])
    for g in groups:
        if g not in KEEP: continue
        if day <= LW_END:
            W[(wk(day), g)] = [a+b for a,b in zip(W[(wk(day), g)], v)]
        if g in ('ai','site','organic_search'):
            D[(day, g)] = [a+b for a,b in zip(D[(day, g)], v)]
weeks = sorted({w for w,_ in W})
weekly = {g: [[round(x, 1) for x in W[(w, g)]] for w in weeks] for g in KEEP}
DK = ['ses','atc','cmp','fc_net','fc_ord','ln_net']
di = [K.index(k) for k in DK]
daily = {g: [[round(D[(day, g)][i], 1) for i in di] for day in days] for g in ('ai','site','organic_search')}

# monthly: landing page types, device, landing pages, products
lpt = collections.defaultdict(lambda: collections.Counter())
for m, seg, t, s, a, c in d['lpt']:
    lpt[(m, seg)][t or 'Other'] += s; lpt[(m, 'all')][t or 'Other'] += s
dev = collections.defaultdict(lambda: collections.Counter())
for m, seg, t, s, c in d['dev']:
    dev[(m, seg)][t or 'other'] += s; dev[(m, 'all')][t or 'other'] += s
months = sorted({m for m,_ in lpt})
# JESTA retail calendar: fiscal year starts on the Sunday nearest 1 Feb; months run 4-5-4 weeks.
FY_STARTS = ['2024-02-04','2025-02-02','2026-02-01','2027-01-31','2028-01-30']
MNAMES = ['Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','Jan']
LENS = [4,5,4]*4
def rmonth(w):
    fy = max(f for f in FY_STARTS if f <= w)
    k = (dt.date.fromisoformat(w) - dt.date.fromisoformat(fy)).days // 7
    acc = 0
    for mi, L in enumerate(LENS):
        if k < acc + L: break
        acc += L
    y = int(fy[:4]) + (1 if mi == 11 else 0)
    return f'{y}-{mi:02d}', f'{MNAMES[mi]} {y}'
rmon = [rmonth(w)[0] for w in weeks]
rmonths = []
for w in weeks:
    k, l = rmonth(w)
    if not rmonths or rmonths[-1]['k'] != k: rmonths.append({'k': k, 'l': l, 'n': 0})
    rmonths[-1]['n'] += 1
for m in rmonths: m['partial'] = m['n'] < (5 if m['l'][:3] in ('Mar','Jun','Sep','Dec') else 4)

P = dict(
  built=dt.date.today().isoformat(), lastDay=last_day, lastWeekEnd=LW_END, keys=K, weeks=weeks, weekly=weekly,
  days=days, dkeys=DK, rmon=rmon, rmonths=rmonths, daily=daily, months=months,
  lpt={f'{m}|{s}': dict(c) for (m, s), c in lpt.items()},
  dev={f'{m}|{s}': dict(c) for (m, s), c in dev.items()},
  lp=d['lp'], prod=[p for p in d['prod'] if p[1] and p[1] != 'null'],
  searchable=SV, market=MK)

# ---------- landing types by week (AI / organic search / all) ----------
LTD = json.load(open(LTF))
wi = {w: i for i, w in enumerate(weeks)}
lt = {}
for c, rows in LTD.items():
    o = {}
    for day, t, *v in rows:
        if day > LW_END: continue
        i = wi.get(wk(day))
        if i is None: continue
        arr = o.setdefault(t or 'Other', [None]*len(weeks))
        arr[i] = [a+b for a, b in zip(arr[i] or [0]*7, v)]
    lt[c] = o
P['lt'] = lt
# ---------- order journeys ----------
JR = json.load(open(JRF))
w0 = wi[min(w for w in wi if w >= JR['since'])]
VB = ['1','2','3-4','5-9','10+']; DB = ['0-1','2-7','8-30','31+','na']
jc = {c: [[0]*13 for _ in weeks[w0:]] for c in ('ai','org','all')}
for w, f_, l_, anyai, vb, db, nr, n, val in JR['agg']:
    if w not in wi or wi[w] < w0: continue
    cs = ['all'] + (['ai'] if anyai == '1' else []) + (['org'] if f_ == 'organic_search' else [])
    for c in cs:
        a = jc[c][wi[w]-w0]
        a[0] += n; a[1] += val; a[2+VB.index(vb)] += n; a[7+DB.index(db)] += n
        if nr == 'n': a[12] += n
orgp = collections.Counter(); orgpos = [[0, 0, 0] for _ in weeks[w0:]]
for coh, w, p, n in JR['pat']:
    if coh == 'org' and w in wi and wi[w] >= w0:
        orgp[(wi[w], p)] += n; st = p.split('>')
        orgpos[wi[w]-w0][0 if len(st) == 1 else (1 if st[-1] == 'organic_search' else 2)] += n
P['jr'] = dict(w0=w0, since=JR['since'], c=jc, orgPos=orgpos,
  ai=[[wi[wk(r[0])]] + r[1:] for r in JR['ai'] if wk(r[0]) in wi and wi[wk(r[0])] >= w0],
  org=[[i, p, n] for (i, p), n in orgp.items() if n >= 2])

# ---------- insights (rule-based, recomputed every build) ----------
idx = {k: i for i, k in enumerate(K)}
def agg(g, ws):
    a = [0.0]*len(K)
    for w in ws:
        if w in weeks: a = [x+y for x, y in zip(a, weekly[g][weeks.index(w)])]
    return a
def m(a, k):
    s = a[idx['ses']] or 1; o = a[idx['fc_ord']]
    return {'ses': a[idx['ses']], 'cvr': a[idx['cmp']]/s, 'atc': a[idx['atc']]/s, 'pps': a[idx['pv']]/s, 'pdp': a[idx['pdp']]/s,
            'dur': a[idx['dur']]/s, 'net': a[idx['fc_net']], 'ln': a[idx['ln_net']], 'ord': o, 'rps': a[idx['ln_net']]/s,
            'new': (a[idx['ln_ord_n']]/a[idx['ln_ord']] if a[idx['ln_ord']] else 0), 'fcnew': (a[idx['fc_ord_n']]/o if o else 0)}[k]
L = weeks[-1]; i = weeks.index(L)
prev = weeks[i-1]; ly = (dt.date.fromisoformat(L) - dt.timedelta(weeks=52)).isoformat()
y0 = f'{L[:4]}-01-01'; ytd = [w for w in weeks if w >= y0 and w <= L]
l13 = weeks[max(0, i-12):i+1]; ly13 = [(dt.date.fromisoformat(w)-dt.timedelta(weeks=52)).isoformat() for w in l13]
f = lambda x: f'{x:,.0f}'; pct = lambda x: f'{x*100:.1f}%'
def ch(a, b): return (a/b-1) if b else 0
aiL, aiP, aiY = agg('ai', [L]), agg('ai', [prev]), agg('ai', [ly])
siL, siY = agg('site', [L]), agg('site', [ly])
a13, a13y = agg('ai', l13), agg('ai', ly13)
s13, s13y = agg('site', l13), agg('site', ly13)
aiT, orT, siT, paT = agg('ai', ytd), agg('organic_search', ytd), agg('site', ytd), agg('paid_search', ytd)
yoy13 = ch(m(a13, 'ses'), m(a13y, 'ses'))
share13 = m(a13, 'ses')/m(s13, 'ses'); share13y = m(a13y, 'ses')/m(s13y, 'ses')
ins = []
ins.append(dict(h='Growth vs the market',
  t=f"AI assistants sent {f(m(aiL,'ses'))} sessions in the week to {LW_END} ({ch(m(aiL,'ses'),m(aiP,'ses'))*100:+.0f}% on the week before, {ch(m(aiL,'ses'),m(aiY,'ses'))*100:+.0f}% on the same week last year). "
    f"Over the last 13 weeks AI sessions are {yoy13*100:+.0f}% year on year, against Graphite's market read of +{MK['ai_referral_yoy_us']}% (US) and +{MK['ai_referral_yoy_ww']}% (worldwide) AI referral growth, so we are {'ahead of' if yoy13*100>MK['ai_referral_yoy_ww'] else 'behind'} the market. "
    f"AI is {share13*100:.2f}% of site sessions (was {share13y*100:.2f}%), still under Graphite's 'under 1%' average."))
ins.append(dict(h='They arrive decided',
  t=f"Year to date AI visitors view {m(aiT,'pps'):.1f} pages and {m(aiT,'pdp'):.1f} product pages per session, against {m(orT,'pps'):.1f} and {m(orT,'pdp'):.1f} from organic search, and stay {m(aiT,'dur'):.0f}s vs {m(orT,'dur'):.0f}s. "
    f"Yet they add to cart at {pct(m(aiT,'atc'))} (organic {pct(m(orT,'atc'))}) and convert at {pct(m(aiT,'cvr'))} (organic {pct(m(orT,'cvr'))}, site {pct(m(siT,'cvr'))}). "
    f"The assistant does the browsing; the visit is the last step."))
ins.append(dict(h='A new-customer channel',
  t=f"{pct(m(aiT,'new'))} of AI orders this year (last non-direct click) came from new customers, vs {pct(m(orT,'new'))} for organic search and {pct(m(siT,'new'))} for the site. "
    f"Revenue per session (last non-direct) is ${m(aiT,'rps'):.2f} (organic ${m(orT,'rps'):.2f}, paid search ${m(paT,'rps'):.2f})."))
# journeys: last 13 complete weeks of orders
jw = [i for i in range(max(w0, len(weeks)-13), len(weeks))]
def jsum(c): return [sum(jc[c][i-w0][k] for i in jw) for k in range(13)]
JA, JO, JT = jsum('ai'), jsum('org'), jsum('all')
pos = collections.Counter(); bef = collections.Counter(); aft = collections.Counter()
for r in P['jr']['ai']:
    if r[0] not in jw or not r[5]: continue
    st = [x.split(':')[0] for x in r[5].split('>')]; ai = [i for i, x in enumerate(st) if x == 'ai']
    i0, i1, n_ = ai[0], ai[-1], len(st)
    pos['only' if len(ai) == n_ else ('first' if i0 == 0 else ('last' if i1 == n_-1 else 'mid'))] += 1
    aft[st[i1+1] if i1 < n_-1 else 'buy'] += 1; bef[st[i0-1] if i0 > 0 else 'start'] += 1
npos = sum(pos.values()) or 1
ps_touch = (bef['paid_search'] + aft['paid_search'])
ins.append(dict(h='Half the journey, not all of it',
  t=f"Over the last 13 weeks {JA[0]:,} orders ({JA[0]/JT[0]*100:.2f}%) had at least one AI visit in the path, about {JA[0]/max(1,m(a13,'ord')):.1f}x the orders AI gets on first click. "
    f"Only {pos['only']/npos*100:.0f}% were AI-only journeys. AI came first in {(bef['start'])/npos*100:.0f}% and was the last visit in {aft['buy']/npos*100:.0f}%. "
    f"Paid search sits right before or after the AI visit in {ps_touch/npos*100:.0f}% of these orders, so paid search is picking up credit for some AI-influenced demand."))
r7 = SV['rank']['7d']; jd = [x for x in r7 if x[0] == 'JD Sports'][0]; top = r7[0]
ins.append(dict(h='Visibility in AI answers',
  t=f"Searchable puts JD's visibility at {jd[1]}% across tracked prompts in Canada last week ({jd[5]:+} pts), #{[x[0] for x in r7].index('JD Sports')+1} behind {top[0]} at {top[1]}%, with average position {jd[3]} vs {top[3]} and the lowest sentiment in the top 8 ({jd[4]})."))

m3 = [m for m in months if m < LW_END[:7]][-3:]
def share_types(seg, types):
    c = collections.Counter()
    for mm in m3: c.update(lpt[(mm, seg)])
    t = sum(c.values()) or 1
    return sum(c[x] for x in types)/t
hp_ai = share_types('ai', ['Custom Page','Blog Article']); hp_org = share_types('organic_search', ['Custom Page','Blog Article'])
pdp_ai = share_types('ai', ['Product']); pdp_org = share_types('organic_search', ['Product']); col_ai = share_types('ai', ['Collection']); col_org = share_types('organic_search', ['Collection'])
ins.append(dict(h='Straight to the product',
  t=f"Over the last 3 months {pdp_ai*100:.0f}% of AI visits landed on a product page (organic search {pdp_org*100:.0f}%) and only {col_ai*100:.0f}% on a collection page (organic {col_org*100:.0f}%). "
    f"Another {hp_ai*100:.0f}% landed on help and info pages such as returns, FAQ, contact and the release calendar (organic {hp_org*100:.0f}%). The assistant picks the product; collection pages barely feature."))
P['insights'] = ins
plat = {g: sum(r[0] for r in weekly[g][weeks.index(ytd[0]):weeks.index(L)+1]) for g in AI_SEGS}
P['plNote'] = (f"ChatGPT sends {{chatgpt}} of our AI sessions in the selected period. Year to date the rest is small: Gemini {plat['ai_gemini']:,.0f} sessions, Perplexity {plat['ai_perplexity']:,.0f}, Copilot {plat['ai_copilot']:,.0f}, Claude {plat['ai_claude']:,.0f}, and Meta AI, Grok, Duck.ai and Muse {plat['ai_other']:,.0f} between them (Grok 2 and Muse 1 since January 2025). "
  "These are checked across every Shopify traffic field: referring channel, referrer domain, referrer URL and UTM source. Shopify files most Gemini and Copilot visits under Google organic and Microsoft, so they are moved into AI here (sessions and funnel only; their few orders stay with the original channel). "
  "Gemini's app strips the referrer from most links, so those visits land in Direct and can't be recovered. Graphite puts ChatGPT at 66% of US AI referrals, Claude 11% and Gemini 10%.")
html = open(tpl).read().replace('/*__DATA__*/', 'window.D=' + json.dumps(P, separators=(',', ':')) + ';')
open(out, 'w').write(html)
print('built', out, len(html), 'bytes; weeks', weeks[0], '->', L, '; days to', last_day)
for x in ins: print('-', x['h'], ':', x['t'])
