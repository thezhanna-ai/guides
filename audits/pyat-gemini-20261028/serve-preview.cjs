const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const site=require(root+'/scripts/preview_article.cjs').serveSite(root);
http.createServer((req,res)=>{
 if(req.url==='/__gemini.js'){res.setHeader('Content-Type','text/javascript');return res.end(fs.readFileSync(__dirname+'/browser-checks.js'))}
 if(req.url==='/__gemini-result'&&req.method==='POST'){let body='';req.on('data',b=>body+=b);req.on('end',()=>{let d=JSON.parse(body);if(![390,1440].includes(d.width)){res.writeHead(400);return res.end('Invalid viewport')}fs.writeFileSync(__dirname+'/chrome-'+d.width+'.json',JSON.stringify(d,null,2));res.end('saved')});return}
 site.emit('request',req,res);
}).listen(8770,'127.0.0.1',()=>console.log('Gemini preview :8770'));
