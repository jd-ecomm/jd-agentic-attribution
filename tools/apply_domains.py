"""Move AI sessions that Shopify files under another channel (gemini.google.com -> google organic,
copilot.microsoft.com -> microsoft, l.meta.ai -> meta, duck.ai -> duck) into the AI segments.
Session metrics only; their orders can't be attributed by referrer domain in ShopifyQL sales."""
import json,sys,re
raw,dom=sys.argv[1:3]
d=json.load(open(raw));K=d['keys']
rows=json.load(open(dom))
SE=['google','bing','yahoo!','duckduckgo','msn','brave','ecosia','kagi','yandex','baidu','aol','startpage','qwant']
def seg(ch,tt):
    ch=(ch or '').lower()
    if tt=='direct':return 'direct'
    if ch in SE:return 'paid_search' if tt=='paid' else ('organic_search' if tt=='organic' else 'other')
    if ch in ['facebook','instagram','pinterest','tiktok','snapchat']:return 'paid_social' if tt=='paid' else 'organic_social'
    if ch in ['klaviyo','attentive','gmail']:return 'email_sms'
    return 'other'
def aiseg(dm):
    if 'gemini' in dm:return 'ai_gemini'
    if 'copilot' in dm:return 'ai_copilot'
    if 'perplexity' in dm:return 'ai_perplexity'
    if 'claude' in dm:return 'ai_claude'
    return 'ai_other'
idx={(r[0],r[1]):r for r in d['daily']}
n=0
for day,dm,ch,tt,ses,dur,pv,pdp,atc,chk,cmp,bnc in rows:
    vals={'ses':ses,'dur':dur*ses,'pv':pv,'pdp':pdp,'atc':atc,'chk':chk,'cmp':cmp,'bnc':bnc*ses}
    for sg,sign in ((seg(ch,tt),-1),(aiseg(dm),1)):
        r=idx.get((day,sg))
        if r is None:
            r=[day,sg]+[0]*len(K);d['daily'].append(r);idx[(day,sg)]=r
        for k,v in vals.items():r[2+K.index(k)]+=sign*v
    n+=ses
json.dump(d,open(raw,'w'))
print('moved sessions',n)
