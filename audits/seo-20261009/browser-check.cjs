const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const vitals = fs.readFileSync(process.env.WEB_VITALS_PATH, 'utf8');
const stage = process.argv[2];
if (!['before','after','live'].includes(stage)) throw new Error('Stage: before, after or live');
fs.mkdirSync(path.join(__dirname,'skriny'),{recursive:true});
const base = process.argv[3] || 'http://127.0.0.1:8769';
const slugs = ['pyat-skillov-claude-code','zakryt-sekrety-ot-claude-code','gotovye-fayly-excel-word-pdf','svoy-server-dlya-claude','shtat-agentov-paperclip'];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 const results=[];
 for(const slug of ['',...slugs]) for(let run=1;run<=3;run++) {
  const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});
  const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript({content:vitals+`;window.__vitals={};for(const n of ['LCP','CLS','INP'])webVitals['on'+n](m=>{window.__vitals[n]={value:m.value,rating:m.rating,entries:m.entries.map(e=>({name:e.name,duration:e.duration,interactionId:e.interactionId,element:e.element?.tagName}))}},{reportAllChanges:true});`});
  const cdp=await context.newCDPSession(page);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{cacheDisabled:true});await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:150,downloadThroughput:1600000/8,uploadThroughput:750000/8,connectionType:'cellular4g'});await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
  const url=base+(slug?'/claude-ai/'+slug+'/':'/');
  await page.goto(url,{waitUntil:'load',timeout:120000});await page.waitForTimeout(4500);
  const theme=page.locator('.theme-toggle');if(await theme.count() && await theme.first().isVisible()){await theme.click();await page.waitForTimeout(200);await theme.click();}
  const close=page.locator('#cookie-decline');if(await close.count() && await close.first().isVisible())await close.first().click();
  const search=page.locator('input[type="search"]');if(await search.count() && await search.first().isVisible()){await search.fill('Claude');await page.waitForTimeout(400);await search.fill('');}
  const toc=page.locator('.mobile-toc summary');if(await toc.count() && await toc.first().isVisible()){await toc.click();await page.waitForTimeout(300);await toc.click();}
  await page.waitForTimeout(300);await page.evaluate(()=>window.scrollTo(0,document.body.scrollHeight));await page.waitForTimeout(800);await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(300);
  await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));await cdp.send('Page.setWebLifecycleState',{state:'frozen'});await cdp.send('Page.setWebLifecycleState',{state:'active'});
  const data=await page.evaluate(()=>({metrics:window.__vitals,metricLimit:'INP for these scripted interactions, not field p75; missing INP is not zero',overflow:document.documentElement.scrollWidth>innerWidth,brokenImages:[...document.images].filter(x=>x.complete&&!x.naturalWidth).map(x=>x.src),navigation:performance.getEntriesByType('navigation').map(x=>({ttfb:x.responseStart,duration:x.duration})),resources:performance.getEntriesByType('resource').map(x=>({url:x.name,bytes:x.transferSize,duration:x.duration}))}));
  results.push({slug:slug||'home',run,url,browser:browser.version(),conditions:{viewport:'390x844',cpu:4,latency_ms:150,download_bps:1600000,upload_bps:750000,cache:'cold per run',tool:'Playwright + web-vitals '+require(path.join(path.dirname(process.env.WEB_VITALS_PATH),'../package.json')).version},...data,errors});
  fs.writeFileSync(path.join(__dirname,stage+'-mobile.json'),JSON.stringify(results,null,2)+'\n');console.log(stage,slug||'home',run,JSON.stringify(data.metrics),errors.length);await context.close();
 }
 if(stage!=='live')for(const slug of slugs) for(const width of [1470,390]){
  const context=await browser.newContext({viewport:{width,height:width===390?844:1000},deviceScaleFactor:1});const page=await context.newPage();await page.goto(base+'/claude-ai/'+slug+'/',{waitUntil:'load'});await page.evaluate(async()=>{for(let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,60));}scrollTo(0,0);});await page.waitForTimeout(500);await page.screenshot({path:path.join(__dirname,'skriny',stage+'-'+slug+'-'+width+'.png'),fullPage:true});await context.close();
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
