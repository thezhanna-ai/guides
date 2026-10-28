(async()=>{
const result={width:innerWidth,height:innerHeight,userAgent:navigator.userAgent,prompts:[],viewers:[],contrast:[]};
const check=(condition,message)=>{if(!condition)throw Error(message)};
const before=await (await fetch('/__before.json')).json();
const pause=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
const loaded=img=>img.complete&&img.naturalWidth>0?Promise.resolve():new Promise((r,j)=>{img.addEventListener('load',r,{once:true});img.addEventListener('error',()=>j(Error('Image load failed')),{once:true})});
const lum=color=>{let c=color.match(/[\d.]+/g).slice(0,3).map(Number).map(x=>{x/=255;return x<=0.04045?x/12.92:((x+.055)/1.055)**2.4});return .2126*c[0]+.7152*c[1]+.0722*c[2]};
const contrast=(a,b)=>{let x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
await document.fonts.ready;
for(const img of document.querySelectorAll('article img')){img.loading='eager';await loaded(img)}
check(document.documentElement.scrollWidth<=innerWidth,'horizontal overflow');
for(const theme of ['light','dark']){
 document.documentElement.dataset.theme=theme;
 for(const card of document.querySelectorAll('article .code-card')){
  const legend=card.previousElementSibling;
  check(legend.classList.contains('prompt-legend'),'Missing legend');
  const legendRatio=contrast(getComputedStyle(legend).color,getComputedStyle(document.body).backgroundColor);
  check(legendRatio>=4.5,'Legend contrast '+legendRatio);
  const pre=card.querySelector('pre'),material=pre.querySelector('.prompt-material'),bg=getComputedStyle(card).backgroundColor;
  check(material,'Missing highlight '+pre.id);check(pre.textContent===before[pre.id],'Prompt text changed '+pre.id);
  const white=getComputedStyle(pre).color,yellow=getComputedStyle(material).color;
  const ratios={legendRatio,theme,id:pre.id,bg,white,yellow,whiteRatio:contrast(white,bg),yellowRatio:contrast(yellow,bg),font:getComputedStyle(pre).fontSize,lineHeight:getComputedStyle(pre).lineHeight};
  check(ratios.whiteRatio>=4.5&&ratios.yellowRatio>=4.5,'Contrast failed');result.contrast.push(ratios);
 }
}
document.documentElement.dataset.theme='light';
// Capture bytes passed by the existing copy handler, then test its fallback as well.
const clipboard=navigator.clipboard,write=clipboard.writeText;let copied;
clipboard.writeText=async text=>{copied=text};
for(const button of document.querySelectorAll('[data-copy-target]')){button.click();await pause();check(copied===before[button.dataset.copyTarget],'Copy changed');check(button.textContent.includes('Скопировано'),'Copy state');result.prompts.push({id:button.dataset.copyTarget,characters:copied.length,exact:true})}
clipboard.writeText=write;
for(const link of document.querySelectorAll('.fig a.zoom')){
 link.focus();link.click();const img=document.querySelector('#viewer img');await loaded(img);await pause();
 const r=img.getBoundingClientRect(),viewer=document.querySelector('#viewer');
 check(viewer.getAttribute('aria-hidden')==='false','Viewer closed');check(img.currentSrc===link.href,'Wrong source');
 check(r.width>100&&r.height>50&&r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth,'Image outside viewport');
 check(document.elementFromPoint(r.left+r.width/2,r.top+r.height/2)===img,'Image covered');
 result.viewers.push({source:img.currentSrc,dimensions:[img.naturalWidth,img.naturalHeight],rect:r.toJSON(),visible:true});
 document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));check(viewer.getAttribute('aria-hidden')==='true','Escape failed');check(document.activeElement===link,'Focus not returned');
}
const link=document.querySelector('.fig a.zoom'),href=link.href;
link.href='assets/missing-regression-image.webp';link.click();
await new Promise(r=>setTimeout(r,400));
check(document.querySelector('.viewer-hint').textContent.includes('Не удалось загрузить'),'Missing failure state');
check(document.querySelector('.viewer-hint a').href===link.href,'Missing original fallback');
document.querySelector('.viewer-close').click();link.href=href;
result.failedImageFallback=true;result.status='PASS';
await fetch('/__result',{method:'POST',body:JSON.stringify(result)});console.log('PASS',JSON.stringify(result));
})().catch(error=>{console.error(error);fetch('/__result',{method:'POST',body:JSON.stringify({width:innerWidth,status:'FAIL',error:String(error)})})});
