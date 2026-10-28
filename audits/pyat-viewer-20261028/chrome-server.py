from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import json,os
ROOT=Path('/Users/zslepova/IvanOS/projects/statya-pyat-neyrosetey')
os.chdir(ROOT)
class H(SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path=='/__viewer-check':
   data=Path(__file__).with_name('chrome-check.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(data)
  else: super().do_GET()
 def do_POST(self):
  if self.path!='/__viewer-results':self.send_error(404);return
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  (ROOT/'audits/pyat-viewer-20261028/chromium-results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
  self.send_response(200);self.end_headers();self.wfile.write(b'OK')
ThreadingHTTPServer(('127.0.0.1',8799),H).serve_forever()
