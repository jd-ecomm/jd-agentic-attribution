// Weekly Shopify pull for the JD Agentic Traffic dashboard.
// Run in the built-in browser on admin.shopify.com/store/jdsports-ca/analytics (signed in as Ryan).
// Set window.__PULL = {since:'YYYY-MM-DD', until:'YYYY-MM-DD', mSince:'YYYY-MM-01'} before pasting this file,
// then: await window.__runPull()  ->  returns 'B64START<gzip+base64 JSON>B64END'.
(function(){
const tok=document.querySelector('meta[name=csrf-token]')?.content||(document.documentElement.innerHTML.match(/"csrfToken":"([^"]+)"/)||[])[1];
const q=async s=>{const r=await fetch('/store/jdsports-ca/admin/api/2026-10/graphql.json',{method:'POST',headers:{'content-type':'application/json','x-csrf-token':tok},body:JSON.stringify({query:'query($q:String!){ shopifyqlQuery(query:$q){ tableData{ columns{name} rows } parseErrors } }',variables:{q:s}})});const j=await r.json();const t=j.data&&j.data.shopifyqlQuery;if(!t)throw new Error('ShopifyQL error '+JSON.stringify(j.errors||j).slice(0,300));if(t.parseErrors&&t.parseErrors.length)throw new Error('parse: '+JSON.stringify(t.parseErrors).slice(0,300)+' in '+s.slice(0,120));return t.tableData.rows};
const seg=(ch,tt)=>{ch=(ch||'').toLowerCase();
 if(/chatgpt|openai/.test(ch))return'ai_chatgpt';if(/perplex/.test(ch))return'ai_perplexity';if(/copilot/.test(ch))return'ai_copilot';if(/gemini|bard/.test(ch))return'ai_gemini';if(/claude/.test(ch))return'ai_claude';if(/grok|poe|meta\.ai|deepseek|mistral|muse/.test(ch))return'ai_other';
 const se=['google','bing','yahoo!','duckduckgo','msn','brave','ecosia','kagi','yandex','baidu','aol','startpage','qwant'];
 if(tt=='direct')return'direct';if(se.includes(ch))return tt=='paid'?'paid_search':(tt=='organic'?'organic_search':'other');
 if(['facebook','instagram','pinterest','tiktok','snapchat'].includes(ch))return tt=='paid'?'paid_social':'organic_social';
 if(['klaviyo','attentive','gmail'].includes(ch))return'email_sms';return'other';};
const KEYS=['ses','dur','pv','pdp','atc','chk','cmp','bnc','fc_net','fc_gross','fc_ord','fc_ord_n','fc_ord_r','ln_net','ln_gross','ln_ord','ln_ord_n','ln_ord_r','fc_aovx','ln_aovx'];
const AIW="WHERE referring_channel IN ('chatgpt.com','chatgpt','openai','chatgpt.co','perplexity','copilot.com','copilot','gemini','claude','grok','poe','muse')";
const DOMS=['gemini.google.com','l.meta.ai','meta.ai','copilot.microsoft.com','perplexity.ai','www.perplexity.ai','claude.ai','duck.ai','muse.ai','grok.com','chat.deepseek.com','chat.mistral.ai'];
const gz=async s=>{const b=await new Response(new Blob([s]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();let bin='';const u=new Uint8Array(b);for(let i=0;i<u.length;i+=8192)bin+=String.fromCharCode(...u.subarray(i,i+8192));return btoa(bin)};
window.__runPull=async()=>{
 const {since,until,mSince}=window.__PULL;const W=`SINCE ${since} UNTIL ${until}`;const D={};
 const add=(day,sg,k,v)=>{const d=D[day]=D[day]||{};const s=d[sg]=d[sg]||{};s[k]=(s[k]||0)+v};
 const G='GROUP BY day, referring_channel, traffic_type';
 for(const r of await q(`FROM sessions SHOW sessions, average_session_duration, pageviews, products_viewed, sessions_with_cart_additions, sessions_that_reached_checkout, sessions_that_completed_checkout, bounce_rate ${G} ${W} LIMIT 100000`)){const sg=seg(r.referring_channel,r.traffic_type),n=+r.sessions;add(r.day,sg,'ses',n);add(r.day,sg,'dur',n*(+r.average_session_duration||0));add(r.day,sg,'pv',+r.pageviews||0);add(r.day,sg,'pdp',+r.products_viewed||0);add(r.day,sg,'atc',+r.sessions_with_cart_additions||0);add(r.day,sg,'chk',+r.sessions_that_reached_checkout||0);add(r.day,sg,'cmp',+r.sessions_that_completed_checkout||0);add(r.day,sg,'bnc',n*(+r.bounce_rate||0))}
 for(const[mod,tag,suf] of [['FIRST_CLICK_ATTRIBUTION','fc','__first_click'],['LAST_NON_DIRECT_CLICK_ATTRIBUTION','ln','__last_non_direct_click']]){
  for(const r of await q(`FROM sales SHOW net_sales, gross_sales, orders ${G}, new_or_returning_customer ${W} WITH ${mod} LIMIT 100000`)){const sg=seg(r.referring_channel,r.traffic_type),nr=r.new_or_returning_customer=='New'?'n':'r',o=+r['orders'+suf]||0;add(r.day,sg,tag+'_net',+r['net_sales'+suf]||0);add(r.day,sg,tag+'_gross',+r['gross_sales'+suf]||0);add(r.day,sg,tag+'_ord',o);add(r.day,sg,tag+'_ord_'+nr,o)}
  for(const r of await q(`FROM sales SHOW average_order_value, orders ${G} ${W} WITH ${mod} LIMIT 100000`)){add(r.day,seg(r.referring_channel,r.traffic_type),tag+'_aovx',(+r['average_order_value'+suf]||0)*(+r['orders'+suf]||0))}
 }
 const daily=[];for(const[d,ss] of Object.entries(D))for(const[s,o] of Object.entries(ss))daily.push([d,s,...KEYS.map(k=>Math.round((o[k]||0)*100)/100)]);
 const dom=(await q(`FROM sessions SHOW sessions, average_session_duration, pageviews, products_viewed, sessions_with_cart_additions, sessions_that_reached_checkout, sessions_that_completed_checkout, bounce_rate GROUP BY day, referrer_domain, referring_channel, traffic_type WHERE referrer_domain IN (${DOMS.map(d=>`'${d}'`).join(',')}) AND referring_channel NOT IN ('chatgpt','chatgpt.com','perplexity','claude','copilot','copilot.com','gemini','grok','muse','openai') ${W} LIMIT 100000`)).map(x=>[x.day,x.referrer_domain,x.referring_channel,x.traffic_type,+x.sessions,+x.average_session_duration,+x.pageviews,+x.products_viewed,+x.sessions_with_cart_additions,+x.sessions_that_reached_checkout,+x.sessions_that_completed_checkout,+x.bounce_rate]);
 // monthly detail for every calendar month from mSince to until
 const months=[];let m=new Date(mSince+'T00:00:00Z');while(m.toISOString().slice(0,10)<=until){const a=m.toISOString().slice(0,10);const e=new Date(Date.UTC(m.getUTCFullYear(),m.getUTCMonth()+1,0)).toISOString().slice(0,10);months.push([a,e<until?e:until]);m=new Date(Date.UTC(m.getUTCFullYear(),m.getUTCMonth()+1,1))}
 const keep=s=>s.startsWith('ai_')?'ai':(['organic_search','paid_search','direct'].includes(s)?s:'rest');
 const lp=[],prod=[],lptA={},devA={};
 for(const[s,e] of months){const mm=s.slice(0,7),MW=`SINCE ${s} UNTIL ${e}`;
  (await q(`FROM sessions SHOW sessions, sessions_with_cart_additions, sessions_that_completed_checkout GROUP BY landing_page_path ${AIW} ${MW} ORDER BY sessions DESC LIMIT 25`)).forEach(x=>lp.push([mm,String(x.landing_page_path).slice(0,90),+x.sessions,+x.sessions_with_cart_additions,+x.sessions_that_completed_checkout]));
  (await q(`FROM sales SHOW net_sales, orders, net_items_sold GROUP BY product_title, product_vendor, product_type ${AIW} ${MW} WITH FIRST_CLICK_ATTRIBUTION ORDER BY net_sales__first_click DESC LIMIT 30`)).forEach(x=>prod.push([mm,String(x.product_title).slice(0,70),x.product_vendor,x.product_type,Math.round(+x.net_sales__first_click),+x.orders__first_click,+x.net_items_sold__first_click]));
  for(const x of await q(`FROM sessions SHOW sessions, sessions_with_cart_additions, sessions_that_completed_checkout GROUP BY landing_page_type, traffic_type, referring_channel ${MW} LIMIT 5000`)){const k=[mm,keep(seg(x.referring_channel,x.traffic_type)),x.landing_page_type].join('|');const v=[+x.sessions,+x.sessions_with_cart_additions,+x.sessions_that_completed_checkout];lptA[k]=lptA[k]?lptA[k].map((a,i)=>a+v[i]):v}
  for(const x of await q(`FROM sessions SHOW sessions, sessions_that_completed_checkout GROUP BY session_device_type, traffic_type, referring_channel ${MW} LIMIT 5000`)){const k=[mm,keep(seg(x.referring_channel,x.traffic_type)),x.session_device_type].join('|');const v=[+x.sessions,+x.sessions_that_completed_checkout];devA[k]=devA[k]?devA[k].map((a,i)=>a+v[i]):v}
 }
 const flat=o=>Object.entries(o).map(([k,v])=>{const p=k.split('|');return [p[0],p[1],p[2]==='null'?null:p[2],...v]});
 const tot=(await q(`FROM sales SHOW net_sales ${W}`))[0];
 const out={since,until,months:months.map(x=>x[0].slice(0,7)),keys:KEYS,daily,dom,lp,prod,lpt:flat(lptA),dev:flat(devA),check_net_sales:+tot.net_sales};
 return 'B64START'+(await gz(JSON.stringify(out)))+'B64END';
};
})();
