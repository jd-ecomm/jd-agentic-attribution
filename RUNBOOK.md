# JD Agentic Traffic: weekly refresh

Live site: https://jd-ecomm.github.io/jd-agentic-attribution/ · Claude page: https://claude.ai/artifact/E3odQM4nUNPJjQ9PvMseXc

AI assistant traffic (ChatGPT, Perplexity, Gemini, Copilot, Claude, Meta AI, Grok, Muse) to jdsports.ca against organic search, paid search, direct and the whole site, from Shopify (ShopifyQL), with Searchable visibility and Graphite market benchmarks.

## Monday schedule (America/Vancouver)
1. **12:17 work PC task** (needs Ryan's computer): Shopify pull in the built-in browser + Searchable pull in Chrome. Writes the results to the Claude page's database (collection `pull`, docs `shopify` and `searchable`).
2. **12:47 cloud task**: reads `pull`, merges into `data/`, rebuilds `index.html`, pushes, checks GitHub Pages deployed, republishes the Claude page.

## Shopify pull (built-in browser)
Open https://admin.shopify.com/store/jdsports-ca/analytics. In the page run:
`window.__PULL={since,until,mSince}` where until = last Saturday, since = the Sunday 4 weeks earlier (re-pulls 4 weeks so late returns settle), mSince = first day of since's calendar month. Then paste `tools/pull_shopify.js` and `await window.__runPull()`. It returns `B64START…B64END` (gzip + base64 JSON). The result is large: return it with padding so it saves to a file, never print it.
- Uses ShopifyQL through the admin GraphQL API version **2026-10** (attribution needs 2026-04 or later). First click = `WITH FIRST_CLICK_ATTRIBUTION`, last non-direct = `WITH LAST_NON_DIRECT_CLICK_ATTRIBUTION`.
- AI = referring_channel chatgpt/chatgpt.com/openai, perplexity, copilot, gemini, claude, grok, poe, muse. Shopify files gemini.google.com under Google organic, copilot.microsoft.com under "microsoft", l.meta.ai under "meta" and duck.ai under "duck": `tools/apply_domains.py` moves those sessions (session metrics only) into AI.
- AOV = Shopify `average_order_value`, orders-weighted (stored as `*_aovx` = AOV × orders).

## Searchable pull (Claude in Chrome)
Open https://app.searchable.com/ai-search-insights?tab=visibility (JD Sports CA project, Canada), wait ~8s, run `tools/pull_searchable.js`. Returns `SVSTART{json}SVEND`. The prompt set grew from 24 to 532 answers a day in Sep 2026, so the page only compares visibility from October 2026.

## Build
```
python3 tools/merge_pull.py data/raw.json pull.json          # asserts pulled net sales = Shopify total
python3 tools/merge_searchable.py data/searchable.json sv.json
python3 tools/build.py data/raw.json data/searchable.json data/market.json template.html index.html
```
Then headless check every tab (no NaN/undefined), commit "Weekly refresh <last Saturday>", push, confirm the pages-build-deployment run for the commit succeeded (push an empty "Redeploy GitHub Pages" commit once if GitHub fails it), republish the Claude page from index.html.

## Calendar
Weeks are Sunday to Saturday. Retail months follow the JESTA 4-5-4 calendar (fiscal year from the Sunday nearest 1 Feb; Feb 4 weeks, Mar 5, Apr 4, …). Same week last year = 52 weeks earlier.

## Market benchmarks
`data/market.json` holds Graphite's State of Gen AI figures (Nov 2026). Update by hand when Graphite publishes a new report.
