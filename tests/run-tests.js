// Runs the test page in a headless browser and prints the results.
// Usage (from the repo root): node tests/run-tests.js
// Serves site/ (index.html, icons, manifest) and tests/tests.html side by side on a local port, so nothing touches the live site.
const http=require('http'),fs=require('fs'),path=require('path');const {chromium}=require('playwright');
const root=path.join(__dirname,'..'),files={'/index.html':'site/index.html','/tests.html':'tests/tests.html'};
const types={'.html':'text/html; charset=utf-8','.png':'image/png','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,r)=>{const u=q.url.split('?')[0];let f=files[u];if(!f&&/^\/[\w.-]+$/.test(u)&&fs.existsSync(path.join(root,'site',u)))f='site'+u;if(!f){r.writeHead(404);return r.end()}r.writeHead(200,{'Content-Type':types[path.extname(f)]||'application/octet-stream'});fs.createReadStream(path.join(root,f)).pipe(r)});
// Runs every check twice: once in light mode and once in dark mode (phones in dark mode see different colors).
srv.listen(0,async()=>{const url='http://localhost:'+srv.address().port+'/tests.html';const b=await chromium.launch();let fails=0;
 for(const cs of ['light','dark']){const pg=await b.newPage({timezoneId:'America/Chicago',colorScheme:cs});
 await pg.goto(url);await pg.waitForFunction(()=>window.__result,null,{timeout:60000});const r=await pg.evaluate(()=>window.__result);
 console.log('\n== '+cs+' mode ==');
 r.suites.forEach(s=>{const bad=s.t.filter(t=>!t.ok);if(bad.length||cs=='light')console.log((bad.length?'FAIL ':'ok   ')+s.n+' ('+(s.t.length-bad.length)+'/'+s.t.length+')');bad.forEach(t=>console.log('     x '+t.n+(t.d?' : '+t.d:'')))});
 console.log(cs+' mode: '+r.passed+' passed, '+r.failed+' failed');fails+=r.failed;await pg.close()}
 console.log('\n'+(fails?fails+' failed':'0 failed'));await b.close();srv.close();process.exit(fails?1:0)});
