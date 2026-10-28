async (page) => {
  const context = await page.context().browser().newContext();
  page = await context.newPage();
  const engine = page.context().browser().browserType().name();
  const output = '/Users/zslepova/IvanOS/projects/statya-pyat-neyrosetey/audits/pyat-viewer-20261028/';
  const results = [];
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const check = (ok, msg) => { if (!ok) throw Error(msg); };
  for (const width of [1440, 390]) {
    await page.setViewportSize({width, height: width === 1440 ? 948 : 844});
    await page.goto('http://127.0.0.1:8798/claude-ai/pyat-neyrosetey-dlya-ucheby/');
    const links = page.locator('.fig a.zoom');
    check(await links.count() === 5, 'five frames');
    for (let index = 0; index < 5; index++) {
      const link = links.nth(index);
      const filename = (await link.getAttribute('href')).split('/').pop().replace('.webp', '');
      await link.focus();
      await page.keyboard.press('Enter');
      await page.locator('#viewer img').evaluate(i => i.decode());
      const result = await page.locator('#viewer img').evaluate(i => {
        const v = document.querySelector('#viewer'), box = v.querySelector('.viewer-scroll');
        const r = i.getBoundingClientRect(), b = box.getBoundingClientRect();
        const c = document.createElement('canvas'); c.width = 64; c.height = 64;
        const ctx = c.getContext('2d'); ctx.drawImage(i, 0, 0, 64, 64);
        const data = ctx.getImageData(0,0,64,64).data;
        let min=255,max=0,green=0;
        for(let j=0;j<data.length;j+=4){min=Math.min(min,data[j],data[j+1],data[j+2]);max=Math.max(max,data[j],data[j+1],data[j+2]);if(data[j+1]>data[j]+40&&data[j+1]>data[j+2]+40)green++;}
        return {source:i.currentSrc,natural:[i.naturalWidth,i.naturalHeight],rect:r.toJSON(),box:b.toJSON(),width:innerWidth,height:innerHeight,visible:v.hasAttribute('open')&&r.width>0&&b.top>=0&&b.bottom<=innerHeight,greenFraction:green/4096,colorRange:max-min,scrolls:box.scrollHeight>box.clientHeight+2,overflow:document.documentElement.scrollWidth>innerWidth};
      });
      check(result.visible, filename+' visible');
      check(result.rect.width >= width*.92-1, filename+' >=92vw');
      check(result.rect.width <= result.natural[0], filename+' <=natural');
      check(Math.abs(result.rect.width/result.rect.height-result.natural[0]/result.natural[1])<.01, filename+' aspect');
      check(result.colorRange>50&&result.greenFraction<.8, filename+' decoded pixels');
      check(!result.overflow, 'page overflow');
      await page.screenshot({path:output+engine+'-'+width+'-'+filename+'.png'});
      if(result.scrolls){
        const bottom = await page.locator('#viewer .viewer-scroll').evaluate(b=>{b.scrollTop=b.scrollHeight;return b.scrollTop>0;});
        check(bottom,'vertical scroll');
        await page.screenshot({path:output+engine+'-'+width+'-'+filename+'-bottom.png'});
      }
      await page.keyboard.press('Escape');
      check(await page.locator('#viewer').getAttribute('aria-hidden')==='true', 'Escape');
      check(await link.evaluate(a=>a===document.activeElement),'focus restored');
      await link.click(); await page.locator('#viewer img').evaluate(i=>i.decode());
      await page.getByRole('button',{name:'Закрыть',exact:true}).click();
      check(await page.locator('#viewer').getAttribute('aria-hidden')==='true','close button and cached reopen');
      results.push({engine,filename,status:'PASS',...result});
    }
  }
  await page.setViewportSize({width:1440,height:948});
  await page.locator('.fig a.zoom').first().click();await page.locator('#viewer img').evaluate(i=>i.decode());
  await page.setViewportSize({width:390,height:844});
  const resized=await page.locator('#viewer img').evaluate(i=>i.getBoundingClientRect().width);
  check(resized>=358&&resized<=367,'live resize');
  await page.keyboard.press('Escape');
  check(errors.length===0,'page errors: '+errors.join(';'));
  return {engine,status:'PASS',cases:results.length,resize:true,errors,results};
}
