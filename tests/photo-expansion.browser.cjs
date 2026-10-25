// Browser acceptance: node tests/photo-expansion.browser.cjs
const {chromium}=require('/Users/zslepova/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../../tasks/content/2026-10-23-foto-pravki/article');
const worktree=path.resolve(__dirname,'..');
const slug='/claude-ai/promty-pravki-foto-chatgpt/';
const out=path.join(root,'screenshots/25-10-v5');fs.mkdirSync(out,{recursive:true});
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.webp':'image/webp','.woff2':'font/woff2','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml'};
const results=[];let browser,server;
async function shot(page,name){await page.screenshot({path:path.join(out,name+'.png')});}
async function center(locator){await locator.evaluate(e=>e.scrollIntoView({block:'center',behavior:'instant'}));await locator.page().waitForTimeout(150);}
async function ready(p){await p.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>{i.loading='eager';return i.decode().catch(()=>{});}));});}
async function run(browserOverride){
 try {
 server=http.createServer((req,res)=>{
  let file;try{file=path.resolve(worktree,'.'+decodeURIComponent(new URL(req.url,'http://local').pathname));}catch{res.writeHead(400);return res.end();}
  if(!file.startsWith(worktree+path.sep)){res.writeHead(403);return res.end();}
  if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
  fs.readFile(file,(err,data)=>{res.writeHead(err?404:200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream'});res.end(err?'Not found':data);});
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 browser=browserOverride||await chromium.launch({headless:true,channel:'chrome'});
 for(const [width,height] of [[390,844],[1440,900]]){
  const c=await browser.newContext({viewport:{width,height},hasTouch:true,permissions:['clipboard-read','clipboard-write']});
  await c.route(/mc\.yandex\./,r=>r.abort());
  const p=await c.newPage(),errors=[],missing=[];
  p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)missing.push(r.url());});
  await p.goto(base+slug);await p.addStyleTag({content:'html { scroll-behavior:auto !important }'});await ready(p);
  const cookie=p.locator('#cookie-banner');await cookie.waitFor({state:'visible'});
  const buttons=await cookie.locator('.cookie-actions button').evaluateAll(es=>es.map(e=>{let r=e.getBoundingClientRect(),c=getComputedStyle(e);return {width:r.width,height:r.height,bg:c.backgroundColor,color:c.color};}));
  assert.equal(buttons[0].width,buttons[1].width);assert.equal(buttons[0].height,buttons[1].height);assert.notEqual(buttons[0].bg,buttons[1].bg);
  await shot(p,`cookies-${width}`);
  await p.locator('#cookie-decline').click();assert(await cookie.isHidden());assert.equal(await p.evaluate(()=>localStorage.getItem('pronovoe-analytics-v1')),'declined');
  await p.reload();await ready(p);await p.addStyleTag({content:'html { scroll-behavior:auto !important }'});assert(await cookie.isHidden());
  await p.locator('[data-cookie-settings]').click();await p.locator('#cookie-accept').click();assert.equal(await p.evaluate(()=>localStorage.getItem('pronovoe-analytics-v1')),'accepted');
  await p.evaluate(()=>scrollTo(0,0));await shot(p,`header-${width}`);
  assert.equal(await p.locator('.prompt-section').count(),10);assert.equal(await p.locator('.comparison-slider').count(),9);assert.equal(await p.locator('.comparison-overlap').count(),0);
  const bodyText=await p.locator('body').evaluate(el=>{const clone=el.cloneNode(true);clone.querySelectorAll('.cta,script,style').forEach(n=>n.remove());return clone.textContent;});
  assert(!/раздатк|(?:^|[^а-яё])Иван/i.test(bodyText));assert(!/Вытянуть лицо из контрового света|Девять|девять/.test(bodyText));
  assert.match(await p.locator('h1').innerText(),/^10 промптов/);
  const expectedToc=await p.locator('article > .prompt-section > h2').evaluateAll(es=>es.map((e,i)=>({href:'#'+e.id,text:`${i+1}. ${[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('')}`})));
  assert.equal(expectedToc.length,10);
  for(const toc of ['.toc','.mobile-toc']){
   assert.deepEqual(await p.locator(`${toc} a[href^="#prompt-"]`).evaluateAll(es=>es.map(e=>({href:e.getAttribute('href'),text:e.textContent}))),expectedToc);
   assert.equal(await p.locator(`${toc} .toc-group, ${toc} a[href="#section-19"]`).count(),0);
   assert(await p.locator(`${toc} a`).evaluateAll(es=>es.every(e=>document.querySelector(e.getAttribute('href')))));
  }
  assert.equal(await p.locator('#style, #section-19').count(),0);
  assert.equal(await p.locator('#p8 .related-plaque a[href="/claude-ai/kopirovat-stil-foto-v-chatgpt/"]').count(),1);
  // Follow each real link in the visible TOC, including the mobile details menu.
  for(let n=1;n<=10;n++){
   if(width===390)await p.locator('.mobile-toc').evaluate(e=>{e.open=true;});
   const toc=width===390?'.mobile-toc':'.toc';
   await p.locator(`${toc} a[href="#prompt-${String(n).padStart(2,'0')}"]`).click();
   await p.waitForTimeout(100);
   const pos=await p.locator(`#prompt-${String(n).padStart(2,'0')}`).evaluate(e=>({top:e.getBoundingClientRect().top,bottom:document.querySelector('.masthead').getBoundingClientRect().bottom}));
   assert(pos.top>=pos.bottom-1&&pos.top<height,'Edit heading hidden after TOC click: '+n+' '+JSON.stringify(pos));
  }
  if(width===390)await p.locator('.mobile-toc').evaluate(e=>{e.open=false;});
  await center(p.locator('#p8 .related-plaque'));await shot(p,`style-card-${width}`);

  assert.equal(await p.locator('table tbody tr').count(),10);
  assert.match(await p.locator('.cover img').getAttribute('src'),/oblozhka-10/);
  for(let n=1;n<=10;n++){
   const section=p.locator('#p'+n),group=section.locator('.comparison');
   await center(group);
   assert.equal(await group.locator('img').count(),2);assert(await group.locator('img').evaluateAll(es=>es.every(e=>e.naturalWidth>0)));
   if(n===7){
    assert.equal(await group.getAttribute('class'),'comparison comparison-stacked comparison-expand');
    assert.equal(await group.locator('input,.comparison-handle,.comparison-stage').count(),0);
    assert.deepEqual(await group.locator('figcaption').allTextContents(),['Было','Стало']);
    const images=await group.locator('img').evaluateAll(es=>es.map(i=>{const r=i.getBoundingClientRect(),s=getComputedStyle(i);return {x:r.x,y:r.y,width:r.width,height:r.height,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,fit:s.objectFit};}));
    assert(images[1].y>=images[0].y+images[0].height+20,'Images must be stacked');
    assert(images[0].height<=height*.78+1,'Before exceeds viewport cap');
    for(const i of images){assert.equal(i.fit,'contain');assert(Math.abs(i.width/i.height-i.naturalWidth/i.naturalHeight)<.002,'Image is cropped or distorted');}
    const column=await group.boundingBox();assert(Math.abs(images[1].width-column.width)<1,'After must fill column');
    await group.screenshot({path:path.join(out,`dolphins-stacked-${width}.png`),style:'.masthead { visibility:hidden }'});
    results.push({width,height,dolphins:images,columnWidth:column.width});
    await section.locator('.copy-btn').click();assert.equal(await p.evaluate(()=>navigator.clipboard.readText()),await section.locator('pre').innerText());
    continue;
   }
   assert((await group.boundingBox()).height<height-100,'Comparison exceeds viewport');
   const geometry=await group.evaluate(e=>{
    const stage=e.querySelector('.comparison-stage'),r=stage.getBoundingClientRect(),handle=stage.querySelector('.comparison-handle'),h=getComputedStyle(handle,'::after');
    return {width:r.width,parentWidth:e.parentElement.getBoundingClientRect().width,ratio:r.width/r.height,handleBottom:parseFloat(h.bottom),handleHeight:parseFloat(h.height),handleTop:h.top,drag:[...stage.querySelectorAll('img')].map(i=>({draggable:getComputedStyle(i).webkitUserDrag,pointer:getComputedStyle(i).pointerEvents,fit:getComputedStyle(i).objectFit}))};
   });
   assert(geometry.handleBottom>=12&&geometry.handleBottom<=24,'Handle must be near bottom');
   assert(geometry.drag.every(i=>i.draggable==='none'&&i.pointer==='none'&&i.fit==='contain'),'Native drag or crop regression');
   if(width===1440){
    assert(geometry.width<=geometry.parentWidth*.89,'Desktop photo spans full article');
    if([1,2,3,4,5,8,10].includes(n))assert(Math.abs((await group.locator('.comparison-stage').boundingBox()).height-height*.78)<2,'Desktop photo must be 18% taller than previous 66svh');
   }
   if([1,2,3,4,5,8,10].includes(n))assert(Math.abs(geometry.ratio-3/4)<.001,'Vertical pair must be 3:4');
   const id=await section.locator('h2').getAttribute('id');assert.equal(id,'prompt-'+String(n).padStart(2,'0'));
   for(const toc of ['.toc','.mobile-toc'])assert.equal(await p.locator(`${toc} a[href="#${id}"]`).count(),1);
   await shot(p,`pair-${n}-${width}`);
   assert.equal(await group.locator('input').count(),1);
   {
    const range=group.locator('input'),stage=group.locator('.comparison-stage');
    await range.focus();await range.press('Home');assert.equal(await range.inputValue(),'0');await range.press('End');assert.equal(await range.inputValue(),'100');await range.press('ArrowLeft');assert.equal(await range.inputValue(),'99');
    await center(group);
    let r=await stage.boundingBox();
    for(const percent of [20,80,50]){
     await center(group);r=await stage.boundingBox();
     await p.mouse.move(r.x+r.width*.5,r.y+r.height*.5);await p.mouse.down();await p.mouse.move(r.x+r.width*percent/100,r.y+r.height*.5,{steps:10});await p.mouse.up();
     assert(Math.abs(Number(await range.inputValue())-percent)<=1,'Mouse drag failed');
     assert.equal(await group.evaluate(e=>e.style.getPropertyValue('--split')),await range.inputValue()+'%');
     await shot(p,`slider-${n}-${percent}-${width}`);
    }
    if(width===390){
     await center(group);r=await stage.boundingBox();
     const cdp=await c.newCDPSession(p);const y=r.y+r.height*.45;
     await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:r.x+r.width*.3,y}]});
     for(const t of [.35,.4,.45,.5,.55,.6,.65,.7])await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:r.x+r.width*t,y}]});
     await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});assert(Math.abs(Number(await range.inputValue())-70)<3,'Touch drag failed');
     await shot(p,`touch-${n}-${width}`);await cdp.detach();
    }
   }
   await section.locator('.copy-btn').click();assert.equal(await p.evaluate(()=>navigator.clipboard.readText()),await section.locator('pre').innerText());
  }
  await p.locator('.toc a[href="#section-27"]').evaluate(a=>a.click());
  await p.waitForTimeout(400);
  const geometry=await p.evaluate(()=>{let h=document.querySelector('.next-read h2').getBoundingClientRect(),bar=document.querySelector('.masthead').getBoundingClientRect();return {headingTop:h.top,headerBottom:bar.bottom};});assert(geometry.headingTop>=geometry.headerBottom,'Heading under sticky header');
  await shot(p,`next-anchor-${width}`);await center(p.locator('.next-read'));await shot(p,`next-cards-${width}`);
  for(const card of await p.locator('.next-card').all())assert(await card.evaluate(e=>e.querySelector('span').getBoundingClientRect().top>=e.querySelector('strong').getBoundingClientRect().bottom+8),'Card text runs together');
  assert(!(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth)),'Horizontal overflow');
  for(const faq of await p.locator('.faq-item').all()){await faq.locator('summary').click();assert(await faq.evaluate(e=>e.open));await faq.locator('summary').click();}
  await p.locator('.theme-toggle').click();await center(p.locator('.next-read'));await shot(p,`next-dark-${width}`);await p.locator('[data-cookie-settings]').click();await shot(p,`cookies-dark-${width}`);
  assert.equal(errors.length,0,JSON.stringify(errors));assert.equal(missing.length,0,JSON.stringify(missing));
  results.push({width,height,status:'PASS',pairs:10,tocEdits:10,tocAnchors:true,styleCard:true,mouse:true,keyboard:true,touch:width===390,cookies:buttons,geometry,errors,missing});await c.close();
 }
 fs.writeFileSync(path.join(root,'browser-checks-25-10-v5.json'),JSON.stringify({status:'PASS',results},null,2));console.log('PASS: 390 / 1440, 9 sliders + 1 stacked pair, mouse/keyboard/touch, copy, FAQ, anchors, cookies');
 }catch(e){fs.writeFileSync(path.join(root,'browser-checks-25-10-v5.json'),JSON.stringify({status:'FAIL',error:e.stack,results},null,2));throw e;}
 finally{if(browser&&!browserOverride)await browser.close();if(server)await new Promise(r=>server.close(r));}
}
module.exports=run;
if(require.main===module)run().catch(e=>{console.error(e);process.exitCode=1;});
