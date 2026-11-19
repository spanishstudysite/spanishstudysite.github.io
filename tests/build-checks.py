# Embeds tests.html into index.html as a private, passcode-protected "Site checks" page (open the site with #checks).
# Run from the repo root after any change to tests/tests.html or site/index.html:  python3 tests/build-checks.py
import json,re,hashlib
SALT="studyhub-checks"
HASH="ecd9968a9cfb36596c784839728ef17db58b94d54bf5fda19503c41c232fc931"
t=open('tests/tests.html',encoding='utf-8').read()
src=json.dumps(t,ensure_ascii=False).replace('</','<\\/')
block=('<!--CHECKS--><script>(function(){var SRC='+src+',SALT="'+SALT+'",H="'+HASH+'";\n'
'function sha(s){return crypto.subtle.digest("SHA-256",new TextEncoder().encode(s)).then(function(b){return Array.prototype.map.call(new Uint8Array(b),function(x){return("0"+x.toString(16)).slice(-2)}).join("")})}\n'
'function box(h){var o=document.getElementById("chk");if(!o){o=document.createElement("div");o.id="chk";o.style.cssText="position:fixed;inset:0;z-index:200;background:var(--bg,#f7f7fb);display:flex;flex-direction:column";document.body.appendChild(o)}o.innerHTML=h;return o}\n'
'function close(){var o=document.getElementById("chk");if(o)o.remove();if(location.hash=="#checks")history.replaceState(null,"",location.pathname+location.search);if(window.SH_pendReload){window.SH_pendReload=0;location.reload()}}\n'
'function run(){var o=box(\'<div style="display:flex;justify-content:flex-end;padding:8px 12px"><button class="chip" id="chkx">Close</button></div><iframe id="chkf" style="flex:1;border:0;width:100%"></iframe>\');document.getElementById("chkx").onclick=close;document.getElementById("chkf").srcdoc=SRC}\n'
'function ask(){try{if(sessionStorage.getItem("chkok")===H){run();return}}catch(e){}box(\'<div style="margin:auto;max-width:340px;width:100%;padding:16px"><div class="card"><h3 style="margin:0 0 4px">Site checks</h3><p class="sub" style="margin:0 0 12px">Private page. Enter the checks passcode.</p><input type="password" id="chkp" autocomplete="off" placeholder="Passcode" style="margin-bottom:8px"><p id="chke" class="sub" style="color:#c0392b;margin:0 0 8px" hidden>That passcode isn\\\'t right.</p><button class="go" id="chkg">Open</button><button class="chip" id="chkc" style="margin-top:8px">Cancel</button></div></div>\');\n'
'var p=document.getElementById("chkp");p.focus();document.getElementById("chkc").onclick=close;var go=function(){sha(SALT+":"+p.value.trim().toLowerCase()).then(function(h){if(h===H){try{sessionStorage.setItem("chkok",H)}catch(e){}run()}else{document.getElementById("chke").hidden=false;p.value=""}})};document.getElementById("chkg").onclick=go;p.onkeydown=function(e){if(e.key=="Enter")go()}}\n'
'function chk(){if(location.hash=="#checks")ask()}window.addEventListener("hashchange",chk);if(document.readyState=="loading")document.addEventListener("DOMContentLoaded",chk);else chk()})();</script><!--/CHECKS-->')
s=open('site/index.html',encoding='utf-8').read()
s=re.sub(r'<!--CHECKS-->.*?<!--/CHECKS-->\n?','',s,flags=re.S)
s=s.replace('</body></html>',block+'\n</body></html>')
open('site/index.html','w',encoding='utf-8').write(s)
print("embedded",len(t),"bytes of tests")
