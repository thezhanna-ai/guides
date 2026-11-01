// Requires an already running CDP browser and local static server; never launches Chrome.
const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs');
const path=require('node:path');

async function run(){
  const browser=await chromium.connectOverCDP(process.env.CDP_URL || 'http://127.0.0.1:9222');
  const context=await browser.newContext({reducedMotion:'reduce'});
  await context.route(/(goatcounter\.com|mc\.yandex\.)/,r=>r.fulfill({status:200,body:''}));
  const page=await context.newPage();
  const observations=[];
  const failures=[];
  try{
    for(const slug of ['shest-skillov','promty-pravki-foto-chatgpt','argon-ili-opus-kak-vybrat','15-zadach-claude-code-codex','8-stiley-reklamy-iz-foto-tovara']){
      await page.goto((process.env.BASE_URL || 'http://127.0.0.1:8764')+'/claude-ai/'+slug+'/',{waitUntil:'load'});
      if(await page.locator('#cookie-banner').isVisible())await page.locator('#cookie-decline').click();
      for(const width of [390,430,768,1280,1440]){
        await page.setViewportSize({width,height:900});
        for(const theme of ['light','dark']){
          if(await page.locator('html').getAttribute('data-theme')!==theme)await page.locator('.theme-toggle').click();
          await page.locator('h1').scrollIntoViewIfNeeded();
          const result=await page.locator('h1').evaluate(h=>{
            const rgb=s=>(s.match(/[\d.]+/g)||[]).map(Number);
            const luminance=c=>c.slice(0,3).map(v=>v/255).map(v=>v<=0.04045?v/12.92:((v+0.055)/1.055)**2.4).reduce((n,v,i)=>n+v*[0.2126,0.7152,0.0722][i],0);
            const color=getComputedStyle(h).color;
            let ancestor=h;
            while(ancestor&&rgb(getComputedStyle(ancestor).backgroundColor)[3]===0)ancestor=ancestor.parentElement;
            const background=ancestor?getComputedStyle(ancestor).backgroundColor:'rgb(255, 255, 255)';
            const a=luminance(rgb(color)),b=luminance(rgb(background));
            return {color,background,ratio:(Math.max(a,b)+0.05)/(Math.min(a,b)+0.05),fontSize:getComputedStyle(h).fontSize};
          });
          let screenshot;
          if(process.env.EVIDENCE_DIR){
            fs.mkdirSync(process.env.EVIDENCE_DIR,{recursive:true});
            screenshot=path.join(process.env.EVIDENCE_DIR,`${slug}-${width}-${theme}-heading.png`);
            await page.screenshot({path:screenshot,animations:'disabled'});
          }
          observations.push({slug,width,theme,...result,screenshot});
          if(result.ratio<3)failures.push({slug,width,theme,...result});
        }
      }
    }
  }finally{
    await context.close();
    if(process.env.EVIDENCE_DIR)fs.writeFileSync(path.join(process.env.EVIDENCE_DIR,'heading-contrast.json'),JSON.stringify(observations,null,2));
  }
  assert.deepEqual(failures,[],'Large article headings need contrast >= 3:1: '+JSON.stringify(failures));
  console.log('PASS: '+observations.length+' article heading contrast scenarios');
}
// End this client process to disconnect CDP. Never send Browser.close.
run().then(()=>process.exit(0),error=>{console.error(error);process.exit(1);});
