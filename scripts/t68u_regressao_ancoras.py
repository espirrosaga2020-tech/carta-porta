#!/usr/bin/env python3
"""P4 regression: anchors resolve, expected files exist, classic byte-identical; T71 rooms and cross-file anchors."""
from __future__ import annotations
import re, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [
    'oi.html','chave.txt','tudo.html','tudo-resumo.html',
    'tudo-suprema2.html','tudo-suprema2-resumo.html','chave-suprema2.txt',
    'index.html','llms.txt','para-ias.html',
    'suprema2-entrada.html','suprema2-entrada.txt','carta.json',
]
PRE = subprocess.check_output(['git','rev-parse','HEAD~0'], cwd=ROOT, text=True).strip()
# Prefer explicit pre-change if on branch with commits; caller may pass PRE_SHA
import os
PRE = os.environ.get('PRE_SHA', 'bd295e0')

def ids_and_hrefs(html: str):
    ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', html))
    hrefs = re.findall(r'href=["\']#([^"\']+)["\']', html)
    return ids, hrefs

def check_html(path: Path):
    data = path.read_text(encoding='utf-8', errors='replace')
    ids, hrefs = ids_and_hrefs(data)
    missing = sorted({h for h in hrefs if h not in ids})
    return missing, len(ids), len(hrefs)

ok = True
print('=== expected files ===')
for f in EXPECTED:
    p = ROOT / f
    exists = p.exists() and p.stat().st_size > 0
    print(f'  {"OK" if exists else "MISSING"} {f} size={p.stat().st_size if p.exists() else 0}')
    ok &= exists

print('=== anchors in HTML ===')
for f in ROOT.glob('*.html'):
    missing, nids, nh = check_html(f)
    if f.name == 'tudo-resumo.html' and 'pg-mapa' in missing:
        print(f'  NOTE {f.name}: inherited missing #pg-mapa (classic left untouched by design)')
        missing = [m for m in missing if m != 'pg-mapa']
    status = 'OK' if not missing else 'FAIL'
    if missing:
        ok = False
    print(f'  {status} {f.name} ids={nids} hrefs={nh} missing={missing}')

print('=== classic strict SHA-256 vs', PRE, '===')
import hashlib, json
CLASSIC = ['tudo.html','chave.txt','tudo-resumo.html','oi.html','para-ias.html','carta.json']
for name in CLASSIC:
    old = subprocess.check_output(['git','show',f'{PRE}:{name}'],cwd=ROOT)
    new = (ROOT/name).read_bytes()
    same = old == new
    ok &= same
    print('  ' + ('OK' if same else 'FAIL'), name, hashlib.sha256(new).hexdigest(), 'byte-identical' if same else 'CHANGED')

# Entry phrase present
ent = (ROOT / 'suprema2-entrada.html').read_text(encoding='utf-8')
if 'ENTRADA-SUPREMA2-PROVA-T68U-20261105' not in ent:
    print('FAIL entry missing test phrase')
    ok = False
else:
    print('OK entry test phrase present')

# Suprema2 footers
for f, name in [('tudo-suprema2.html','tudo-suprema2.html'), ('tudo-suprema2-resumo.html','tudo-suprema2-resumo.html')]:
    t = (ROOT / f).read_text(encoding='utf-8', errors='replace')
    if f'CARTA, {name}' not in t:
        print(f'FAIL footer identity {f}')
        ok = False
    else:
        print(f'OK footer {f}')

# T71 regression: generated navigation, text fallback and bounded payloads.
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag=='a' and 'href' in a: self.links.append(a['href'])

def parse_file(path):
    parser=Parser(); parser.feed(path.read_text()); return parser

manifest=json.loads((ROOT/'scripts/t71u_manifesto.json').read_text())
assert manifest['drive_items']==140 and manifest['harvest_refs']==42 and manifest['nexus_children']==30
parsed={}
print('=== T71 rooms, TXT twins, cross-file routes ===')
for stem,meta in manifest['pages'].items():
    for ext in ['html','txt']:
        path=ROOT/(stem+'.'+ext)
        valid=path.exists() and 0 < path.stat().st_size < 150000 and meta['prova'] in path.read_text()
        if not valid: print('FAIL payload/prova',path.name)
        ok &= valid
    parser=parse_file(ROOT/(stem+'.html')); parsed[stem+'.html']=parser
    if len(parser.ids)!=len(set(parser.ids)):
        print('FAIL duplicate IDs',stem); ok=False
    for route in ['suprema2-mapa.html','suprema2-entrada.html']:
        if route not in parser.links: print('FAIL backlink',stem,route);ok=False
    if 'Fontes' not in (ROOT/(stem+'.html')).read_text(): print('FAIL fontes',stem);ok=False
for filename,parser in list(parsed.items()):
    for href in parser.links:
        url=urlsplit(href)
        if url.scheme or url.netloc:continue
        target=ROOT/(unquote(url.path) or filename)
        if not target.exists(): print('FAIL local route',filename,href);ok=False;continue
        if url.fragment and target.suffix=='.html':
            if target.name not in parsed: parsed[target.name]=parse_file(target)
            if unquote(url.fragment) not in parsed[target.name].ids:
                print('FAIL cross-file anchor',filename,href);ok=False
for f in ['suprema2-entrada.html','tudo-suprema2-resumo.html','chave-suprema2.txt','index.html','llms.txt']:
    if 'suprema2-mapa.html' not in (ROOT/f).read_text():print('FAIL hub discovery',f);ok=False
if (ROOT/'suprema2-entrada.html').stat().st_size >= 15000:print('FAIL entry too big');ok=False
inventory=json.loads((ROOT/'scripts/t71u_fontes.json').read_text())
drive=(ROOT/'suprema2-drive.html').read_text()
for item in inventory['inventory']:
    if item['id'] not in drive:print('FAIL missing Drive id',item['id']);ok=False
for key in ['indice','aditivos']:
    for record in inventory[key]['registros']:
        if 'registro-'+record['id'] not in (ROOT/'suprema2-enciclopedia.html').read_text(): print('FAIL registry record',record['id']);ok=False
for n in range(1,13):
    if f'q3-c{n:02}' not in (ROOT/'suprema2-jornada.html').read_text():print('FAIL question',n);ok=False
print('T71 page pairs',len(manifest['pages']),'public readings',manifest['public_readings'])

print('RESULT', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
