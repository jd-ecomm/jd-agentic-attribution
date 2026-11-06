// Order journey pull for the JD Agentic Traffic dashboard (Discovery & journeys tab).
// Run in the built-in browser on admin.shopify.com/store/jdsports-ca (signed in).
// Set window.__JPULL = {since:'YYYY-MM-DD', until:'YYYY-MM-DD'} (until exclusive), paste this file, then
// window.__runJourneys(6) starts a background job (one worker per calendar month, 6 at a time); poll window.__J.status until 'done', then
// await window.__jOut() -> 'B64START<gzip+base64 JSON>B64END'.
// Every order's customer journey (visits before purchase, each with source and landing page) is reduced in the page:
//  agg  : counts by week x first-touch group x last-touch group x AI-touched x visits bucket x days bucket x new/returning
//  pat  : collapsed touch-path patterns (max 5 steps) by week bucket, for AI-touched and organic-first orders
//  ai   : one row per AI-touched order: [date, orderIndex, days, visits, value, path]
(function(){
const tok=document.querySelector('meta[name=csrf-token]')?.content||(document.documentElement.innerHTML.match(/"csrfToken":"([^"]+)"/)||[])[1];
const AI=/chatgpt|openai|perplexity|gemini\.google|bard\.google|copilot|claude\.ai|meta\.ai|grok\.com|muse\.ai|deepseek|mistral|duck\.ai/i;
const host=u=>{try{return new URL(u).hostname.replace(/^www\./,'')}catch(e){return ''}};
const seg=v=>{const ref=host(v.referrerUrl||''),src=(v.source||'').toLowerCase(),us=((v.utmParameters||{}).source||'').toLowerCase(),um=((v.utmParameters||{}).medium||'').toLowerCase();
 if(AI.test(ref)||AI.test(us)||AI.test(src))return 'ai';
 if(/shop\.app/.test(ref)||/shop\.app/.test(src))return 'shop_app';
 if(/klaviyo|attentive|email|sms/.test(us+um))return 'email_sms';
 const paid=/cpc|cpm|paid|ppc|display|shopping|pmax/.test(um);
 if(/google|bing|yahoo|duckduckgo|ecosia|brave|yandex|baidu|msn/.test(ref+' '+src+' '+us))return paid?'paid_search':'organic_search';
 if(/facebook|instagram|fb|tiktok|pinterest|snapchat|ig|meta|threads|youtube|reddit|x\.com|t\.co/.test(ref+' '+src+' '+us))return paid?'paid_social':'organic_social';
 if(src==='direct'||(!ref&&!us))return 'direct';
 return 'other'};
const lt=u=>{u=u||'';if(/shop\.app\/checkout|\/checkouts?\//.test(u))return 'checkout';if(/\/cart/.test(u))return 'cart';if(/\/products\//.test(u))return 'pdp';if(/\/collections\//.test(u))return 'plp';if(/\/search/.test(u))return 'search';if(/account\.|\/account/.test(u))return 'account';if(/\/pages\//.test(u))return 'page';if(/\/blogs?\//.test(u))return 'blog';try{const p=new URL(u).pathname;if(p==='/'||p==='')return 'home'}catch(e){}return 'other'};
const wk=d=>{const t=new Date(d.slice(0,10)+'T00:00:00Z');t.setUTCDate(t.getUTCDate()-t.getUTCDay());return t.toISOString().slice(0,10)};
const vb=n=>n<=1?'1':n==2?'2':n<=4?'3-4':n<=9?'5-9':'10+';
const db=d=>d==null?'na':d<=1?'0-1':d<=7?'2-7':d<=30?'8-30':'31+';
const Q=`query($c:String,$q:String!){ orders(first:250, after:$c, query:$q, sortKey:CREATED_AT){ pageInfo{hasNextPage endCursor} nodes{ createdAt totalPriceSet{shopMoney{amount}} customerJourneySummary{ customerOrderIndex daysToConversion momentsCount{count} moments(first:40){ nodes{ occurredAt ... on CustomerVisit { source referrerUrl landingPage utmParameters{source medium} } } } } } } }`;
window.__runJourneys=(workers=6)=>{
 const {since,until}=window.__JPULL;const J=window.__J={status:'running',pages:0,orders:0,agg:{},pat:{},ai:[],err:null,done:0,ranges:[]};
 // split into calendar-month ranges, run several at once
 let a=new Date(since+'T00:00:00Z');while(a.toISOString().slice(0,10)<until){const b=new Date(Date.UTC(a.getUTCFullYear(),a.getUTCMonth()+1,1));const e=b.toISOString().slice(0,10)<until?b.toISOString().slice(0,10):until;J.ranges.push([a.toISOString().slice(0,10),e]);a=b}
 const queue=J.ranges.slice();
 const one=async([s0,e0])=>{let c=null;for(;;){
  let j;for(let t=0;t<6;t++){try{const r=await fetch('/store/jdsports-ca/admin/api/2026-10/graphql.json',{method:'POST',headers:{'content-type':'application/json','x-csrf-token':tok},body:JSON.stringify({query:Q,variables:{c,q:`created_at:>=${s0} created_at:<${e0}`}})});j=await r.json();if(!j.errors)break}catch(e){j={errors:[String(e)]}}await new Promise(z=>setTimeout(z,3000*(t+1)))}
  if(j.errors)throw new Error(JSON.stringify(j.errors).slice(0,300));
  const o=j.data.orders;for(const n of o.nodes)take(n);
  J.pages++;if(!o.pageInfo.hasNextPage)break;c=o.pageInfo.endCursor;
  const ts=j.extensions&&j.extensions.cost&&j.extensions.cost.throttleStatus;if(ts&&ts.currentlyAvailable<4000)await new Promise(z=>setTimeout(z,2000));
 }};
 const take=n=>{J.orders++;const s=n.customerJourneySummary;const vs=((s&&s.moments&&s.moments.nodes)||[]).filter(v=>'landingPage' in v);
   const day=n.createdAt.slice(0,10),w=wk(day),val=+((n.totalPriceSet||{}).shopMoney||{}).amount||0;
   const steps=vs.map(v=>[seg(v),lt(v.landingPage)]);const nv=s&&s.momentsCount?s.momentsCount.count:vs.length;
   const f=steps.length?steps[0][0]:'none',l=steps.length?steps[steps.length-1][0]:'none';const anyAI=steps.some(x=>x[0]==='ai')?1:0;
   const nw=s&&s.customerOrderIndex===1?'n':'r';const k=[w,f,l,anyAI,vb(nv),db(s?s.daysToConversion:null),nw].join('|');
   const A=J.agg[k]=J.agg[k]||[0,0];A[0]++;A[1]+=val;
   const col=[];for(const x of steps){if(!col.length||col[col.length-1]!==x[0])col.push(x[0])}
   const p=col.slice(0,5).join('>')+(col.length>5?'>…':'');const coh=anyAI?'ai':(f==='organic_search'?'org':(f==='paid_search'?'paid':null));
   if(coh){const pk=coh+'|'+w+'|'+p;J.pat[pk]=(J.pat[pk]||0)+1}
   if(anyAI)J.ai.push([day,s?s.customerOrderIndex:null,s?s.daysToConversion:null,nv,Math.round(val*100)/100,steps.map(x=>x[0]+':'+x[1]).join('>')]);};
 const worker=async()=>{while(queue.length){const r=queue.shift();await one(r);J.done++}};
 Promise.all(Array.from({length:workers},worker)).then(()=>{J.status='done'}).catch(e=>{J.err=String(e);J.status='error'});
 return 'started '+J.ranges.length+' ranges';
};
window.__jOut=async()=>{const J=window.__J;const out={since:window.__JPULL.since,until:window.__JPULL.until,orders:J.orders,aggKeys:['week','first','last','anyAI','visits','days','nr'],agg:Object.entries(J.agg).map(([k,v])=>[...k.split('|'),v[0],Math.round(v[1])]),pat:Object.entries(J.pat).map(([k,v])=>[...k.split('|'),v]),ai:J.ai};
 const b=await new Response(new Blob([JSON.stringify(out)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();let bin='';const u=new Uint8Array(b);for(let i=0;i<u.length;i+=8192)bin+=String.fromCharCode(...u.subarray(i,i+8192));return 'B64START'+btoa(bin)+'B64END'};
})();
