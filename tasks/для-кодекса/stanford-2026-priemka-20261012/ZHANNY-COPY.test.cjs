const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const data=JSON.parse(fs.readFileSync(__dirname+'/ZHANNY-COPY-INPUT.json','utf8'));
function harness(mode){
 let handler,copied,field;
 const button={dataset:{copyTarget:'pamyatka-text'},textContent:'Скопировать',classList:{add(){},remove(){}},addEventListener(name,fn){assert.equal(name,'click');handler=fn;}};
 const document={querySelectorAll(selector){assert.equal(selector,'[data-copy-target]');return [button];},getElementById(id){assert.equal(id,'pamyatka-text');return {textContent:data.textContent};},createElement(tag){assert.equal(tag,'textarea');field={style:{},setAttribute(){},select(){},remove(){}};return field;},body:{appendChild(){}},execCommand(command){assert.equal(command,'copy');copied=field.value;return true;}};
 const navigator=mode==='fallback'?{}:{clipboard:{writeText(text){if(mode==='rejected')return Promise.reject(new Error('clipboard unavailable'));copied=text;return Promise.resolve();}}};
 vm.runInNewContext(data.script,{document,navigator,setTimeout(){return 1;},clearTimeout(){}});
 return {async click(){handler();await new Promise(resolve=>setImmediate(resolve));return {copied,button};}};
}
for(const mode of ['clipboard','fallback','rejected'])test('Памятка копируется с адресом: '+mode,async()=>{
 const {copied,button}=await harness(mode).click();
 assert.equal(copied,data.textContent);
 assert.ok(copied.includes('Оригинал лекции: '+data.url));
 assert.ok(copied.includes('Как применить в ChatGPT или Claude:'));
 assert.equal(copied.split(data.url).length-1,1);
 assert.ok(!copied.includes('<a'));
 assert.equal(button.textContent,'✓ Скопировано');
});
