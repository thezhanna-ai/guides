const http=require('node:http'),fs=require('node:fs');
const root=require('node:path').resolve(__dirname,'../..');
const out=__dirname;
const site=require(root+'/scripts/preview_article.cjs').serveSite(root);
http.createServer((req,res)=>{
 if(req.url==='/__checks.js'||req.url==='/__before.json'){res.setHeader('Content-Type',req.url.endsWith('.js')?'text/javascript':'application/json');return res.end(fs.readFileSync(out+(req.url.endsWith('.js')?'/browser-checks.js':'/prompts-before.json')))}
 if(req.url==='/__result'&&req.method==='POST'){let body='';req.on('data',b=>body+=b);req.on('end',()=>{let data=JSON.parse(body);if(![390,1440].includes(data.width)){res.writeHead(400);return res.end('Unexpected viewport')}fs.writeFileSync(out+'/chrome-'+data.width+'.json',JSON.stringify(data,null,2));res.end('saved')});return}
 site.emit('request',req,res);
}).listen(8770,'127.0.0.1',()=>console.log('Evidence preview :8770'));
