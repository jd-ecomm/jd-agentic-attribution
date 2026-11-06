// Searchable pull for the JD Agentic Traffic dashboard. Run in Claude in Chrome (Ryan is signed in to Searchable there)
// on https://app.searchable.com/ai-search-insights?tab=visibility after the page has loaded (wait ~8s).
// Returns 'SVSTART<json>SVEND' with weekly visibility and the 7/30/90-day competitor ranking.
(async()=>{
 const es=performance.getEntriesByType('resource').map(e=>e.name);
 const pick=k=>es.filter(x=>x.includes(k)).pop();
 const f=async(k,tr)=>{const u=pick(k);if(!u)throw new Error('no '+k+' request on page');const x=new URL(u);x.searchParams.set('timeRange',tr);const r=await fetch(x);if(!r.ok)throw new Error(k+' '+r.status);return r.json()};
 const ts=await f('/api/analytics/visibility/chart-timeseries','365d');
 const v=(ts.brand&&ts.brand.data||[]).filter(x=>x.totalResponses>0);const wk={};
 v.forEach(x=>{const d=new Date(x.date+'T00:00:00Z');d.setUTCDate(d.getUTCDate()-d.getUTCDay());const k=d.toISOString().slice(0,10);(wk[k]=wk[k]||[]).push([x.score,x.totalResponses])});
 const weekly=Object.entries(wk).sort().map(([k,a])=>[k,Math.round(a.reduce((s,x)=>s+x[0],0)/a.length*10)/10,Math.round(a.reduce((s,x)=>s+x[1],0)/a.length)]);
 const rank={};for(const tr of ['7d','30d','90d']){const r=await f('/api/analytics/visibility/industry-ranking',tr);rank[tr]=r.entities.slice(0,8).map(e=>[e.entityName==='brand'?'JD Sports':e.entityName,e.visibility,e.shareOfVoice,e.avgPosition,Math.round(e.sentiment),tr==='90d'?null:e.change])}
 return 'SVSTART'+JSON.stringify({pulled:new Date().toISOString().slice(0,10),weekly,rank})+'SVEND';
})()
