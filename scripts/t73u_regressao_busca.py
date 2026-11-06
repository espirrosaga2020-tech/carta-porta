#!/usr/bin/env python3
"""Verify the T73 search is additive; baseline rooms and entry immutable."""
from pathlib import Path
import json,subprocess,re
R=Path(__file__).resolve().parents[1];BASE='7bc8a5b10e80efcc45574e4e8ef084e49aa0f81b'
line='<p id="busca-t73u"><a href="suprema2-busca.html">Busca local nas 125 páginas</a> · <a href="suprema2-indice-palavras.txt">Índice de palavras para IAs (sem JavaScript)</a></p>'
files=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R,text=True).splitlines()
for name in files:
 old=subprocess.check_output(['git','show',BASE+':'+name],cwd=R)
 new=(R/name).read_bytes()
 if name=='suprema2-mapa.html':
  assert new.count(line.encode())==1
  new=new.replace(('\n'+line+'\n').encode(),b'',1)
 assert old==new,'Existing file modified: '+name
index=json.loads((R/'suprema2-busca-indice.json').read_text());pages=index['pages'];assert len(pages)==125
manifest=json.loads((R/'scripts/t71u_manifesto.json').read_text())
assert {p['url'].rsplit('/',1)[1] for p in pages}=={p['html'] for p in manifest['pages'].values()}
assert any('serrote' in p['text'].lower() for p in pages)
text=(R/'suprema2-indice-palavras.txt').read_text();assert 'serrote (' in text and 'Contexto:' in text
for file in re.findall(r'https://[^\s]+/(suprema2-indice-palavras-\d+\.txt)',text):assert (R/file).is_file()
html=(R/'suprema2-busca.html').read_text();assert 'textContent=' in html and 'innerHTML' not in html
assert 'SUPREMA2-BUSCA-T73U' in html and (R/'suprema2-busca.txt').exists()
print('PASS: 125 pages indexed; serrote found; existing baseline byte-identical except one map link line.')
