const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('/Users/zslepova/IvanOS/.worktrees/statya-konspekt/claude-ai/konspekt-rechi-v-chatgpt/index.html','utf8');
const match=html.match(/document\.querySelectorAll\("\[data-copy-target\]"\)[\s\S]+?(?=<\/script>)/);assert.ok(match);
const prompts=Array.from(html.matchAll(/<pre id="(prompt-[1-5])"><code>([\s\S]*?)<\/code><\/pre>/g));assert.equal(prompts.length,5);
const decode=s=>s.replaceAll('&gt;','>').replaceAll('&lt;','<').replaceAll('&amp;','&').replaceAll('&quot;','"').replaceAll('&#x27;',"'");
async function run(fallback){
let written=[],timers=[];
const elements=Object.fromEntries(prompts.map(([_,id,s])=>[id,{textContent:decode(s)}]));
const buttons=prompts.map(([_,id])=>({dataset:{copyTarget:id},textContent:'Скопировать',classList:{add(){},remove(){}},addEventListener(e,fn){this.click=fn;}}));
let current='';
const document={querySelectorAll:()=>buttons,getElementById:id=>elements[id],createElement:()=>({setAttribute(){},style:{},select(){current=this.value;},remove(){}}),body:{appendChild(){}},execCommand:()=>{written.push(current);return true;}};
vm.runInNewContext(match[0],{document,navigator:fallback?{}:{clipboard:{writeText:s=>{written.push(s);return Promise.resolve();}}},clearTimeout(){},setTimeout(fn,ms){assert.equal(ms,1800);timers.push(fn);return timers.length;}});
for(const b of buttons){b.click();await new Promise(r=>setImmediate(r));assert.equal(b.textContent,'✓ Скопировано');b.click();await new Promise(r=>setImmediate(r));assert.equal(b.textContent,'✓ Скопировано');}
assert.equal(written.length,10);for(let i=0;i<5;i++)assert.equal(written[2*i],elements['prompt-'+(i+1)].textContent);
for(const fn of timers)fn();for(const b of buttons)assert.equal(b.textContent,'Скопировать');
console.log((fallback?'FALLBACK':'CLIPBOARD')+'_OK: пять запросов целиком, повторный клик, подтверждение, 1800 мс');
}
(async()=>{await run(false);await run(true);})().catch(e=>{console.error(e);process.exitCode=1;});
